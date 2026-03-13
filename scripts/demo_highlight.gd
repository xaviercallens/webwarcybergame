extends Control
class_name DemoHighlight

# Draws highlight rectangles around UI elements during demo

var highlight_area: Rect2 = Rect2()
var is_highlighting: bool = false
var pulse_time: float = 0.0

func _process(delta: float) -> void:
	if is_highlighting:
		pulse_time += delta
		queue_redraw()

func _draw() -> void:
	if not is_highlighting:
		return
	
	var pulse = (sin(pulse_time * 4.0) + 1.0) / 2.0
	
	# Draw darkened area everywhere except highlight
	_draw_darkened_overlay()
	
	# Draw highlight border
	var border_color = Color(0, 1, 1, 0.6 + pulse * 0.4)
	var glow_color = Color(0, 1, 1, 0.2 + pulse * 0.1)
	
	# Outer glow
	var glow_rect = highlight_area.grow(8)
	draw_rect(glow_rect, glow_color, false, 6.0)
	
	# Main border
	draw_rect(highlight_area, border_color, false, 3.0)
	
	# Corner accents
	_draw_corner_accents(border_color)
	
	# Pulsing inner glow
	var inner_glow = Color(0, 1, 1, 0.05 + pulse * 0.05)
	draw_rect(highlight_area, inner_glow, true)

func _draw_darkened_overlay() -> void:
	var screen_size = get_viewport_rect().size
	var dark_color = Color(0, 0, 0, 0.4)
	
	# Top
	if highlight_area.position.y > 0:
		draw_rect(Rect2(0, 0, screen_size.x, highlight_area.position.y), dark_color, true)
	
	# Bottom
	var bottom_y = highlight_area.position.y + highlight_area.size.y
	if bottom_y < screen_size.y:
		draw_rect(Rect2(0, bottom_y, screen_size.x, screen_size.y - bottom_y), dark_color, true)
	
	# Left
	if highlight_area.position.x > 0:
		draw_rect(Rect2(0, highlight_area.position.y, highlight_area.position.x, highlight_area.size.y), dark_color, true)
	
	# Right
	var right_x = highlight_area.position.x + highlight_area.size.x
	if right_x < screen_size.x:
		draw_rect(Rect2(right_x, highlight_area.position.y, screen_size.x - right_x, highlight_area.size.y), dark_color, true)

func _draw_corner_accents(color: Color) -> void:
	var corner_len: float = 15.0
	var pos = highlight_area.position
	var size = highlight_area.size
	
	# Top-left
	draw_line(pos, pos + Vector2(corner_len, 0), color, 3.0)
	draw_line(pos, pos + Vector2(0, corner_len), color, 3.0)
	
	# Top-right
	var tr = pos + Vector2(size.x, 0)
	draw_line(tr, tr + Vector2(-corner_len, 0), color, 3.0)
	draw_line(tr, tr + Vector2(0, corner_len), color, 3.0)
	
	# Bottom-left
	var bl = pos + Vector2(0, size.y)
	draw_line(bl, bl + Vector2(corner_len, 0), color, 3.0)
	draw_line(bl, bl + Vector2(0, -corner_len), color, 3.0)
	
	# Bottom-right
	var br = pos + size
	draw_line(br, br + Vector2(-corner_len, 0), color, 3.0)
	draw_line(br, br + Vector2(0, -corner_len), color, 3.0)

func set_highlight_area(rect: Rect2) -> void:
	highlight_area = rect
	is_highlighting = true
	pulse_time = 0.0
	queue_redraw()

func clear_highlight() -> void:
	is_highlighting = false
	queue_redraw()
