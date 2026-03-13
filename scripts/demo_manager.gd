extends CanvasLayer
class_name DemoManager

# Demo mode manager - shows scripted tutorial gameplay

signal demo_completed
signal step_changed(step_index: int)

@export var auto_advance_delay: float = 4.0
@export var typing_speed: float = 0.03

# References (set by game_manager)
var network_manager: NetworkManager
var combat_manager: CombatManager
var alliance_manager: AllianceManager
var game_ui: GameUI

# Demo state
var demo_active: bool = false
var current_step: int = 0
var is_typing: bool = false
var typing_text: String = ""
var displayed_text: String = ""
var typing_timer: float = 0.0
var step_timer: float = 0.0
var waiting_for_click: bool = false
var auto_advance: bool = true

# Demo steps
var demo_steps: Array[Dictionary] = []

# UI elements
var overlay: ColorRect
var panel: PanelContainer
var title_label: Label
var description_label: RichTextLabel
var step_indicator: Label
var continue_button: Button
var skip_button: Button
var highlight_rect: Control

func _ready() -> void:
	layer = 50
	_create_ui()
	_setup_demo_steps()
	visible = false

func _process(delta: float) -> void:
	if not demo_active:
		return
	
	# Handle typing effect
	if is_typing:
		typing_timer += delta
		if typing_timer >= typing_speed:
			typing_timer = 0.0
			if displayed_text.length() < typing_text.length():
				displayed_text += typing_text[displayed_text.length()]
				description_label.text = displayed_text
			else:
				is_typing = false
	
	# Auto-advance timer
	if auto_advance and not waiting_for_click and not is_typing:
		step_timer += delta
		if step_timer >= auto_advance_delay:
			advance_step()

func _create_ui() -> void:
	# Semi-transparent overlay
	overlay = ColorRect.new()
	overlay.color = Color(0, 0.02, 0.05, 0.7)
	overlay.set_anchors_preset(Control.PRESET_FULL_RECT)
	overlay.mouse_filter = Control.MOUSE_FILTER_STOP
	add_child(overlay)
	
	# Main panel
	panel = PanelContainer.new()
	panel.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
	panel.anchor_top = 1.0
	panel.anchor_bottom = 1.0
	panel.offset_left = -350
	panel.offset_right = 350
	panel.offset_top = -220
	panel.offset_bottom = -20
	
	# Apply cyberpunk style
	var style = StyleBoxFlat.new()
	style.bg_color = Color(0.02, 0.05, 0.1, 0.95)
	style.border_color = Color(0, 0.8, 0.9, 0.8)
	style.set_border_width_all(2)
	style.set_corner_radius_all(4)
	style.shadow_color = Color(0, 0.8, 0.9, 0.3)
	style.shadow_size = 8
	panel.add_theme_stylebox_override("panel", style)
	add_child(panel)
	
	var margin = MarginContainer.new()
	margin.add_theme_constant_override("margin_left", 20)
	margin.add_theme_constant_override("margin_right", 20)
	margin.add_theme_constant_override("margin_top", 15)
	margin.add_theme_constant_override("margin_bottom", 15)
	panel.add_child(margin)
	
	var vbox = VBoxContainer.new()
	vbox.add_theme_constant_override("separation", 12)
	margin.add_child(vbox)
	
	# Header row
	var header = HBoxContainer.new()
	vbox.add_child(header)
	
	var icon1 = Label.new()
	icon1.text = "[>]"
	icon1.add_theme_color_override("font_color", Color(0, 1, 0.8, 1))
	header.add_child(icon1)
	
	title_label = Label.new()
	title_label.text = " DEMO_MODE.exe"
	title_label.add_theme_color_override("font_color", Color(0, 1, 0.8, 1))
	title_label.add_theme_font_size_override("font_size", 20)
	title_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	title_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	header.add_child(title_label)
	
	var icon2 = Label.new()
	icon2.text = "[<]"
	icon2.add_theme_color_override("font_color", Color(0, 1, 0.8, 1))
	header.add_child(icon2)
	
	# Separator
	var sep = HSeparator.new()
	var sep_style = StyleBoxFlat.new()
	sep_style.bg_color = Color(0, 0.6, 0.7, 0.5)
	sep.add_theme_stylebox_override("separator", sep_style)
	vbox.add_child(sep)
	
	# Description
	description_label = RichTextLabel.new()
	description_label.bbcode_enabled = true
	description_label.fit_content = false
	description_label.scroll_active = false
	description_label.custom_minimum_size = Vector2(0, 80)
	description_label.size_flags_vertical = Control.SIZE_EXPAND_FILL
	description_label.add_theme_color_override("default_color", Color(0, 0.9, 1, 0.95))
	vbox.add_child(description_label)
	
	# Step indicator
	step_indicator = Label.new()
	step_indicator.text = "Step 1 / 10"
	step_indicator.add_theme_color_override("font_color", Color(0.5, 0.7, 0.8, 0.7))
	step_indicator.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	vbox.add_child(step_indicator)
	
	# Button row
	var button_row = HBoxContainer.new()
	button_row.add_theme_constant_override("separation", 15)
	button_row.alignment = BoxContainer.ALIGNMENT_CENTER
	vbox.add_child(button_row)
	
	skip_button = Button.new()
	skip_button.text = "[ SKIP DEMO ]"
	skip_button.custom_minimum_size = Vector2(140, 40)
	_style_button(skip_button)
	skip_button.pressed.connect(_on_skip_pressed)
	button_row.add_child(skip_button)
	
	continue_button = Button.new()
	continue_button.text = "[ CONTINUE >> ]"
	continue_button.custom_minimum_size = Vector2(160, 40)
	_style_button(continue_button)
	continue_button.pressed.connect(_on_continue_pressed)
	button_row.add_child(continue_button)
	
	# Highlight rectangle (for pointing at UI elements)
	highlight_rect = Control.new()
	highlight_rect.set_anchors_preset(Control.PRESET_FULL_RECT)
	highlight_rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
	highlight_rect.set_script(preload("res://scripts/demo_highlight.gd"))
	add_child(highlight_rect)

func _style_button(btn: Button) -> void:
	var normal = StyleBoxFlat.new()
	normal.bg_color = Color(0.05, 0.1, 0.15, 0.9)
	normal.border_color = Color(0, 0.8, 0.9, 0.6)
	normal.set_border_width_all(2)
	normal.set_corner_radius_all(3)
	btn.add_theme_stylebox_override("normal", normal)
	
	var hover = StyleBoxFlat.new()
	hover.bg_color = Color(0, 0.3, 0.4, 0.9)
	hover.border_color = Color(0, 1, 1, 1)
	hover.set_border_width_all(2)
	hover.set_corner_radius_all(3)
	btn.add_theme_stylebox_override("hover", hover)
	
	btn.add_theme_color_override("font_color", Color(0, 0.9, 1, 1))
	btn.add_theme_color_override("font_hover_color", Color(0.5, 1, 1, 1))

func _setup_demo_steps() -> void:
	demo_steps = [
		{
			"title": " WELCOME.txt",
			"text": "[center][color=#00ffdd]// CYBER//WAR DEMONSTRATION //[/color][/center]\n\nWelcome to the tactical demonstration.\n\nThis demo will [color=#ffcc00]simulate an end user session[/color] so you can learn all the commands and mechanics.\n\n[color=#666688]Watch carefully as we walk through a simple scenario.[/color]",
			"action": "intro",
			"delay": 5.0
		},
		{
			"title": " CAMERA_SYNC.sys",
			"text": "[color=#00ff88]>> NAVIGATING THE NETWORK[/color]\n\nYou can use your [color=#ffcc00]Scroll Wheel[/color] to zoom in and out of the map.\n\nTo pan the camera, hold [color=#00ddff]Right-Click[/color] and drag, or use [color=#00ddff]WASD[/color] keys.\n\n[color=#666688]Let's zoom out to see the full procedural terrain...[/color]",
			"action": "camera_controls",
			"delay": 6.0
		},
		{
			"title": " NETWORK_OVERVIEW.dat",
			"text": "[color=#00ff88]>> OBSERVE THE NODES[/color]\n\nThe network consists of servers. Your nodes are [color=#00ff88]GREEN[/color].\nWe need to capture hostile [color=#ff4444]RED[/color] and neutral [color=#66aaaa]CYAN[/color] nodes.\n\n[color=#4488ff]BLUE[/color] nodes are potential allies.\n\n[color=#666688]Your network status is on the top-left HUD.[/color]",
			"action": "show_network",
			"delay": 6.0
		},
		{
			"title": " NODE_SELECTION.exe",
			"text": "[color=#00ff88]>> SELECTING A NODE[/color]\n\nTo take action, [color=#ffcc00]Click[/color] on one of your GREEN servers.\n\nThe [color=#00ddff]Server Info Panel[/color] on the right displays its stats.",
			"action": "player_select",
			"delay": 5.0
		},
		{
			"title": " TARGET_ACQUISITION.sys",
			"text": "[color=#ff8844]>> DIRECT INTERACTION[/color]\n\nNotice the [color=#ff4444]pulsing target brackets[/color] on adjacent enemy nodes?\n\nYou don't need a clunky menu anymore. You can [color=#ffcc00]Click directly[/color] on a highlighted node to launch an attack!",
			"action": "show_targets",
			"delay": 6.0
		},
		{
			"title": " ATTACK_INIT.exe",
			"text": "[color=#ff8844]>> INITIATING ATTACK[/color]\n\nAttack launched! Watch the [color=#ff8844]continuous data stream[/color] overload the target firewall.\n\n[color=#666688]Hacking takes time... wait for the firewall to reach zero.[/color]",
			"action": "player_attack",
			"delay": 6.0
		},
		{
			"title": " NODE_CAPTURED.log",
			"text": "[color=#00ff88]>> NODE SECURED![/color]\n\nThe firewall is breached! The server is now [color=#00ff88]GREEN[/color].\n\n[color=#ffcc00]Did you see the Notification Toast?[/color] Your newly captured node is now regenerating its health.",
			"action": "capture_node",
			"delay": 6.0
		},
		{
			"title": " ENEMY_RESPONSE.sys",
			"text": "[color=#ff4444]>> HOSTILE COUNTER-ATTACK[/color]\n\nWARNING: The [color=#ff4444]RED Faction AI[/color] is retaliating!\n\nThey have targeted your weakest node. [color=#ffcc00]Nodes under attack pulse red.[/color]",
			"action": "enemy_attack",
			"delay": 5.0
		},
		{
			"title": " DEFENSE_PROTOCOL.exe",
			"text": "[color=#00ff88]>> DEFENDING NODES[/color]\n\nDon't let them take it! You can select your node and attack them back to [color=#00ddff]disrupt their hack[/color].\n\n[color=#666688]Both sides are now locked in combat.[/color]",
			"action": "combat_defense",
			"delay": 6.0
		},
		{
			"title": " DIPLOMACY_LINK.cfg",
			"text": "[color=#4488ff]>> FORMING ALLIANCES[/color]\n\nLet's get some help. The [color=#4488ff]BLUE Faction[/color] is friendly.\n\nClicking [color=#00ddff]REQUEST LINK[/color] in the HUD forms an alliance. They will attack your enemies and share conquered nodes!",
			"action": "show_alliance",
			"delay": 6.0
		},
		{
			"title": " DOMINANCE_REACHED.sys",
			"text": "[color=#00ff88]>> VICTORY CONDITION MET[/color]\n\nFast-forwarding time...\nWe have captured enough servers to reach [color=#00ff88]75% Network Control[/color]! Watch the Progress Bar at the top.",
			"action": "victory_condition",
			"delay": 5.0
		},
		{
			"title": " EXPLANATION_END.txt",
			"text": "[center][color=#00ff88]// TOTAL DOMINANCE //[/color][/center]\n\nThe [color=#ffcc00]Game Over Statistics Screen[/color] tracks your session metrics.\n\nNow you know all commands:\n- Click node to select\n- Click adjacent targets to attack\n- Scroll to zoom\n- Use Alliance and Notifications to plan!\n\n[center][color=#666688]Demo complete. Returning to menu...[/color][/center]",
			"action": "conclusion",
			"delay": 8.0
		}
	]

func start_demo() -> void:
	demo_active = true
	current_step = 0
	visible = true
	_show_step(0)

func stop_demo() -> void:
	demo_active = false
	visible = false
	emit_signal("demo_completed")

func advance_step() -> void:
	current_step += 1
	step_timer = 0.0
	
	if current_step >= demo_steps.size():
		stop_demo()
		return
	
	_show_step(current_step)

func _show_step(index: int) -> void:
	if index >= demo_steps.size():
		return
	
	var step = demo_steps[index]
	
	title_label.text = step["title"]
	step_indicator.text = "Step %d / %d" % [index + 1, demo_steps.size()]
	
	# Start typing effect
	typing_text = step["text"]
	displayed_text = ""
	description_label.text = ""
	is_typing = true
	typing_timer = 0.0
	step_timer = 0.0
	
	# Set delay for this step
	auto_advance_delay = step.get("delay", 4.0)
	
	# Execute step action
	_execute_action(step["action"])
	
	emit_signal("step_changed", index)

func _execute_action(action: String) -> void:
	match action:
		"intro", "show_network":
			_clear_highlights()
		"camera_controls":
			_demo_camera_controls()
		"player_select":
			_demo_player_select()
		"show_targets":
			pass # Automatic highlighting from selection
		"player_attack":
			_demo_player_attack()
		"capture_node":
			_demo_capture()
		"enemy_attack":
			_demo_enemy_attack()
		"combat_defense":
			_demo_combat_defense()
		"show_alliance":
			_demo_alliance()
		"victory_condition":
			_demo_victory()
		"conclusion":
			_clear_highlights()

func _demo_camera_controls() -> void:
	var camera_node = get_tree().current_scene.get_node_or_null("CameraController")
	if camera_node:
		var tween = create_tween().set_parallel(true)
		# Zoom out slightly and pan
		tween.tween_property(camera_node, "zoom", Vector2(0.8, 0.8), 2.0).set_ease(Tween.EASE_OUT)
		tween.tween_property(camera_node, "position", Vector2(700, 400), 2.0).set_ease(Tween.EASE_IN_OUT)

func _demo_player_select() -> void:
	if not network_manager: return
	var player_servers = network_manager.get_servers_by_owner(ServerNode.Owner.PLAYER)
	if player_servers.size() > 0:
		var server = player_servers[0]
		if game_ui:
			game_ui.select_server(server)

func _demo_player_attack() -> void:
	if not network_manager or not combat_manager: return
	# Launch attack on first selected adjacent enemy
	if game_ui and game_ui.selected_server:
		var enemies = network_manager.get_adjacent_enemies(game_ui.selected_server)
		if enemies.size() > 0:
			combat_manager.player_attack(game_ui.selected_server, enemies[0])

func _demo_capture() -> void:
	if not network_manager or not combat_manager: return
	# Fast forward capture of current target
	for proj in combat_manager.active_attacks:
		if proj["from"].owner_type == ServerNode.Owner.PLAYER:
			proj["to"].firewall_strength = 5.0 # Almost zero

func _demo_enemy_attack() -> void:
	if not network_manager or not combat_manager: return
	var enemy_servers = network_manager.get_servers_by_owner(ServerNode.Owner.ENEMY)
	var player_servers = network_manager.get_servers_by_owner(ServerNode.Owner.PLAYER)
	if enemy_servers.size() > 0 and player_servers.size() > 0:
		var attacker = enemy_servers[0]
		var target = null
		# Find connected player server
		for p in player_servers:
			if attacker.is_connected_to(p):
				target = p
				break
		if target:
			combat_manager.start_attack(attacker, target)

func _demo_combat_defense() -> void:
	if not network_manager or not combat_manager: return
	# Counter attack
	for proj in combat_manager.active_attacks:
		if proj["from"].owner_type == ServerNode.Owner.ENEMY:
			var target = proj["to"]
			var attacker = proj["from"]
			if target.owner_type == ServerNode.Owner.PLAYER:
				game_ui.select_server(target)
				combat_manager.player_attack(target, attacker)
				break

func _demo_alliance() -> void:
	_highlight_alliance_panel()
	if alliance_manager and not alliance_manager.is_allied():
		alliance_manager.request_alliance()

func _demo_victory() -> void:
	if game_ui:
		# Force show game over victory logic
		var mock_stats = {
			"time_played": 124.0,
			"nodes_captured": 14,
			"nodes_lost": 2,
			"attacks_launched": 16,
			"alliances_formed": 1
		}
		game_ui.show_game_over(true, mock_stats)

func _highlight_alliance_panel() -> void:
	if highlight_rect and highlight_rect.has_method("set_highlight_area"):
		highlight_rect.set_highlight_area(Rect2(1000, 540, 280, 180))

func _clear_highlights() -> void:
	if highlight_rect and highlight_rect.has_method("clear_highlight"):
		highlight_rect.clear_highlight()

func _on_continue_pressed() -> void:
	if Audio:
		Audio.play_ui_click()
	is_typing = false
	displayed_text = typing_text
	description_label.text = typing_text
	advance_step()

func _on_skip_pressed() -> void:
	if Audio:
		Audio.play_ui_click()
	stop_demo()
	get_tree().change_scene_to_file("res://scenes/main_menu.tscn")
