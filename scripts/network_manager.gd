extends Node2D
class_name NetworkManager

signal network_updated
signal server_clicked(server: ServerNode)

@export var server_scene: PackedScene
@export var connection_color_neutral: Color = Color(0.3, 0.6, 0.8, 0.5)
@export var connection_color_player: Color = Color(0.3, 1.0, 0.3, 0.7)
@export var connection_color_enemy: Color = Color(1.0, 0.3, 0.3, 0.7)
@export var connection_color_ally: Color = Color(0.3, 0.3, 1.0, 0.7)
@export var connection_width: float = 2.0

# Animation settings
@export var pulse_speed: float = 2.0
@export var data_packet_speed: float = 0.8
@export var packets_per_connection: int = 4
@export var packet_size: float = 5.0

var servers: Array[ServerNode] = []
var connections: Array[Dictionary] = []  # [{from: ServerNode, to: ServerNode}]

# Animation state
var animation_time: float = 0.0

const BACKEND_URL = "http://localhost:8000"
const API_HEALTH_ENDPOINT = BACKEND_URL + "/api/health"

func check_backend_health() -> bool:
	var http = HTTPClient.new()
	var error = http.connect_to_host(BACKEND_URL.split("://")[1].split(":")[0], 8000)
	if error != OK:
		return false
	return true


@onready var connections_container: Node2D = $ConnectionsContainer
@onready var servers_container: Node2D = $ServersContainer

func _ready() -> void:
	if not server_scene:
		server_scene = load("res://scenes/server_node.tscn")
	
	if check_backend_health():
		print("✅ Backend is reachable")
	else:
		print("❌ Backend connection failed")

func _process(delta: float) -> void:
	animation_time += delta
	queue_redraw()

func _draw() -> void:
	# Draw all connections with animations
	for conn in connections:
		var from_server: ServerNode = conn["from"]
		var to_server: ServerNode = conn["to"]
		
		if from_server and to_server:
			_draw_animated_connection(from_server, to_server)

func _draw_animated_connection(from_server: ServerNode, to_server: ServerNode) -> void:
	var from_pos: Vector2 = from_server.position
	var to_pos: Vector2 = to_server.position
	var from_color: Color = _get_owner_color(from_server.owner_type)
	var to_color: Color = _get_owner_color(to_server.owner_type)
	
	# Calculate pulse intensity
	var pulse: float = (sin(animation_time * pulse_speed) + 1.0) / 2.0
	var pulse_intensity: float = 0.3 + pulse * 0.4
	
	# Draw base glow line (wider, more transparent)
	var glow_color: Color = from_color.lerp(to_color, 0.5)
	glow_color.a = 0.15 + pulse * 0.1
	draw_line(from_pos, to_pos, glow_color, connection_width * 4, true)
	
	# Draw middle glow
	glow_color.a = 0.25 + pulse * 0.15
	draw_line(from_pos, to_pos, glow_color, connection_width * 2.5, true)
	
	# Draw main connection line with gradient effect
	_draw_gradient_line(from_pos, to_pos, from_color, to_color, connection_width, pulse_intensity)
	
	# Draw core bright line
	var core_color: Color = Color.WHITE
	core_color.a = 0.2 + pulse * 0.1
	draw_line(from_pos, to_pos, core_color, connection_width * 0.5, true)
	
	# Draw data packets flowing along the connection
	_draw_data_packets(from_pos, to_pos, from_color, to_color, from_server, to_server)

func _draw_gradient_line(from_pos: Vector2, to_pos: Vector2, from_color: Color, to_color: Color, width: float, intensity: float) -> void:
	# Draw line as segments with color interpolation
	var segments: int = 10
	var prev_pos: Vector2 = from_pos
	
	for i in range(1, segments + 1):
		var t: float = float(i) / segments
		var curr_pos: Vector2 = from_pos.lerp(to_pos, t)
		var segment_color: Color = from_color.lerp(to_color, t)
		segment_color.a *= intensity
		draw_line(prev_pos, curr_pos, segment_color, width, true)
		prev_pos = curr_pos

func _draw_data_packets(from_pos: Vector2, to_pos: Vector2, from_color: Color, to_color: Color, from_server: ServerNode, to_server: ServerNode) -> void:
	var distance: float = from_pos.distance_to(to_pos)
	var direction: Vector2 = (to_pos - from_pos).normalized()
	
	# Determine packet flow direction based on ownership
	var flow_forward: bool = true
	var flow_backward: bool = true
	var forward_speed: float = data_packet_speed
	var backward_speed: float = data_packet_speed
	
	# Same owner - bidirectional flow
	if from_server.owner_type == to_server.owner_type:
		flow_forward = true
		flow_backward = true
	# Different owners - show contested connection
	elif _are_enemies(from_server, to_server):
		flow_forward = true
		flow_backward = true
		forward_speed *= 1.5  # Faster for contested
		backward_speed *= 1.5
	else:
		# Mixed non-enemy - slower flow
		forward_speed *= 0.5
		backward_speed *= 0.5
	
	# Draw forward packets
	if flow_forward:
		for i in range(packets_per_connection):
			var offset: float = float(i) / packets_per_connection
			var t: float = fmod(animation_time * forward_speed + offset, 1.0)
			var packet_pos: Vector2 = from_pos.lerp(to_pos, t)
			var packet_color: Color = from_color.lerp(to_color, t)
			
			# Packet glow
			var glow_size: float = packet_size * 2.0
			var glow_color: Color = packet_color
			glow_color.a = 0.3
			draw_circle(packet_pos, glow_size, glow_color)
			
			# Packet core
			packet_color.a = 0.8
			draw_circle(packet_pos, packet_size, packet_color)
			
			# Bright center
			var bright_color: Color = Color.WHITE
			bright_color.a = 0.6
			draw_circle(packet_pos, packet_size * 0.4, bright_color)
	
	# Draw backward packets (offset timing)
	if flow_backward:
		for i in range(packets_per_connection):
			var offset: float = float(i) / packets_per_connection + 0.5
			var t: float = 1.0 - fmod(animation_time * backward_speed + offset, 1.0)
			var packet_pos: Vector2 = from_pos.lerp(to_pos, t)
			var packet_color: Color = to_color.lerp(from_color, 1.0 - t)
			
			# Packet glow
			var glow_size: float = packet_size * 1.5
			var glow_color: Color = packet_color
			glow_color.a = 0.25
			draw_circle(packet_pos, glow_size, glow_color)
			
			# Packet core (slightly smaller for backward)
			packet_color.a = 0.6
			draw_circle(packet_pos, packet_size * 0.8, packet_color)

func _get_owner_color(owner: ServerNode.Owner) -> Color:
	var cb = GameState and GameState.colorblind_mode
	match owner:
		ServerNode.Owner.PLAYER:
			return Color(0.2, 0.5, 1.0, 0.7) if cb else connection_color_player
		ServerNode.Owner.ENEMY:
			return Color(1.0, 0.5, 0.0, 0.7) if cb else connection_color_enemy
		ServerNode.Owner.ALLY:
			return Color(0.9, 0.8, 0.2, 0.7) if cb else connection_color_ally
		_:
			return connection_color_neutral

func _are_enemies(server1: ServerNode, server2: ServerNode) -> bool:
	return is_enemy_of(server1.owner_type, server2.owner_type)

func get_connection_color(from: ServerNode, to: ServerNode) -> Color:
	if from.owner_type == to.owner_type:
		return _get_owner_color(from.owner_type)
	return connection_color_neutral

func create_server(pos: Vector2, server_name: String, owner: ServerNode.Owner) -> ServerNode:
	var server: ServerNode = server_scene.instantiate() as ServerNode
	server.position = pos
	server.server_name = server_name
	server.owner_type = owner
	
	servers_container.add_child(server)
	servers.append(server)
	
	server.server_selected.connect(_on_server_selected)
	server.server_captured.connect(_on_server_captured)
	
	return server

func connect_servers(server1: ServerNode, server2: ServerNode) -> void:
	for conn in connections:
		if (conn["from"] == server1 and conn["to"] == server2) or \
		   (conn["from"] == server2 and conn["to"] == server1):
			return
	
	connections.append({"from": server1, "to": server2})
	server1.add_connection(server2)
	server2.add_connection(server1)

func get_servers_by_owner(owner: ServerNode.Owner) -> Array[ServerNode]:
	var result: Array[ServerNode] = []
	for server in servers:
		if server.owner_type == owner:
			result.append(server)
	return result

func get_adjacent_enemies(server: ServerNode) -> Array[ServerNode]:
	var enemies: Array[ServerNode] = []
	for connected in server.connected_servers:
		if is_enemy_of(server.owner_type, connected.owner_type):
			enemies.append(connected)
	return enemies

func get_adjacent_allies(server: ServerNode) -> Array[ServerNode]:
	var allies: Array[ServerNode] = []
	for connected in server.connected_servers:
		if is_ally_of(server.owner_type, connected.owner_type):
			allies.append(connected)
	return allies

func is_enemy_of(owner1: ServerNode.Owner, owner2: ServerNode.Owner) -> bool:
	match owner1:
		ServerNode.Owner.PLAYER, ServerNode.Owner.ALLY:
			return owner2 == ServerNode.Owner.ENEMY
		ServerNode.Owner.ENEMY:
			return owner2 == ServerNode.Owner.PLAYER or owner2 == ServerNode.Owner.ALLY
	return false

func is_ally_of(owner1: ServerNode.Owner, owner2: ServerNode.Owner) -> bool:
	if owner1 == owner2:
		return true
	if owner1 == ServerNode.Owner.PLAYER and owner2 == ServerNode.Owner.ALLY:
		return true
	if owner1 == ServerNode.Owner.ALLY and owner2 == ServerNode.Owner.PLAYER:
		return true
	return false

func count_servers_by_owner() -> Dictionary:
	var counts: Dictionary = {
		ServerNode.Owner.NEUTRAL: 0,
		ServerNode.Owner.PLAYER: 0,
		ServerNode.Owner.ENEMY: 0,
		ServerNode.Owner.ALLY: 0
	}
	
	for server in servers:
		counts[server.owner_type] += 1
	
	return counts

func _on_server_selected(server: ServerNode) -> void:
	emit_signal("server_clicked", server)

func _on_server_captured(server: ServerNode, _new_owner: int) -> void:
	emit_signal("network_updated")
