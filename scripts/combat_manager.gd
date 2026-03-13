extends Node
class_name CombatManager

signal attack_started(attacker: ServerNode, target: ServerNode)
signal attack_ended(attacker: ServerNode, target: ServerNode)
signal server_captured(server: ServerNode, new_owner: int)

@export var network_manager: NetworkManager
@export var attack_speed_multiplier: float = 1.0
@export var ai_decision_interval: float = 2.0  # How often AI makes decisions

# Reference to attack effects manager
var attack_effects: AttackEffectsManager

# Active attacks: {attacker: target}
var active_attacks: Dictionary = {}
var ai_attack_timer: float = 0.0

func _ready() -> void:
	pass

func _process(delta: float) -> void:
	# Process AI decisions
	ai_attack_timer += delta
	if ai_attack_timer >= ai_decision_interval:
		ai_attack_timer = 0.0
		process_ai_decisions()
	
	# Process active attacks
	process_attacks(delta)

func set_attack_effects(effects: AttackEffectsManager) -> void:
	attack_effects = effects

func process_ai_decisions() -> void:
	if not network_manager:
		return
	
	# Enemy AI decision making
	var enemy_servers = network_manager.get_servers_by_owner(ServerNode.Owner.ENEMY)
	for server in enemy_servers:
		if server not in active_attacks:
			var targets = network_manager.get_adjacent_enemies(server)
			if targets.size() > 0:
				# Pick weakest target
				var weakest = targets[0]
				for t in targets:
					if t.firewall_strength < weakest.firewall_strength:
						weakest = t
				start_attack(server, weakest)
	
	# Ally AI decision making (helps player)
	var ally_servers = network_manager.get_servers_by_owner(ServerNode.Owner.ALLY)
	for server in ally_servers:
		if server not in active_attacks:
			var targets = network_manager.get_adjacent_enemies(server)
			if targets.size() > 0:
				# Pick target being attacked by player if possible
				var target = targets[0]
				for t in targets:
					if t in active_attacks.values():
						target = t
						break
				start_attack(server, target)

func process_attacks(delta: float) -> void:
	var attacks_to_remove: Array = []
	
	for attacker in active_attacks:
		var target = active_attacks[attacker]
		
		# Check if attack is still valid
		if not is_instance_valid(attacker) or not is_instance_valid(target):
			attacks_to_remove.append(attacker)
			continue
		
		# Check if still connected
		if not attacker.is_connected_to(target):
			attacks_to_remove.append(attacker)
			continue
		
		# Check if still enemies
		if not network_manager.is_enemy_of(attacker.owner_type, target.owner_type):
			attacks_to_remove.append(attacker)
			continue
		
		# Apply damage
		var damage = attacker.get_attack_power() * attack_speed_multiplier * delta
		target.receive_attack(damage)
		
		# Check for capture
		if target.firewall_strength <= 0:
			capture_server(target, attacker.owner_type)
			attacks_to_remove.append(attacker)
	
	# Clean up finished attacks
	for attacker in attacks_to_remove:
		end_attack(attacker)

func start_attack(attacker: ServerNode, target: ServerNode) -> void:
	if attacker in active_attacks:
		return
	
	active_attacks[attacker] = target
	
	# Create visual projectile with particle effects
	if attack_effects:
		attack_effects.spawn_attack_projectile(attacker, target)
	
	# Play attack sound
	if Audio:
		Audio.play_attack_launch()
	
	emit_signal("attack_started", attacker, target)

func end_attack(attacker: ServerNode) -> void:
	if attacker in active_attacks:
		var target = active_attacks[attacker]
		# Stop projectile effects
		if attack_effects:
			attack_effects.stop_projectile(attacker, target)
		active_attacks.erase(attacker)
		emit_signal("attack_ended", attacker, target)

func player_attack(attacker: ServerNode, target: ServerNode) -> bool:
	# Validate attack
	if attacker.owner_type != ServerNode.Owner.PLAYER:
		return false
	
	if not attacker.is_connected_to(target):
		return false
	
	if not network_manager.is_enemy_of(attacker.owner_type, target.owner_type):
		return false
	
	start_attack(attacker, target)
	return true

func player_cancel_attack(attacker: ServerNode) -> void:
	if attacker in active_attacks and attacker.owner_type == ServerNode.Owner.PLAYER:
		end_attack(attacker)

func capture_server(server: ServerNode, new_owner: ServerNode.Owner) -> void:
	# When player or ally captures, it becomes player's
	# When enemy captures, it becomes enemy's
	var final_owner = new_owner
	if new_owner == ServerNode.Owner.ALLY:
		final_owner = ServerNode.Owner.PLAYER  # Allies capture for player
	
	# Spawn capture effect
	if attack_effects:
		attack_effects.spawn_capture_effect(server.position, final_owner)
	
	server.capture(final_owner)
	emit_signal("server_captured", server, final_owner)

func get_attack_target(attacker: ServerNode) -> ServerNode:
	if attacker in active_attacks:
		return active_attacks[attacker]
	return null

func is_server_attacking(server: ServerNode) -> bool:
	return server in active_attacks

func is_server_under_attack(server: ServerNode) -> bool:
	return server in active_attacks.values()
