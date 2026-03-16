import asyncio
import os
from datetime import datetime
from sqlmodel import Session, select
from backend.database import get_engine
from backend.models import Epoch, EpochPhase, Node, Faction, EpochAction, ActionType, Player, Accord, NewsItem, Notification, NotificationType
from backend.websocket import manager

def inject_sentinel_actions(session: Session, epoch_id: int):
    print(f"[ENGINE] Injecting Sentinel autonomous actions for Epoch {epoch_id}...")
    from backend.models import Sentinel, SentinelPolicy, SentinelStatus, SentinelLog, Faction, Player, Node, EpochAction, ActionType
    import random
    
    sentinels = session.exec(select(Sentinel).where(Sentinel.status == SentinelStatus.DEPLOYED)).all()
    all_nodes = session.exec(select(Node)).all()
    if not all_nodes: return
    
    for s in sentinels:
        player = session.get(Player, s.player_id)
        if not player or not player.faction_id:
            continue
            
        faction = session.get(Faction, player.faction_id)
        if not faction or faction.compute_reserves < 50:
            log = SentinelLog(sentinel_id=s.id, epoch_id=epoch_id, description="Skipped action due to low Faction CU reserves (<50).")
            session.add(log)
            continue
            
        policy = session.exec(select(SentinelPolicy).where(SentinelPolicy.sentinel_id == s.id)).first()
        if not policy: continue
        
        action_type = ActionType.BREACH if random.random() < policy.aggression_weight else ActionType.DEFEND
        
        target_node = None
        cu_spend = 50
        
        if action_type == ActionType.BREACH:
            enemy_nodes = [n for n in all_nodes if n.faction_id != player.faction_id]
            if enemy_nodes:
                if random.random() < policy.stealth_weight:
                    # Stealthy: sort by lowest defense
                    enemy_nodes.sort(key=lambda n: n.defense_level)
                    target_node = enemy_nodes[0]
                else:
                    target_node = random.choice(enemy_nodes)
            else:
                action_type = ActionType.DEFEND
                
        if action_type == ActionType.DEFEND:
            owned_nodes = [n for n in all_nodes if n.faction_id == player.faction_id]
            if owned_nodes:
                target_node = random.choice(owned_nodes)
                
        if target_node:
            faction.compute_reserves -= cu_spend
            session.add(faction)
            
            new_action = EpochAction(
                epoch_id=epoch_id,
                player_id=player.id,
                action_type=action_type,
                target_node_id=target_node.id,
                cu_committed=cu_spend
            )
            session.add(new_action)
            
            log_desc = f"Executed {action_type} on Node {target_node.name} for {cu_spend} CU."
            log = SentinelLog(sentinel_id=s.id, epoch_id=epoch_id, description=log_desc)
            session.add(log)
            
    session.commit()

# Create an async wrapper for the synchronous DB session logic,
# because DiplomacyService uses `async def` for Google GenAI calls.
async def process_transition_phase_async(session: Session, epoch: Epoch):
    print(f"[ENGINE] Processing Transition for Epoch {epoch.number}...")
    inject_sentinel_actions(session, epoch.id)
    actions = session.exec(select(EpochAction).where(EpochAction.epoch_id == epoch.id)).all()
    
    # Pre-fetch and parse active Accords for CNSA Buffs
    accords = session.exec(select(Accord).where(Accord.status == "ACTIVE")).all()
    mercenary_allies = set()
    sentinel_allies = set()
    cartel_allies = set()
    
    for a in accords:
        if a.faction_a_id == 6: mercenary_allies.add(a.faction_b_id)
        if a.faction_b_id == 6: mercenary_allies.add(a.faction_a_id)
        if a.faction_a_id == 7: sentinel_allies.add(a.faction_b_id)
        if a.faction_b_id == 7: sentinel_allies.add(a.faction_a_id)
        if a.faction_a_id == 8: cartel_allies.add(a.faction_b_id)
        if a.faction_b_id == 8: cartel_allies.add(a.faction_a_id)

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
                faction_id = player.faction_id
                cu = act.cu_committed
                
                # CNSA Buffs & Debuffs
                if faction_id in mercenary_allies:
                    cu = int(cu * 1.2) # Skill-Booster Offense
                if node.faction_id in cartel_allies:
                    cu = int(cu * 0.8) # Chaos Operations Debuff on Attackers
                    
                if faction_id not in attackers:
                    attackers[faction_id] = 0
                attackers[faction_id] += cu
            elif act.action_type == ActionType.DEFEND:
                if player.faction_id == node.faction_id:
                    defenders += act.cu_committed
        
        # Sentinel Vanguard Hardening Protocols
        base_defense = node.defense_level
        if node.faction_id in sentinel_allies:
            base_defense = int(base_defense * 1.2)
            
        total_defense = base_defense + defenders
        if attackers:
            # Type safe max key extraction
            strongest_attacker_faction: int = 0
            max_attack_cu: int = 0
            for f_id, cu_val in attackers.items():
                if cu_val > max_attack_cu:
                    max_attack_cu = cu_val
                    strongest_attacker_faction = f_id
            
            # Simple threshold: If attack > defense, capture it
            if max_attack_cu > total_defense and strongest_attacker_faction != 0:
                print(f"[ENGINE] Node {node.name} captured by Faction {strongest_attacker_faction}!")
                
                # Notify original owner if player-controlled
                old_owner_id = node.faction_id
                old_players = session.exec(select(Player).where(Player.faction_id == old_owner_id)).all()
                for p in old_players:
                    notif = Notification(player_id=p.id, message=f"CRITICAL: Node {node.name} was captured by an enemy!", type=NotificationType.COMBAT)
                    session.add(notif)
                    # Use asyncio.create_task to fire and forget
                    asyncio.create_task(manager.send_personal_message({"type": "NOTIFICATION", "message": notif.message, "severity": "error"}, p.id))
                    
                node.faction_id = strongest_attacker_faction
                # Defense takes a hit upon capture
                node.defense_level = max(50, node.defense_level - int(max_attack_cu * 0.1))
                session.add(node)
                
                # Broadcast generic message
                asyncio.create_task(manager.broadcast({
                    "type": "NODE_CAPTURED",
                    "node_id": node.id,
                    "new_faction_id": strongest_attacker_faction,
                    "message": f"Node {node.name} has been captured by Faction {strongest_attacker_faction}"
                }))
                
    # 2. Update economy (Compute Units) and global influence
    factions = session.exec(select(Faction)).all()
    total_nodes = session.exec(select(Node)).all()
    total_count = len(total_nodes)
    
    for faction in factions:
        owned_nodes = [n for n in total_nodes if n.faction_id == faction.id]
        
        if faction.compute_reserves is None:
            faction.compute_reserves = 0
        faction.compute_reserves += sum(n.compute_output for n in owned_nodes if n.compute_output)
        
        faction.global_influence_pct = (len(owned_nodes) / max(1, total_count)) * 100.0
        session.add(faction)
        
    # 3. Process Accords (Treaties)
    events_log = []
    
    for a in accords:
        fa = session.get(Faction, a.faction_a_id)
        fb = session.get(Faction, a.faction_b_id)
        if not fa or not fb: continue
        
        # Check for violations (Did A attack B this epoch?)
        # Simple check: were there any BREACH actions by A on B's nodes?
        violation = False
        for node_id, node_acts in node_actions.items():
            node = session.get(Node, node_id)
            if not node: continue
            
            for act in node_acts:
                if act.action_type == ActionType.BREACH:
                    player = session.get(Player, act.player_id)
                    if not player: continue
                    # A attacked B
                    if player.faction_id == fa.id and node.faction_id == fb.id:
                        violation = True
                    # B attacked A
                    if player.faction_id == fb.id and node.faction_id == fa.id:
                        violation = True
                        
        if violation:
            a.status = "BROKEN"
            session.add(a)
            events_log.append(f"TREATY BROKEN: Hostilities erupted between {fa.name} and {fb.name}.")
            print(f"[ENGINE] Treaty {a.id} BROKEN due to hostilities.")
            
            # Notify affected players
            affected = session.exec(select(Player).where(Player.faction_id.in_([fa.id, fb.id]))).all()
            for p in affected:
                notif = Notification(player_id=p.id, message=f"ACCORD BROKEN: Hostilities detected with an allied faction.", type=NotificationType.DIPLOMACY)
                session.add(notif)
                asyncio.create_task(manager.send_personal_message({"type": "NOTIFICATION", "message": notif.message, "severity": "warning"}, p.id))
                
            asyncio.create_task(manager.broadcast({"type": "TREATY_BROKEN", "accord_id": a.id}))
        else:
            # Apply passive CU effects or fees
            if 6 in (fa.id, fb.id):
                # Mercenary fee
                client = fb if fa.id == 6 else fa
                fee = 100
                if client.compute_reserves >= fee:
                    client.compute_reserves -= fee
                    session.add(client)
                else:
                    a.status = "BROKEN"
                    session.add(a)
                    events_log.append(f"MERCENARY CONTRACT BROKEN: {client.name} failed to pay the Cyber Mercenaries.")
            elif a.type == "TRADE":
                # Both gain +50 CU
                fa.compute_reserves += 50
                fb.compute_reserves += 50
                session.add(fa)
                session.add(fb)
                print(f"[ENGINE] Trade Treaty {a.id} paid dividends to {fa.name} and {fb.name}.")

    session.commit()
    
    # 4. Generate AI News (Sprint 3)
    from backend.services.diplomacy import DiplomacyService
    diplomacy_svc = DiplomacyService(api_key=os.environ.get("GOOGLE_API_KEY"))
    
    prior_news = session.exec(select(NewsItem).order_by(NewsItem.created_at.desc())).first()
    prior_text = prior_news.content if prior_news else ""
    
    # Collect generic combat events for the prompt
    combat_summaries = []
    for node_id, node_acts in node_actions.items():
        node = session.get(Node, node_id)
        if node:
            combat_summaries.append(f"Activity at Node {node.name} (Owned by Faction {node.faction_id})")
            
    all_events = events_log + combat_summaries
    
    try:
        news_text = await diplomacy_svc.generate_epoch_news(all_events, prior_text)
        new_item = NewsItem(epoch_id=epoch.id, content=news_text)
        session.add(new_item)
        session.commit()
        print(f"[ENGINE] AI News Generated: {news_text[:50]}...")
    except Exception as e:
        print(f"[ENGINE] AI News Generation Failed: {e}")
        
    return True

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
                        await process_transition_phase_async(session, current)
                    
                    current.ended_at = now
                    session.add(current)
                    
                    new_epoch = Epoch(number=current.number + 1, phase=EpochPhase.PLANNING)
                    session.add(new_epoch)
                    session.commit()
                    print(f"[ENGINE] Epoch {new_epoch.number} started. Phase: PLANNING")
                    await manager.broadcast({"type": "EPOCH_PHASE_CHANGE", "epoch_number": new_epoch.number, "phase": "PLANNING"})

                elif time_elapsed >= t_trans:
                    if current.phase != EpochPhase.TRANSITION:
                        current.phase = EpochPhase.TRANSITION
                        print(f"[ENGINE] Epoch {current.number} entering TRANSITION.")
                        session.add(current)
                        session.commit()
                        await manager.broadcast({"type": "EPOCH_PHASE_CHANGE", "epoch_number": current.number, "phase": "TRANSITION"})
                        await process_transition_phase_async(session, current)
                
                elif time_elapsed >= t_sim:
                    if current.phase == EpochPhase.PLANNING:
                        current.phase = EpochPhase.SIM
                        print(f"[ENGINE] Epoch {current.number} entering SIMULATION.")
                        session.add(current)
                        session.commit()
                        await manager.broadcast({"type": "EPOCH_PHASE_CHANGE", "epoch_number": current.number, "phase": "SIM"})
                        
        except Exception as e:
            print(f"[ENGINE ERROR] {e}")
            
        await asyncio.sleep(5)
