extends CanvasLayer
class_name PauseMenu

var pause_panel: PanelContainer
var is_paused: bool = false

func _ready() -> void:
	layer = 20  # Above everything
	process_mode = Node.PROCESS_MODE_ALWAYS  # Always process even when paused
	_build_ui()
	pause_panel.visible = false

func _input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_cancel"):
		if is_paused:
			resume()
		else:
			pause()
		get_viewport().set_input_as_handled()

func pause() -> void:
	is_paused = true
	get_tree().paused = true
	pause_panel.visible = true
	if Audio:
		Audio.play_ui_click()

func resume() -> void:
	is_paused = false
	get_tree().paused = false
	pause_panel.visible = false
	if Audio:
		Audio.play_ui_click()

func _build_ui() -> void:
	# Full-screen dark overlay
	var overlay = ColorRect.new()
	overlay.set_anchors_preset(Control.PRESET_FULL_RECT)
	overlay.color = Color(0, 0.02, 0.05, 0.75)
	overlay.mouse_filter = Control.MOUSE_FILTER_STOP
	add_child(overlay)
	
	# Center panel
	pause_panel = PanelContainer.new()
	pause_panel.set_anchors_preset(Control.PRESET_CENTER)
	pause_panel.offset_left = -180
	pause_panel.offset_top = -200
	pause_panel.offset_right = 180
	pause_panel.offset_bottom = 200
	
	var panel_style = StyleBoxFlat.new()
	panel_style.bg_color = Color(0.02, 0.05, 0.1, 0.95)
	panel_style.border_color = Color(0, 0.8, 0.9, 0.8)
	panel_style.set_border_width_all(2)
	panel_style.set_corner_radius_all(6)
	panel_style.shadow_color = Color(0, 0.5, 0.6, 0.3)
	panel_style.shadow_size = 12
	panel_style.content_margin_left = 30
	panel_style.content_margin_right = 30
	panel_style.content_margin_top = 30
	panel_style.content_margin_bottom = 30
	pause_panel.add_theme_stylebox_override("panel", panel_style)
	overlay.add_child(pause_panel)
	
	var vbox = VBoxContainer.new()
	vbox.add_theme_constant_override("separation", 16)
	pause_panel.add_child(vbox)
	
	# Title
	var title = Label.new()
	title.text = "// SYSTEM PAUSED"
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title.add_theme_color_override("font_color", Color(0, 1, 0.9))
	title.add_theme_font_size_override("font_size", 22)
	vbox.add_child(title)
	
	# Separator
	var sep = HSeparator.new()
	vbox.add_child(sep)
	
	# Spacer
	var spacer = Control.new()
	spacer.custom_minimum_size = Vector2(0, 10)
	vbox.add_child(spacer)
	
	# Resume button
	var resume_btn = _create_button("[ RESUME ]")
	resume_btn.pressed.connect(resume)
	vbox.add_child(resume_btn)
	
	# Restart button
	var restart_btn = _create_button("[ RESTART MISSION ]")
	restart_btn.pressed.connect(_on_restart)
	vbox.add_child(restart_btn)
	
	# Main Menu button
	var menu_btn = _create_button("[ MAIN MENU ]")
	menu_btn.pressed.connect(_on_main_menu)
	vbox.add_child(menu_btn)
	
	# Quit button
	var quit_btn = _create_button("[ QUIT ]")
	quit_btn.pressed.connect(_on_quit)
	vbox.add_child(quit_btn)

func _create_button(text: String) -> Button:
	var btn = Button.new()
	btn.text = text
	btn.custom_minimum_size = Vector2(250, 44)
	
	var normal = StyleBoxFlat.new()
	normal.bg_color = Color(0.03, 0.08, 0.12, 0.9)
	normal.border_color = Color(0, 0.6, 0.7, 0.5)
	normal.set_border_width_all(1)
	normal.set_corner_radius_all(4)
	normal.content_margin_left = 16
	normal.content_margin_right = 16
	normal.content_margin_top = 8
	normal.content_margin_bottom = 8
	btn.add_theme_stylebox_override("normal", normal)
	
	var hover = normal.duplicate()
	hover.bg_color = Color(0.05, 0.12, 0.18, 0.95)
	hover.border_color = Color(0, 0.9, 1.0, 0.8)
	hover.shadow_color = Color(0, 0.5, 0.6, 0.3)
	hover.shadow_size = 6
	btn.add_theme_stylebox_override("hover", hover)
	
	var pressed = normal.duplicate()
	pressed.bg_color = Color(0.08, 0.15, 0.22, 0.95)
	btn.add_theme_stylebox_override("pressed", pressed)
	
	btn.add_theme_color_override("font_color", Color(0.5, 0.9, 1.0))
	btn.add_theme_color_override("font_hover_color", Color(0, 1, 0.9))
	
	return btn

func _on_restart() -> void:
	resume()  # Unpause first
	get_tree().reload_current_scene()

func _on_main_menu() -> void:
	resume()  # Unpause first
	get_tree().change_scene_to_file("res://scenes/main_menu.tscn")

func _on_quit() -> void:
	get_tree().quit()
