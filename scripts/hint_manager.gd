extends CanvasLayer
class_name HintManager

# Contextual hint system to teach mechanics without a tutorial barrage

signal hint_dismissed(hint_id: String)

const HINT_DELAY: float = 3.0
const HINT_DURATION: float = 6.0

enum HintType {
	SELECT_NODE,
	ATTACK_ENEMY,
	CAPTURE_NODE,
	UNDER_ATTACK,
	ALLIANCE
}

var shown_hints: Dictionary = {}
var active_hint_panel: PanelContainer
var hint_label: Label
var current_hint_type: HintType = -1
var hide_timer: SceneTreeTimer

# References needed to check state
var game_manager: Node
var network_manager: Node
var combat_manager: Node
var game_ui: Node

func _ready() -> void:
	layer = 15  # Above game UI, below pause menu
	
	# Create hint UI
	active_hint_panel = PanelContainer.new()
	active_hint_panel.set_anchors_preset(Control.PRESET_CENTER_BOTTOM)
	active_hint_panel.offset_left = -250
	active_hint_panel.offset_right = 250
	active_hint_panel.offset_top = -120
	active_hint_panel.offset_bottom = -70
	active_hint_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	
	var style = StyleBoxFlat.new()
	style.bg_color = Color(0.02, 0.1, 0.15, 0.85)
	style.border_color = Color(0, 0.8, 1.0, 0.6)
	style.set_border_width_all(2)
	style.set_corner_radius_all(8)
	style.content_margin_left = 20
	style.content_margin_right = 20
	style.content_margin_top = 10
	style.content_margin_bottom = 10
	active_hint_panel.add_theme_stylebox_override("panel", style)
	
	var hbox = HBoxContainer.new()
	hbox.add_theme_constant_override("separation", 15)
	active_hint_panel.add_child(hbox)
	
	var icon = Label.new()
	icon.text = "[?]"
	icon.add_theme_color_override("font_color", Color(0, 1.0, 0.8))
	icon.add_theme_font_size_override("font_size", 18)
	hbox.add_child(icon)
	
	hint_label = Label.new()
	hint_label.text = "Hint Text"
	hint_label.add_theme_color_override("font_color", Color(0.8, 0.9, 1.0))
	hint_label.add_theme_font_size_override("font_size", 14)
	hint_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	hint_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	hbox.add_child(hint_label)
	
	active_hint_panel.modulate.a = 0
	add_child(active_hint_panel)
	
	# Start initial hint timer
	get_tree().create_timer(4.0).timeout.connect(_check_initial_hint)

func setup(gm: Node, nm: Node, cm: Node, ui: Node) -> void:
	game_manager = gm
	network_manager = nm
	combat_manager = cm
	game_ui = ui
	
	# Connect to events to trigger hints or dismiss them
	if network_manager:
		network_manager.server_clicked.connect(_on_server_clicked)
	if combat_manager:
		combat_manager.attack_started.connect(_on_attack_started)
		combat_manager.server_captured.connect(_on_server_captured)

func show_hint(type: HintType, text: String, force: bool = false) -> void:
	if shown_hints.has(type) and not force:
		return
	
	shown_hints[type] = true
	current_hint_type = type
	hint_label.text = text
	
	if Audio:
		Audio.play_ui_select() # Gentle beep
	
	var tween = create_tween()
	tween.tween_property(active_hint_panel, "modulate:a", 1.0, 0.3)
	
	if hide_timer:
		hide_timer.disconnect("timeout", _hide_current_hint)
	hide_timer = get_tree().create_timer(HINT_DURATION)
	hide_timer.timeout.connect(_hide_current_hint)

func _hide_current_hint() -> void:
	if active_hint_panel.modulate.a > 0:
		var tween = create_tween()
		tween.tween_property(active_hint_panel, "modulate:a", 0.0, 0.3)
		hide_timer = null

func dismiss_hint(type: HintType) -> void:
	if current_hint_type == type and active_hint_panel.modulate.a > 0:
		_hide_current_hint()

# --- Hint Condition Checks ---

func _check_initial_hint() -> void:
	if game_manager and game_manager.game_over: return
	if game_ui and not game_ui.selected_server:
		show_hint(HintType.SELECT_NODE, "HINT: Click your GREEN node to select it and view its stats.")

func _on_server_clicked(server) -> void:
	if server.owner_type == 1: # Player
		dismiss_hint(HintType.SELECT_NODE)
		
		# Delay slightly so it doesn't pop up instantly
		get_tree().create_timer(1.0).timeout.connect(func():
			if game_ui and game_ui.selected_server == server:
				show_hint(HintType.ATTACK_ENEMY, "HINT: Click an adjacent RED node (highlighted) to launch a cyber attack!")
		)

func _on_attack_started(attacker, target) -> void:
	if attacker.owner_type == 1: # Player
		dismiss_hint(HintType.ATTACK_ENEMY)
		
	elif attacker.owner_type == 2 and target.owner_type == 1: # Enemy attacking Player
		show_hint(HintType.UNDER_ATTACK, "WARNING: Enemy is hacking your node! Click your node, then click the enemy to counter-attack!")

func _on_server_captured(server, new_owner) -> void:
	if new_owner == 1: # Player captured
		show_hint(HintType.CAPTURE_NODE, "HINT: Node Captured! Reach 75% Network Control (see progress bar above) to win the match.")
