extends Control
class_name Minimap

# Minimap settings
@export var minimap_size: Vector2 = Vector2(180, 180)
@export var padding: float = 10.0
@export var node_size: float = 6.0
@export var connection_width: float = 1.5
@export var selected_node_size: float = 10.0

# Colors
@export var background_color: Color = Color(0.02, 0.05, 0.1, 0.85)
@export var border_color: Color = Color(0, 0.8, 0.9, 0.7)
@export var player_color: Color = Color(0.3, 1.0, 0.5, 1.0)
@export var enemy_color: Color = Color(1.0, 0.3, 0.3, 1.0)
@export var ally_color: Color = Color(0.3, 0.5, 1.0, 1.0)
@export var neutral_color: Color = Color(0.5, 0.7, 0.8, 0.7)
@export var connection_color: Color = Color(0, 0.6, 0.7, 0.4)

# References
var network_manager: NetworkManager
var selected_server: ServerNode

# Calculated bounds
var map_bounds: Rect2 = Rect2()
var scale_factor: float = 1.0
var offset: Vector2 = Vector2.ZERO

# Animation
var pulse_time: float = 0.0

func _ready() -> void:
	custom_minimum_size = minimap_size

func _process(delta: float) -> void:
	pulse_time += delta
	queue_redraw()

func _draw() -> void:
	# Draw background
	var bg_rect = Rect2(Vector2.ZERO, minimap_size)
	draw_rect(bg_rect, background_color)
	
	# Draw border with glow effect
	_draw_cyber_border()
	
	# Draw header
	_draw_header()
	
	if not network_manager or network_manager.servers.size() == 0:
		return
	
	# Calculate bounds and scale
	_calculate_bounds()
	
	# Draw connections first (behind nodes)
	_draw_connections()
	
	# Draw servers
	_draw_servers()
	
	# Draw selected indicator
	if selected_server:
		_draw_selected_indicator()

func _draw_cyber_border() -> void:
	var rect = Rect2(Vector2.ZERO, minimap_size)
	
	# Outer glow
	var glow_color = border_color
	glow_color.a = 0.2
	draw_rect(Rect2(-2, -2, minimap_size.x + 4, minimap_size.y + 4), glow_color, false, 4.0)
	
	# Main border
	draw_rect(rect, border_color, false, 2.0)
	
	# Corner accents
	var corner_len: float = 12.0
	var accent_color = Color(0, 1.0, 1.0, 0.8)
	
	# Top-left
	draw_line(Vector2(0, 0), Vector2(corner_len, 0), accent_color, 2.0)
	draw_line(Vector2(0, 0), Vector2(0, corner_len), accent_color, 2.0)
	
	# Top-right
	draw_line(Vector2(minimap_size.x, 0), Vector2(minimap_size.x - corner_len, 0), accent_color, 2.0)
	draw_line(Vector2(minimap_size.x, 0), Vector2(minimap_size.x, corner_len), accent_color, 2.0)
	
	# Bottom-left
	draw_line(Vector2(0, minimap_size.y), Vector2(corner_len, minimap_size.y), accent_color, 2.0)
	draw_line(Vector2(0, minimap_size.y), Vector2(0, minimap_size.y - corner_len), accent_color, 2.0)
	
	# Bottom-right
	draw_line(Vector2(minimap_size.x, minimap_size.y), Vector2(minimap_size.x - corner_len, minimap_size.y), accent_color, 2.0)
	draw_line(Vector2(minimap_size.x, minimap_size.y), Vector2(minimap_size.x, minimap_size.y - corner_len), accent_color, 2.0)

func _draw_header() -> void:
	# Draw mini header bar
	var header_rect = Rect2(0, 0, minimap_size.x, 18)
	var header_color = Color(0, 0.3, 0.4, 0.5)
	draw_rect(header_rect, header_color)
	
	# Header text would require a font - skip for now, border shows it's the minimap
	# Draw separator line
	draw_line(Vector2(0, 18), Vector2(minimap_size.x, 18), border_color, 1.0)

func _calculate_bounds() -> void:
	if network_manager.servers.size() == 0:
		return
	
	# Find min/max positions
	var min_pos = network_manager.servers[0].position
	var max_pos = network_manager.servers[0].position
	
	for server in network_manager.servers:
		min_pos.x = min(min_pos.x, server.position.x)
		min_pos.y = min(min_pos.y, server.position.y)
		max_pos.x = max(max_pos.x, server.position.x)
		max_pos.y = max(max_pos.y, server.position.y)
	
	# Add padding
	min_pos -= Vector2(50, 50)
	max_pos += Vector2(50, 50)
	
	map_bounds = Rect2(min_pos, max_pos - min_pos)
	
	# Calculate scale to fit in minimap (accounting for header)
	var available_size = minimap_size - Vector2(padding * 2, padding * 2 + 18)
	var scale_x = available_size.x / map_bounds.size.x
	var scale_y = available_size.y / map_bounds.size.y
	scale_factor = min(scale_x, scale_y)
	
	# Calculate offset to center
	var scaled_size = map_bounds.size * scale_factor
	offset = (minimap_size - scaled_size) / 2
	offset.y += 9  # Account for header

func _world_to_minimap(world_pos: Vector2) -> Vector2:
	var relative_pos = world_pos - map_bounds.position
	return relative_pos * scale_factor + offset

func _draw_connections() -> void:
	for conn in network_manager.connections:
		var from_server: ServerNode = conn["from"]
		var to_server: ServerNode = conn["to"]
		
		if not is_instance_valid(from_server) or not is_instance_valid(to_server):
			continue
		
		var from_pos = _world_to_minimap(from_server.position)
		var to_pos = _world_to_minimap(to_server.position)
		
		# Determine connection color based on owners
		var line_color = connection_color
		if from_server.owner_type == to_server.owner_type:
			line_color = _get_owner_color(from_server.owner_type)
			line_color.a = 0.5
		
		draw_line(from_pos, to_pos, line_color, connection_width)

func _draw_servers() -> void:
	for server in network_manager.servers:
		var pos = _world_to_minimap(server.position)
		var color = _get_owner_color(server.owner_type)
		
		# Outer glow
		var glow_color = color
		glow_color.a = 0.3
		draw_circle(pos, node_size + 2, glow_color)
		
		# Main node
		draw_circle(pos, node_size, color)
		
		# Inner highlight
		var highlight_color = Color.WHITE
		highlight_color.a = 0.4
		draw_circle(pos, node_size * 0.4, highlight_color)
		
		# Draw attack indicator if under attack
		if server.is_under_attack:
			_draw_attack_indicator(pos)

func _draw_attack_indicator(pos: Vector2) -> void:
	var pulse = (sin(pulse_time * 8.0) + 1.0) / 2.0
	var ring_size = node_size + 4 + pulse * 3
	var ring_color = Color(1.0, 0.3, 0.1, 0.6 + pulse * 0.3)
	
	# Draw pulsing ring
	_draw_ring(pos, ring_size, 1.5, ring_color)

func _draw_ring(center: Vector2, radius: float, width: float, color: Color) -> void:
	var segments: int = 16
	var prev_point = center + Vector2(radius, 0)
	
	for i in range(1, segments + 1):
		var angle = (2.0 * PI * i) / segments
		var point = center + Vector2(cos(angle), sin(angle)) * radius
		draw_line(prev_point, point, color, width)
		prev_point = point

func _draw_selected_indicator() -> void:
	if not is_instance_valid(selected_server):
		return
	
	var pos = _world_to_minimap(selected_server.position)
	var pulse = (sin(pulse_time * 4.0) + 1.0) / 2.0
	
	# Pulsing selection ring
	var ring_size = selected_node_size + pulse * 4
	var ring_color = Color(1.0, 1.0, 0.3, 0.8)
	
	_draw_ring(pos, ring_size, 2.0, ring_color)
	
	# Inner selection ring
	_draw_ring(pos, selected_node_size - 2, 1.5, ring_color)

func _get_owner_color(owner: ServerNode.Owner) -> Color:
	match owner:
		ServerNode.Owner.PLAYER:
			return player_color
		ServerNode.Owner.ENEMY:
			return enemy_color
		ServerNode.Owner.ALLY:
			return ally_color
		_:
			return neutral_color

func set_network_manager(manager: NetworkManager) -> void:
	network_manager = manager

func set_selected_server(server: ServerNode) -> void:
	selected_server = server
