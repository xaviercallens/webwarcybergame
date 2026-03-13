extends Node2D
class_name ServerNode

signal server_selected(server: ServerNode)
signal server_captured(server: ServerNode, new_owner: int)
signal server_attacked(server: ServerNode)

enum Owner { NEUTRAL, PLAYER, ENEMY, ALLY }

# Server properties
@export var server_name: String = "Server"
@export var owner_type: Owner = Owner.NEUTRAL
@export var firewall_strength: float = 100.0
@export var max_firewall: float = 100.0
@export var processing_power: float = 10.0  # Attack power
@export var regeneration_rate: float = 2.0  # Firewall regen per second

# Visual nodes
@onready var sprite: Sprite2D = $Sprite2D
@onready var selection_ring: Sprite2D = $SelectionRing
@onready var health_bar: ProgressBar = $HealthBar
@onready var attack_particles: GPUParticles2D = $AttackParticles
@onready var defense_particles: GPUParticles2D = $DefenseParticles
@onready var label: Label = $Label

# Connected servers (for network topology)
var connected_servers: Array[ServerNode] = []
var is_selected: bool = false
var is_under_attack: bool = false
var incoming_damage: float = 0.0
var is_target_highlighted: bool = false

# Attack pulse animation
var attack_pulse_time: float = 0.0
var base_scale: Vector2 = Vector2.ONE
var base_modulate: Color = Color.WHITE

# Textures for different owners
var texture_neutral: Texture2D
var texture_player: Texture2D
var texture_enemy: Texture2D
var texture_ally: Texture2D

func _ready() -> void:
	# Load textures
	texture_neutral = load("res://assets/images/server_node_neutral.png")
	texture_player = load("res://assets/images/server_node_player.png")
	texture_enemy = load("res://assets/images/server_node_enemy.png")
	texture_ally = load("res://assets/images/server_node_ally.png")
	
	update_visuals()
	
	if selection_ring:
		selection_ring.visible = false
	
	# Setup health bar
	if health_bar:
		health_bar.max_value = max_firewall
		health_bar.value = firewall_strength

func _process(delta: float) -> void:
	# Regenerate firewall when not under attack
	if not is_under_attack and firewall_strength < max_firewall:
		firewall_strength = min(firewall_strength + regeneration_rate * delta, max_firewall)
		update_health_bar()
	
	# Process incoming damage
	if incoming_damage > 0:
		apply_damage(incoming_damage * delta)
		incoming_damage = 0
	
	# Update attack pulse animation
	_update_attack_pulse(delta)
	
	# Redraw danger ring if needed
	if is_under_attack or attack_pulse_time > 0 or is_target_highlighted:
		queue_redraw()
	
	# Reset attack state each frame (will be set by combat manager)
	is_under_attack = false

func _update_attack_pulse(delta: float) -> void:
	if is_under_attack:
		# Increment pulse time when under attack
		attack_pulse_time += delta * 8.0  # Fast pulse
		
		# Calculate pulse values
		var pulse: float = (sin(attack_pulse_time) + 1.0) / 2.0
		var scale_pulse: float = 1.0 + pulse * 0.15  # Scale between 1.0 and 1.15
		var color_pulse: float = 0.3 + pulse * 0.7  # Red intensity varies
		
		# Apply scale pulse
		if sprite:
			sprite.scale = base_scale * scale_pulse
		
		# Apply red warning flash overlay
		var warning_color: Color = base_modulate.lerp(Color(1.0, 0.3, 0.3), color_pulse * 0.5)
		if sprite:
			sprite.modulate = warning_color
		
		# Make health bar pulse too
		if health_bar:
			health_bar.modulate = Color(1.0, 0.3 + pulse * 0.3, 0.3 + pulse * 0.3)
	else:
		# Smoothly return to normal when not under attack
		if attack_pulse_time > 0:
			attack_pulse_time = max(0, attack_pulse_time - delta * 4.0)
			var recovery: float = attack_pulse_time / (PI * 2)  # Normalize
			
			if sprite:
				sprite.scale = base_scale.lerp(base_scale * 1.1, recovery * 0.5)
				sprite.modulate = base_modulate
			
			if attack_pulse_time <= 0:
				# Fully reset
				if sprite:
					sprite.scale = base_scale
				update_visuals()  # Restore proper colors
				update_health_bar()  # Restore health bar color

func update_visuals() -> void:
	if not sprite:
		return
	
	var cb = GameState and GameState.colorblind_mode
	
	match owner_type:
		Owner.NEUTRAL:
			sprite.texture = texture_neutral
			base_modulate = Color(0.7, 0.7, 0.7, 1.0)
		Owner.PLAYER:
			sprite.texture = texture_player
			base_modulate = Color(0.2, 0.5, 1.0, 1.0) if cb else Color(0.5, 1.0, 0.5, 1.0)
		Owner.ENEMY:
			sprite.texture = texture_enemy
			base_modulate = Color(1.0, 0.5, 0.0, 1.0) if cb else Color(1.0, 0.5, 0.5, 1.0)
		Owner.ALLY:
			sprite.texture = texture_ally
			base_modulate = Color(0.9, 0.8, 0.2, 1.0) if cb else Color(0.5, 0.5, 1.0, 1.0)
	
	sprite.modulate = base_modulate
	base_scale = sprite.scale
	
	if label:
		label.text = server_name

func update_health_bar() -> void:
	if health_bar:
		health_bar.value = firewall_strength
		
		# Color based on health
		var health_ratio = firewall_strength / max_firewall
		if health_ratio > 0.6:
			health_bar.modulate = Color(0.3, 1.0, 0.3)
		elif health_ratio > 0.3:
			health_bar.modulate = Color(1.0, 1.0, 0.3)
		else:
			health_bar.modulate = Color(1.0, 0.3, 0.3)

func apply_damage(damage: float) -> void:
	firewall_strength -= damage
	update_health_bar()
	
	if firewall_strength <= 0:
		firewall_strength = 0
		# Server is vulnerable to capture
		emit_signal("server_attacked", self)

var _shield_sound_cooldown: float = 0.0

func receive_attack(damage: float) -> void:
	is_under_attack = true
	incoming_damage += damage
	
	if defense_particles:
		defense_particles.emitting = true
	
	# Play shield hit sound with cooldown to avoid spam
	_shield_sound_cooldown -= get_process_delta_time()
	if _shield_sound_cooldown <= 0 and Audio and randf() < 0.15:
		Audio.play_shield_hit()
		_shield_sound_cooldown = 0.5  # Half second cooldown

func capture(new_owner: Owner) -> void:
	var old_owner = owner_type
	owner_type = new_owner
	firewall_strength = max_firewall * 0.3  # Start with 30% firewall after capture
	update_visuals()
	update_health_bar()
	emit_signal("server_captured", self, new_owner)

func select() -> void:
	is_selected = true
	if selection_ring:
		selection_ring.visible = true
		selection_ring.modulate = Color(1.0, 1.0, 0.0, 0.8)

func deselect() -> void:
	is_selected = false
	if selection_ring:
		selection_ring.visible = false

func set_target_highlight(highlight: bool) -> void:
	is_target_highlighted = highlight
	queue_redraw()

func add_connection(server: ServerNode) -> void:
	if server not in connected_servers:
		connected_servers.append(server)

func is_connected_to(server: ServerNode) -> bool:
	return server in connected_servers

func get_attack_power() -> float:
	# Attack power scales with health
	return processing_power * (firewall_strength / max_firewall)

func _draw() -> void:
	# Draw danger ring when under attack
	if attack_pulse_time > 0:
		var pulse: float = (sin(attack_pulse_time * 1.5) + 1.0) / 2.0
		var ring_alpha: float = 0.3 + pulse * 0.5
		var ring_radius: float = 35.0 + pulse * 10.0
		
		# Outer danger glow
		var outer_color: Color = Color(1.0, 0.2, 0.1, ring_alpha * 0.3)
		draw_circle(Vector2.ZERO, ring_radius + 15.0, outer_color)
		
		# Middle ring
		var mid_color: Color = Color(1.0, 0.3, 0.1, ring_alpha * 0.5)
		draw_circle(Vector2.ZERO, ring_radius + 8.0, mid_color)
		
		# Draw pulsing ring outline
		var ring_color: Color = Color(1.0, 0.4, 0.2, ring_alpha)
		_draw_ring(Vector2.ZERO, ring_radius, 3.0, ring_color)
		
		# Inner bright ring
		var inner_color: Color = Color(1.0, 0.6, 0.3, ring_alpha * 0.8)
		_draw_ring(Vector2.ZERO, ring_radius - 5.0, 2.0, inner_color)
		
		# Warning arc segments (rotating)
		_draw_warning_arcs(ring_radius + 3.0, ring_alpha)
		
	# Draw target highlight for click-to-attack
	elif is_target_highlighted:
		var time = Time.get_ticks_msec() / 1000.0
		var pulse: float = (sin(time * 4.0) + 1.0) / 2.0
		var highlight_color = Color(1.0, 0.2, 0.2, 0.6 + pulse * 0.4)
		_draw_ring(Vector2.ZERO, 38.0, 2.0, highlight_color)
		
		# Draw crosshairs
		var crosshair_len = 8.0
		var dist = 42.0 + pulse * 4.0
		draw_line(Vector2(-dist, 0), Vector2(-dist + crosshair_len, 0), highlight_color, 2.0, true)
		draw_line(Vector2(dist, 0), Vector2(dist - crosshair_len, 0), highlight_color, 2.0, true)
		draw_line(Vector2(0, -dist), Vector2(0, -dist + crosshair_len), highlight_color, 2.0, true)
		draw_line(Vector2(0, dist), Vector2(0, dist - crosshair_len), highlight_color, 2.0, true)

func _draw_ring(center: Vector2, radius: float, width: float, color: Color) -> void:
	var segments: int = 32
	var prev_point: Vector2 = center + Vector2(radius, 0)
	
	for i in range(1, segments + 1):
		var angle: float = (2.0 * PI * i) / segments
		var point: Vector2 = center + Vector2(cos(angle), sin(angle)) * radius
		draw_line(prev_point, point, color, width, true)
		prev_point = point

func _draw_warning_arcs(radius: float, alpha: float) -> void:
	# Draw rotating warning arc segments
	var rotation_offset: float = attack_pulse_time * 2.0
	var arc_count: int = 4
	var arc_length: float = PI / 6.0  # 30 degrees each
	
	for i in range(arc_count):
		var start_angle: float = rotation_offset + (2.0 * PI * i / arc_count)
		var segments: int = 8
		
		var color: Color = Color(1.0, 0.8, 0.3, alpha)
		
		for j in range(segments):
			var a1: float = start_angle + (arc_length * j / segments)
			var a2: float = start_angle + (arc_length * (j + 1) / segments)
			var p1: Vector2 = Vector2(cos(a1), sin(a1)) * radius
			var p2: Vector2 = Vector2(cos(a2), sin(a2)) * radius
			draw_line(p1, p2, color, 2.5, true)

func _on_area_2d_input_event(_viewport: Node, event: InputEvent, _shape_idx: int) -> void:
	if event is InputEventMouseButton:
		if event.button_index == MOUSE_BUTTON_LEFT and event.pressed:
			emit_signal("server_selected", self)
