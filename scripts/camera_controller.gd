extends Camera2D
class_name CameraController

# Camera controller for panning and zooming the strategy map

@export var zoom_speed: float = 0.1
@export var min_zoom: float = 0.5
@export var max_zoom: float = 2.0
@export var pan_speed: float = 500.0

var is_dragging: bool = false
var drag_start_mouse_pos: Vector2
var drag_start_camera_pos: Vector2

func _ready() -> void:
	# Center camera initially
	position = Vector2(640, 360)
	make_current()

func _input(event: InputEvent) -> void:
	# Handle Zoom
	if event is InputEventMouseButton:
		if event.button_index == MOUSE_BUTTON_WHEEL_UP and event.pressed:
			_zoom_camera(1)
		elif event.button_index == MOUSE_BUTTON_WHEEL_DOWN and event.pressed:
			_zoom_camera(-1)
			
		# Handle Drag panning
		if event.button_index == MOUSE_BUTTON_MIDDLE or event.button_index == MOUSE_BUTTON_RIGHT:
			if event.pressed:
				is_dragging = true
				drag_start_mouse_pos = event.position
				drag_start_camera_pos = position
			else:
				is_dragging = false
				
	# Process dragging
	elif event is InputEventMouseMotion and is_dragging:
		var raw_delta = drag_start_mouse_pos - event.position
		# Scale delta by zoom level so dragging feels consistent at all zoom levels
		position = drag_start_camera_pos + raw_delta / zoom

func _process(delta: float) -> void:
	if not is_dragging:
		# Keyboard panning
		var move_dir = Vector2.ZERO
		
		# Allow WASD mapping (using UI actions if they map, or hardcoding fallback)
		if Input.is_action_pressed("ui_up") or Input.is_key_pressed(KEY_W):
			move_dir.y -= 1
		if Input.is_action_pressed("ui_down") or Input.is_key_pressed(KEY_S):
			move_dir.y += 1
		if Input.is_action_pressed("ui_left") or Input.is_key_pressed(KEY_A):
			move_dir.x -= 1
		if Input.is_action_pressed("ui_right") or Input.is_key_pressed(KEY_D):
			move_dir.x += 1
			
		if move_dir != Vector2.ZERO:
			position += move_dir.normalized() * pan_speed * delta / zoom.x

func _zoom_camera(direction: int) -> void:
	var old_zoom = zoom
	var target_zoom = zoom * (1.0 + zoom_speed * direction)
	
	# Clamp zoom
	target_zoom.x = clamp(target_zoom.x, min_zoom, max_zoom)
	target_zoom.y = clamp(target_zoom.y, min_zoom, max_zoom)
	
	# Only adjust position if zoom actually changed
	if target_zoom != old_zoom:
		# Get mouse position before zoom
		var mouse_pos = get_global_mouse_position()
		
		zoom = target_zoom
		
		# Adjust position to zoom towards mouse
		var new_mouse_pos = get_global_mouse_position()
		position += mouse_pos - new_mouse_pos
