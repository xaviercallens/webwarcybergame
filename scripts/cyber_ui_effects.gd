extends CanvasLayer
class_name CyberUIEffects

# Cyberpunk UI visual effects layer
# Adds scanlines, corner decorations, and animated effects

@export var scanline_opacity: float = 0.08
@export var scanline_spacing: int = 4
@export var corner_size: float = 20.0
@export var enable_glitch: bool = true
@export var glitch_interval: float = 3.0
@export var glitch_duration: float = 0.15

var time: float = 0.0
var glitch_timer: float = 0.0
var is_glitching: bool = false
var glitch_offset: Vector2 = Vector2.ZERO

@onready var effects_rect: ColorRect

func _ready() -> void:
	# Create the effects drawing layer
	layer = 100  # Draw on top
	
	# Create a Control to draw on
	var control = Control.new()
	control.name = "EffectsControl"
	control.set_anchors_preset(Control.PRESET_FULL_RECT)
	control.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(control)
	
	# Create custom drawing node
	var drawer = CyberDrawer.new()
	drawer.name = "CyberDrawer"
	drawer.cyber_effects = self
	drawer.set_anchors_preset(Control.PRESET_FULL_RECT)
	drawer.mouse_filter = Control.MOUSE_FILTER_IGNORE
	control.add_child(drawer)

func _process(delta: float) -> void:
	time += delta
	
	# Handle glitch effect
	if enable_glitch:
		glitch_timer += delta
		if is_glitching:
			if glitch_timer >= glitch_duration:
				is_glitching = false
				glitch_timer = 0.0
				glitch_offset = Vector2.ZERO
		else:
			if glitch_timer >= glitch_interval + randf() * 2.0:
				trigger_glitch()

func trigger_glitch() -> void:
	is_glitching = true
	glitch_timer = 0.0
	glitch_offset = Vector2(randf_range(-5, 5), randf_range(-2, 2))

# Inner class for custom drawing
class CyberDrawer extends Control:
	var cyber_effects: CyberUIEffects
	
	func _process(_delta: float) -> void:
		queue_redraw()
	
	func _draw() -> void:
		if not cyber_effects:
			return
		
		var viewport_size = get_viewport_rect().size
		
		# Draw scanlines
		_draw_scanlines(viewport_size)
		
		# Draw corner decorations
		_draw_corners(viewport_size)
		
		# Draw edge lines
		_draw_edge_accents(viewport_size)
		
		# Draw glitch effect
		if cyber_effects.is_glitching:
			_draw_glitch_effect(viewport_size)
	
	func _draw_scanlines(size: Vector2) -> void:
		var scanline_color = Color(0, 0, 0, cyber_effects.scanline_opacity)
		var spacing = cyber_effects.scanline_spacing
		
		for y in range(0, int(size.y), spacing):
			draw_line(Vector2(0, y), Vector2(size.x, y), scanline_color, 1.0)
	
	func _draw_corners(size: Vector2) -> void:
		var corner_size = cyber_effects.corner_size
		var pulse = (sin(cyber_effects.time * 2.0) + 1.0) / 2.0
		var color = Color(0, 0.8 + pulse * 0.2, 0.9 + pulse * 0.1, 0.6 + pulse * 0.2)
		var thickness = 2.0
		
		# Top-left corner
		draw_line(Vector2(0, 0), Vector2(corner_size, 0), color, thickness)
		draw_line(Vector2(0, 0), Vector2(0, corner_size), color, thickness)
		
		# Top-right corner
		draw_line(Vector2(size.x - corner_size, 0), Vector2(size.x, 0), color, thickness)
		draw_line(Vector2(size.x, 0), Vector2(size.x, corner_size), color, thickness)
		
		# Bottom-left corner
		draw_line(Vector2(0, size.y - corner_size), Vector2(0, size.y), color, thickness)
		draw_line(Vector2(0, size.y), Vector2(corner_size, size.y), color, thickness)
		
		# Bottom-right corner
		draw_line(Vector2(size.x, size.y - corner_size), Vector2(size.x, size.y), color, thickness)
		draw_line(Vector2(size.x - corner_size, size.y), Vector2(size.x, size.y), color, thickness)
		
		# Corner dots
		var dot_color = Color(0, 1.0, 1.0, 0.8)
		draw_circle(Vector2(4, 4), 3, dot_color)
		draw_circle(Vector2(size.x - 4, 4), 3, dot_color)
		draw_circle(Vector2(4, size.y - 4), 3, dot_color)
		draw_circle(Vector2(size.x - 4, size.y - 4), 3, dot_color)
	
	func _draw_edge_accents(size: Vector2) -> void:
		var pulse = (sin(cyber_effects.time * 1.5) + 1.0) / 2.0
		var accent_color = Color(0, 0.6, 0.8, 0.15 + pulse * 0.1)
		
		# Top edge gradient line
		var top_rect = Rect2(0, 0, size.x, 3)
		draw_rect(top_rect, accent_color)
		
		# Bottom edge gradient line
		var bottom_rect = Rect2(0, size.y - 3, size.x, 3)
		draw_rect(bottom_rect, accent_color)
	
	func _draw_glitch_effect(size: Vector2) -> void:
		# Draw colored offset rectangles for glitch
		var num_glitches = randi_range(3, 8)
		
		for i in range(num_glitches):
			var glitch_y = randf() * size.y
			var glitch_height = randf_range(2, 15)
			var glitch_color: Color
			
			match randi() % 3:
				0: glitch_color = Color(1, 0, 0, 0.3)  # Red
				1: glitch_color = Color(0, 1, 1, 0.3)  # Cyan
				2: glitch_color = Color(1, 0, 1, 0.3)  # Magenta
			
			var offset_x = randf_range(-10, 10)
			draw_rect(Rect2(offset_x, glitch_y, size.x, glitch_height), glitch_color)
