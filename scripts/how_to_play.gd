extends Control
class_name HowToPlay

@onready var back_button: Button = $BackButton
@onready var prev_button: Button = $NavigationContainer/PrevButton
@onready var next_button: Button = $NavigationContainer/NextButton
@onready var page_label: Label = $NavigationContainer/PageLabel
@onready var content_container: VBoxContainer = $ContentPanel/MarginContainer/ContentContainer
@onready var title_label: Label = $ContentPanel/MarginContainer/ContentContainer/HeaderRow/TitleLabel
@onready var description_label: RichTextLabel = $ContentPanel/MarginContainer/ContentContainer/DescriptionLabel

var current_page: int = 0
var pages: Array[Dictionary] = []

func _ready() -> void:
	_setup_pages()
	
	back_button.pressed.connect(_on_back_pressed)
	prev_button.pressed.connect(_on_prev_pressed)
	next_button.pressed.connect(_on_next_pressed)
	
	_show_page(0)

func _setup_pages() -> void:
	pages = [
		{
			"title": " OBJECTIVE.exe",
			"content": """[center][color=#00ffdd]// SYSTEM BRIEFING //[/color][/center]

Your directive: [color=#00ff88]DOMINATE THE NETWORK[/color] by infiltrating and capturing hostile nodes.

[color=#ffcc00]>> PRIMARY OBJECTIVE:[/color]
Achieve [color=#00ff88]75%[/color] network control to establish dominance.

[color=#ff4444]>> FAILURE CONDITION:[/color]
Network compromised if all nodes lost or enemy reaches 75% control."""
		},
		{
			"title": " NETWORK_MAP.dat",
			"content": """[center][color=#00ffdd]// NODE CLASSIFICATION //[/color][/center]

[color=#00ff88]> GREEN NODES [FRIENDLY][/color]
Under your direct control. Deploy for offensive operations.

[color=#ff4444]> RED NODES [HOSTILE][/color]
Enemy AI faction. Priority targets for elimination.

[color=#4488ff]> BLUE NODES [POTENTIAL ALLY][/color]
Neutral faction. Diplomatic relations possible.

[color=#66aaaa]> CYAN NODES [UNCLAIMED][/color]
Unallocated resources. First-come, first-served."""
		},
		{
			"title": " COMBAT_PROTOCOL.sys",
			"content": """[center][color=#00ffdd]// ENGAGEMENT PROCEDURE //[/color][/center]

[color=#ffcc00]STEP 01:[/color] Select operational node
Click on a [color=#00ff88]controlled node[/color] to activate.

[color=#ffcc00]STEP 02:[/color] Initiate attack sequence
Execute [color=#ff8844][ INITIATE ATTACK ][/color] > select target.

[color=#ffcc00]STEP 03:[/color] Monitor engagement
Node will deploy continuous assault on target firewall.

[color=#ffcc00]STEP 04:[/color] Capture confirmation
Firewall breach at [color=#ff4444]0%[/color] = node captured.

[color=#666688]// Note: Inactive nodes regenerate firewall integrity.[/color]"""
		},
		{
			"title": " NODE_SPECS.doc",
			"content": """[center][color=#00ffdd]// TECHNICAL SPECIFICATIONS //[/color][/center]

[color=#ffcc00]> FIREWALL_INTEGRITY[/color]
Node defensive capacity. Breach occurs at 0%.

[color=#ffcc00]> ATTACK_OUTPUT[/color]
Offensive capability rating. Scales with firewall status.
Formula: PWR = base_power * (firewall / max_firewall)

[color=#ffcc00]> REGEN_RATE[/color]
Passive firewall recovery when not under siege.

[color=#666688]// Tactical note: Prioritize low-firewall targets.[/color]"""
		},
		{
			"title": " DIPLO_LINK.cfg",
			"content": """[center][color=#00ffdd]// ALLIANCE PROTOCOL //[/color][/center]

The [color=#4488ff]BLUE FACTION[/color] operates independently. Diplomatic channel available.

[color=#ffcc00]> ESTABLISH LINK[/color]
Execute [color=#ff8844][ REQUEST LINK ][/color] in DIPLO panel.

[color=#ffcc00]> ALLIANCE BENEFITS[/color]
- Allied AI engages hostile nodes
- Coordinated network defense
- Captured nodes transfer to you

[color=#ffcc00]> TRUST_COEFFICIENT[/color]
Actions modify diplomatic standing. Higher = better relations.

[color=#ff4444]// WARNING: Link termination causes severe trust damage.[/color]"""
		},
		{
			"title": " TACTICS.txt",
			"content": """[center][color=#00ffdd]// STRATEGIC RECOMMENDATIONS //[/color][/center]

[color=#00ff88]>[/color] Target [color=#ff4444]compromised nodes[/color] for rapid acquisition.

[color=#00ff88]>[/color] Coordinate [color=#ffcc00]multi-node assaults[/color] on priority targets.

[color=#00ff88]>[/color] Establish [color=#4488ff]alliance early[/color] for numerical superiority.

[color=#00ff88]>[/color] Fortify [color=#00ff88]perimeter nodes[/color] - primary attack vectors.

[color=#00ff88]>[/color] The [color=#ff8844]CENTRAL HUB[/color] offers significant tactical advantage.

[color=#00ff88]>[/color] Monitor HUD for real-time network status.

[center][color=#00ffdd]// END TRANSMISSION //[/color]
[color=#666688]Good luck, Operator.[/color][/center]"""
		}
	]

func _show_page(page_index: int) -> void:
	current_page = clamp(page_index, 0, pages.size() - 1)
	
	var page: Dictionary = pages[current_page]
	title_label.text = page["title"]
	description_label.text = page["content"]
	
	# Update navigation
	page_label.text = "[ %d / %d ]" % [current_page + 1, pages.size()]
	prev_button.disabled = current_page == 0
	next_button.disabled = current_page == pages.size() - 1

func _on_back_pressed() -> void:
	if Audio:
		Audio.play_ui_click()
	get_tree().change_scene_to_file("res://scenes/main_menu.tscn")

func _on_prev_pressed() -> void:
	if Audio:
		Audio.play_ui_click()
	_show_page(current_page - 1)

func _on_next_pressed() -> void:
	if Audio:
		Audio.play_ui_click()
	_show_page(current_page + 1)

func _input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_cancel"):
		_on_back_pressed()
	elif event.is_action_pressed("ui_left"):
		if not prev_button.disabled:
			_on_prev_pressed()
	elif event.is_action_pressed("ui_right"):
		if not next_button.disabled:
			_on_next_pressed()
