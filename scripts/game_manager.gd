extends Node2D
class_name GameManager

@export var win_threshold: float = 0.75  # 75% control to win
@export var map_center: Vector2 = Vector2(640, 360)
@export var map_radius: float = 300.0

@onready var network_manager: NetworkManager = $NetworkManager
@onready var combat_manager: CombatManager = $CombatManager
@onready var alliance_manager: AllianceManager = $AllianceManager
@onready var attack_effects: AttackEffectsManager = $AttackEffectsManager
@onready var game_ui: GameUI = $GameUI
@onready var background: Sprite2D = $Background
@onready var attack_lines: Node2D = $AttackLines
@onready var demo_manager: DemoManager = $DemoManager
@onready var notification_manager = $NotificationManager
@onready var hint_manager = $HintManager

var game_over: bool = false
var demo_mode: bool = false

# Match statistics
var stats = {
	"start_time": 0,
	"nodes_captured": 0,
	"nodes_lost": 0,
	"attacks_launched": 0,
	"alliances_formed": 0
}

func _ready() -> void:
	# Setup references
	combat_manager.network_manager = network_manager
	combat_manager.set_attack_effects(attack_effects)
	alliance_manager.network_manager = network_manager
	game_ui.network_manager = network_manager
	game_ui.combat_manager = combat_manager
	game_ui.alliance_manager = alliance_manager
	
	if hint_manager:
		hint_manager.setup(self, network_manager, combat_manager, game_ui)
		
	# Connect signals
	network_manager.server_clicked.connect(_on_server_clicked)
	combat_manager.server_captured.connect(_on_server_captured)
	combat_manager.attack_started.connect(_on_attack_started)
	alliance_manager.alliance_formed.connect(_on_alliance_formed)
	
	# Setup the map
	setup_network()
	
	# Setup minimap after network is created
	if game_ui.minimap:
		game_ui.minimap.set_network_manager(network_manager)
		
	# Start match timer
	stats["start_time"] = Time.get_ticks_msec()
	
	# Check if demo mode was requested
	if GameState and GameState.demo_mode:
		start_demo()
		GameState.demo_mode = false

func start_demo() -> void:
	demo_mode = true
	if demo_manager:
		demo_manager.network_manager = network_manager
		demo_manager.combat_manager = combat_manager
		demo_manager.alliance_manager = alliance_manager
		demo_manager.game_ui = game_ui
		demo_manager.demo_completed.connect(_on_demo_completed)
		demo_manager.start_demo()

func _on_demo_completed() -> void:
	demo_mode = false

func setup_network() -> void:
	# Procedural generation: Jittered Ring Topology
	var servers: Array[ServerNode] = []
	
	# Randomize parameters for replayability
	randomize()
	var inner_count = randi_range(5, 7)
	var outer_count = randi_range(11, 15)
	var inner_radius = randf_range(map_radius * 0.35, map_radius * 0.45)
	var outer_radius = randf_range(map_radius * 0.75, map_radius * 0.9)
	
	# Center hub (neutral)
	var hub_pos = map_center + Vector2(randf_range(-20, 20), randf_range(-20, 20))
	var hub = network_manager.create_server(hub_pos, "Central Hub", ServerNode.Owner.NEUTRAL)
	hub.max_firewall = 150.0
	hub.firewall_strength = 150.0
	hub.processing_power = 15.0
	servers.append(hub)
	
	# Inner ring
	var inner_positions = generate_ring_positions(hub_pos, inner_radius, inner_count, 25.0)
	var inner_servers: Array[ServerNode] = []
	
	# Determine faction starting indices in inner ring (evenly spaced)
	var player_idx = 0
	var enemy_idx = inner_count / 2
	var ally_idx = inner_count - 1
	
	for i in range(inner_count):
		var owner = ServerNode.Owner.NEUTRAL
		var name_prefix = "Node"
		
		if i == player_idx:
			owner = ServerNode.Owner.PLAYER
			name_prefix = "Alpha"
		elif i == enemy_idx:
			owner = ServerNode.Owner.ENEMY
			name_prefix = "Omega"
		elif i == ally_idx:
			owner = ServerNode.Owner.ALLY
			name_prefix = "Beta"
		
		var server = network_manager.create_server(inner_positions[i], "%s-%d" % [name_prefix, i], owner)
		inner_servers.append(server)
		servers.append(server)
		
		# Connect to hub
		network_manager.connect_servers(hub, server)
	
	# Connect inner ring adjacent nodes
	for i in range(inner_count):
		network_manager.connect_servers(inner_servers[i], inner_servers[(i + 1) % inner_count])
	
	# Outer ring
	var outer_positions = generate_ring_positions(hub_pos, outer_radius, outer_count, 35.0)
	var outer_servers: Array[ServerNode] = []
	
	# Find closest outer nodes to the faction inner nodes to assign them correctly
	var player_outer_idx = _get_closest_index(outer_positions, inner_positions[player_idx])
	var enemy_outer_idx = _get_closest_index(outer_positions, inner_positions[enemy_idx])
	var ally_outer_idx = _get_closest_index(outer_positions, inner_positions[ally_idx])
	
	for i in range(outer_count):
		var owner = ServerNode.Owner.NEUTRAL
		var name_prefix = "Relay"
		
		if i == player_outer_idx or i == (player_outer_idx + 1) % outer_count:
			owner = ServerNode.Owner.PLAYER
			name_prefix = "Alpha"
		elif i == enemy_outer_idx or i == (enemy_outer_idx + 1) % outer_count:
			owner = ServerNode.Owner.ENEMY
			name_prefix = "Omega"
		elif i == ally_outer_idx or i == (ally_outer_idx + 1) % outer_count:
			owner = ServerNode.Owner.ALLY
			name_prefix = "Beta"
		
		var server = network_manager.create_server(outer_positions[i], "%s-%d" % [name_prefix, i + inner_count], owner)
		server.max_firewall = randf_range(60.0, 100.0)
		server.firewall_strength = server.max_firewall
		server.processing_power = randf_range(6.0, 10.0)
		outer_servers.append(server)
		servers.append(server)
	
	# Connect outer nodes to nearest inner node
	for i in range(outer_count):
		var nearest_inner = inner_servers[0]
		var min_dist = outer_positions[i].distance_squared_to(inner_positions[0])
		
		for j in range(1, inner_count):
			var d = outer_positions[i].distance_squared_to(inner_positions[j])
			if d < min_dist:
				min_dist = d
				nearest_inner = inner_servers[j]
				
		network_manager.connect_servers(outer_servers[i], nearest_inner)
	
	# Connect outer ring adjacent nodes safely (skip if crossing hub)
	for i in range(outer_count):
		network_manager.connect_servers(outer_servers[i], outer_servers[(i + 1) % outer_count])
	
	# Add some random cross connections to make graph less predictable
	var extra_connections = randi_range(3, 6)
	for i in range(extra_connections):
		var s1 = outer_servers[randi() % outer_count]
		var s2 = outer_servers[randi() % outer_count]
		if s1 != s2 and not s1.is_connected_to(s2):
			# Only connect if they are relatively close, to avoid long ugly lines crossing the whole map
			if s1.position.distance_to(s2.position) < map_radius * 1.2:
				network_manager.connect_servers(s1, s2)

func _get_closest_index(positions: Array[Vector2], target: Vector2) -> int:
	var best_idx = 0
	var min_dist = positions[0].distance_squared_to(target)
	for i in range(1, positions.size()):
		var d = positions[i].distance_squared_to(target)
		if d < min_dist:
			min_dist = d
			best_idx = i
	return best_idx

func generate_ring_positions(center: Vector2, radius: float, count: int, max_jitter: float = 0.0) -> Array[Vector2]:
	var positions: Array[Vector2] = []
	for i in range(count):
		var angle = (2 * PI * i / count) - PI / 2  # Start from top
		var jitter_radius = radius + randf_range(-max_jitter, max_jitter)
		var jitter_angle = angle + randf_range(-max_jitter/radius, max_jitter/radius)
		var pos = center + Vector2(cos(jitter_angle), sin(jitter_angle)) * jitter_radius
		positions.append(pos)
	return positions

func _process(_delta: float) -> void:
	if game_over:
		return
	
	check_win_condition()
	queue_redraw()

func _draw() -> void:
	# Attack effects are now handled by AttackEffectsManager
	pass

func check_win_condition() -> void:
	var counts = network_manager.count_servers_by_owner()
	var total = network_manager.servers.size()
	
	if total == 0:
		return
	
	var player_control = float(counts[ServerNode.Owner.PLAYER]) / total
	var enemy_control = float(counts[ServerNode.Owner.ENEMY]) / total
	
	var time_played = (Time.get_ticks_msec() - stats["start_time"]) / 1000.0
	stats["time_played"] = time_played
	
	# Player wins
	if player_control >= win_threshold:
		game_over = true
		game_ui.show_game_over(true, stats)
		if Audio:
			Audio.play_victory()
	
	# Player loses
	elif counts[ServerNode.Owner.PLAYER] == 0:
		game_over = true
		game_ui.show_game_over(false, stats)
		if Audio:
			Audio.play_defeat()
	
	# Enemy wins (optional - could also just check player loss)
	elif enemy_control >= win_threshold:
		game_over = true
		game_ui.show_game_over(false, stats)
		if Audio:
			Audio.play_defeat()

func _on_server_clicked(server: ServerNode) -> void:
	var current_selection = game_ui.selected_server
	
	# Check for direct click-to-attack
	if current_selection and current_selection.owner_type == ServerNode.Owner.PLAYER:
		if server.owner_type == ServerNode.Owner.ENEMY and current_selection.is_connected_to(server):
			combat_manager.player_attack(current_selection, server)
			game_ui.hide_target_selection()
			
			# Add click feedback sound
			if Audio:
				Audio.play_ui_click()
			return
			
	game_ui.select_server(server)

func _on_server_captured(server: ServerNode, new_owner: int) -> void:
	# Play capture sound
	if Audio:
		var by_player = new_owner == ServerNode.Owner.PLAYER
		Audio.play_server_captured(by_player)
	
	# Send notification
	if notification_manager:
		if new_owner == ServerNode.Owner.PLAYER:
			stats["nodes_captured"] += 1
			notification_manager.notify_server_captured(server.server_name)
		else:
			if server.owner_type == ServerNode.Owner.PLAYER:
				stats["nodes_lost"] += 1
			notification_manager.notify_server_lost(server.server_name)

func _on_attack_started(attacker: ServerNode, target: ServerNode) -> void:
	if attacker.owner_type == ServerNode.Owner.PLAYER:
		stats["attacks_launched"] += 1
		
	# Notify when enemy attacks player nodes
	if notification_manager:
		if target.owner_type == ServerNode.Owner.PLAYER and attacker.owner_type == ServerNode.Owner.ENEMY:
			notification_manager.notify_under_attack(target.server_name)

func _on_alliance_formed(_faction: ServerNode.Owner) -> void:
	stats["alliances_formed"] += 1
	# Play alliance sound
	if Audio:
		Audio.play_alliance_formed()
	
	# Send notification
	if notification_manager:
		notification_manager.notify_alliance_formed()

