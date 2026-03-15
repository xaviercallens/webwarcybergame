import asyncio
from datetime import datetime
from sqlmodel import Session, select
from backend.database import get_engine
from backend.models import Epoch, EpochPhase, Node, Faction, EpochAction, ActionType, Player

def process_transition_phase(session: Session, epoch: Epoch):
    print(f"[ENGINE] Processing Transition for Epoch {epoch.number}...")
    actions = session.exec(select(EpochAction).where(EpochAction.epoch_id == epoch.id)).all()
    
    node_actions = {}
    for action in actions:
        if action.target_node_id not in node_actions:
            node_actions[action.target_node_id] = []
        node_actions[action.target_node_id].append(action)

    # 1. Resolve combat interactions
    for node_id, node_acts in node_actions.items():
        node = session.get(Node, node_id)
        if not node: continue
        
        attackers = {}
        defenders = 0
        
        for act in node_acts:
            player = session.get(Player, act.player_id)
            if not player or not player.faction_id:
                continue
                
            if act.action_type == ActionType.BREACH:
                if player.faction_id not in attackers:
                    attackers[player.faction_id] = 0
                attackers[player.faction_id] += act.cu_committed
            elif act.action_type == ActionType.DEFEND:
                if player.faction_id == node.faction_id:
                    defenders += act.cu_committed
        
        total_defense = node.defense_level + defenders
        if attackers:
            strongest_attacker_faction = max(attackers, key=attackers.get)
            max_attack_cu = attackers[strongest_attacker_faction]
            
            # Simple threshold: If attack > defense, capture it
            if max_attack_cu > total_defense:
                print(f"[ENGINE] Node {node.name} captured by Faction {strongest_attacker_faction}!")
                node.faction_id = strongest_attacker_faction
                # Defense takes a hit upon capture
                node.defense_level = max(50, node.defense_level - int(max_attack_cu * 0.1))
                session.add(node)
                
    # 2. Update economy (Compute Units) and global influence
    factions = session.exec(select(Faction)).all()
    total_nodes = session.exec(select(Node)).all()
    total_count = len(total_nodes)
    
    for faction in factions:
        owned_nodes = [n for n in total_nodes if n.faction_id == faction.id]
        income = sum(n.compute_output for n in owned_nodes)
        
        faction.compute_reserves += income
        faction.global_influence_pct = (len(owned_nodes) / max(1, total_count)) * 100.0
        session.add(faction)

async def epoch_loop():
    engine = get_engine()
    print("[ENGINE] Epoch loop started.")
    
    while True:
        try:
            with Session(engine) as session:
                # Get current active epoch
                current = session.exec(select(Epoch).where(Epoch.ended_at == None).order_by(Epoch.id.desc())).first()
                if not current:
                    current = Epoch(number=1, phase=EpochPhase.PLANNING)
                    session.add(current)
                    session.commit()
                    session.refresh(current)

                now = datetime.utcnow()
                time_elapsed = (now - current.started_at).total_seconds()
                
                # Time slices
                # PLANNING: 0 - 600s (10 min)
                # SIM: 600 - 840s (4 min)
                # TRANSITION: 840 - 900s (1 min)

                # DEBUG: Fast forward timescales for local dev if needed. Let's use 1 min total loop for dev:
                # PLANNING: 0 - 45s
                # SIM: 45 - 55s
                # TRANSITION: 55 - 60s
                DEV_MODE = True
                
                if DEV_MODE:
                    t_sim = 45
                    t_trans = 55
                    t_end = 60
                else:
                    t_sim = 600
                    t_trans = 840
                    t_end = 900

                if time_elapsed >= t_end:
                    if current.phase != EpochPhase.TRANSITION:
                        process_transition_phase(session, current)
                    
                    current.ended_at = now
                    session.add(current)
                    
                    new_epoch = Epoch(number=current.number + 1, phase=EpochPhase.PLANNING)
                    session.add(new_epoch)
                    session.commit()
                    print(f"[ENGINE] Epoch {new_epoch.number} started. Phase: PLANNING")

                elif time_elapsed >= t_trans:
                    if current.phase != EpochPhase.TRANSITION:
                        current.phase = EpochPhase.TRANSITION
                        print(f"[ENGINE] Epoch {current.number} entering TRANSITION.")
                        process_transition_phase(session, current)
                        session.add(current)
                        session.commit()
                
                elif time_elapsed >= t_sim:
                    if current.phase == EpochPhase.PLANNING:
                        current.phase = EpochPhase.SIM
                        print(f"[ENGINE] Epoch {current.number} entering SIMULATION.")
                        session.add(current)
                        session.commit()
                        
        except Exception as e:
            print(f"[ENGINE ERROR] {e}")
            
        await asyncio.sleep(5)
