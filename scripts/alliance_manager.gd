extends Node
class_name AllianceManager

signal alliance_formed(faction: ServerNode.Owner)
signal alliance_broken(faction: ServerNode.Owner)
signal alliance_request_received(from_faction: ServerNode.Owner)

enum AllianceStatus { NEUTRAL, ALLIED, AT_WAR }

@export var network_manager: NetworkManager

# Alliance states
var player_enemy_status: AllianceStatus = AllianceStatus.AT_WAR  # Always at war
var player_ally_status: AllianceStatus = AllianceStatus.NEUTRAL  # Can become allied

# Alliance trust (affects AI behavior)
var ally_trust: float = 0.0  # -100 to 100
var pending_alliance_request: bool = false

func _ready() -> void:
	pass

func request_alliance() -> bool:
	if player_ally_status == AllianceStatus.ALLIED:
		return false  # Already allied
	
	if pending_alliance_request:
		return false  # Already pending
	
	# Check if ally faction has any servers
	if not network_manager:
		return false
	
	var ally_servers = network_manager.get_servers_by_owner(ServerNode.Owner.ALLY)
	if ally_servers.size() == 0:
		return false  # No ally faction exists
	
	pending_alliance_request = true
	
	# Simulate AI decision delay
	var timer = get_tree().create_timer(2.0)
	timer.timeout.connect(_on_alliance_decision)
	
	return true

func _on_alliance_decision() -> void:
	pending_alliance_request = false
	
	# AI decides based on trust and game state
	var accept_chance = 0.5 + (ally_trust / 200.0)  # 0% at -100 trust, 100% at +100
	
	# Also consider relative strength
	if network_manager:
		var counts = network_manager.count_servers_by_owner()
		var player_strength = counts[ServerNode.Owner.PLAYER]
		var enemy_strength = counts[ServerNode.Owner.ENEMY]
		
		# More likely to ally if enemy is stronger
		if enemy_strength > player_strength:
			accept_chance += 0.2
	
	if randf() < accept_chance:
		form_alliance()
	else:
		# Increase trust slightly for asking
		ally_trust = min(ally_trust + 10, 100)

func form_alliance() -> void:
	player_ally_status = AllianceStatus.ALLIED
	ally_trust = 50.0
	emit_signal("alliance_formed", ServerNode.Owner.ALLY)

func break_alliance() -> void:
	if player_ally_status == AllianceStatus.ALLIED:
		player_ally_status = AllianceStatus.NEUTRAL
		ally_trust = -50.0  # Breaking alliance hurts trust
		emit_signal("alliance_broken", ServerNode.Owner.ALLY)

func is_allied() -> bool:
	return player_ally_status == AllianceStatus.ALLIED

func get_ally_trust() -> float:
	return ally_trust

func modify_trust(amount: float) -> void:
	ally_trust = clamp(ally_trust + amount, -100, 100)

# Called when player helps ally (defending their servers)
func on_player_helped_ally() -> void:
	modify_trust(5.0)

# Called when ally helps player
func on_ally_helped_player() -> void:
	modify_trust(2.0)

# Check if a specific owner is friendly to player
func is_friendly_to_player(owner: ServerNode.Owner) -> bool:
	match owner:
		ServerNode.Owner.PLAYER:
			return true
		ServerNode.Owner.ALLY:
			return player_ally_status == AllianceStatus.ALLIED
		_:
			return false

func get_alliance_status_text() -> String:
	match player_ally_status:
		AllianceStatus.ALLIED:
			return "Allied"
		AllianceStatus.NEUTRAL:
			return "Neutral"
		AllianceStatus.AT_WAR:
			return "At War"
	return "Unknown"
