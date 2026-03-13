extends CanvasLayer
class_name GameUI

signal attack_button_pressed
signal defend_button_pressed
signal alliance_button_pressed

@export var network_manager: NetworkManager
@export var combat_manager: CombatManager
@export var alliance_manager: AllianceManager

# UI References
@onready var hud_panel: PanelContainer = $HUDPanel
@onready var server_count_label: RichTextLabel = $HUDPanel/MarginContainer/VBoxContainer/TitleRow/ServerCountLabel
@onready var status_label: Label = $HUDPanel/MarginContainer/VBoxContainer/StatusLabel
@onready var victory_progress_bar: ProgressBar = $HUDPanel/MarginContainer/VBoxContainer/VictoryProgressBar

@onready var server_info_panel: PanelContainer = $ServerInfoPanel
@onready var server_name_label: Label = $ServerInfoPanel/MarginContainer/VBoxContainer/ServerNameLabel
@onready var server_owner_label: Label = $ServerInfoPanel/MarginContainer/VBoxContainer/OwnerLabel
@onready var firewall_bar: ProgressBar = $ServerInfoPanel/MarginContainer/VBoxContainer/FirewallBar
@onready var firewall_label: Label = $ServerInfoPanel/MarginContainer/VBoxContainer/FirewallLabel
@onready var power_label: Label = $ServerInfoPanel/MarginContainer/VBoxContainer/PowerLabel
@onready var firewall_header: Label = $ServerInfoPanel/MarginContainer/VBoxContainer/FirewallHeader
@onready var attack_button: Button = $ServerInfoPanel/MarginContainer/VBoxContainer/ButtonContainer/AttackButton
@onready var cancel_button: Button = $ServerInfoPanel/MarginContainer/VBoxContainer/ButtonContainer/CancelButton

@onready var alliance_panel: PanelContainer = $AlliancePanel
@onready var alliance_status_label: Label = $AlliancePanel/MarginContainer/VBoxContainer/AllianceStatusLabel
@onready var trust_bar: ProgressBar = $AlliancePanel/MarginContainer/VBoxContainer/TrustBar
@onready var trust_label: Label = $AlliancePanel/MarginContainer/VBoxContainer/TrustLabel
@onready var alliance_button: Button = $AlliancePanel/MarginContainer/VBoxContainer/AllianceButton

@onready var target_panel: PanelContainer = $TargetPanel
@onready var target_label: Label = $TargetPanel/MarginContainer/VBoxContainer/HeaderRow/TargetLabel
@onready var target_list: ItemList = $TargetPanel/MarginContainer/VBoxContainer/TargetList

@onready var game_over_panel: PanelContainer = $GameOverPanel
@onready var game_over_label: Label = $GameOverPanel/MarginContainer/VBoxContainer/GameOverLabel
@onready var restart_button: Button = $GameOverPanel/MarginContainer/VBoxContainer/RestartButton
@onready var cancel_target_button: Button = $TargetPanel/MarginContainer/VBoxContainer/CancelTargetButton
@onready var minimap: Minimap = $Minimap

var selected_server: ServerNode = null
var selecting_target: bool = false
var available_targets: Array[ServerNode] = []

func _ready() -> void:
	server_info_panel.visible = false
	target_panel.visible = false
	game_over_panel.visible = false
	
	# Setup minimap
	if minimap and network_manager:
		minimap.set_network_manager(network_manager)
	
	if attack_button:
		attack_button.pressed.connect(_on_attack_pressed)
	if cancel_button:
		cancel_button.pressed.connect(_on_cancel_pressed)
	if alliance_button:
		alliance_button.pressed.connect(_on_alliance_pressed)
	if restart_button:
		restart_button.pressed.connect(_on_restart_pressed)
	if target_list:
		target_list.item_selected.connect(_on_target_selected)
	if cancel_target_button:
		cancel_target_button.pressed.connect(_on_cancel_target_pressed)

func _process(_delta: float) -> void:
	update_hud()
	update_alliance_panel()
	
	if selected_server:
		update_server_info()

func update_hud() -> void:
	if not network_manager:
		return
	
	var counts = network_manager.count_servers_by_owner()
	var total = network_manager.servers.size()
	
	if server_count_label:
		var cb = GameState and GameState.colorblind_mode
		
		var p_color = "3380ff" if cb else "7fff7f" # Blue for player in CB, Green otherwise
		var e_color = "ff8000" if cb else "ff7f7f" # Orange for enemy in CB, Red otherwise
		var a_color = "e6cc33" if cb else "7f7fff" # Yellow for ally in CB, Blue otherwise
		
		server_count_label.text = "[color=#%s]Player: %d[/color] | [color=#%s]Enemy: %d[/color] | [color=#%s]Ally: %d[/color] | [color=#aaaaaa]Neutral: %d[/color]" % [
			p_color, counts[ServerNode.Owner.PLAYER],
			e_color, counts[ServerNode.Owner.ENEMY],
			a_color, counts[ServerNode.Owner.ALLY],
			counts[ServerNode.Owner.NEUTRAL]
		]
	
	if status_label:
		var player_pct = float(counts[ServerNode.Owner.PLAYER]) / total * 100 if total > 0 else 0
		var target_pct = 75.0
		status_label.text = "// Network Control: %.0f%% | Target: %.0f%% | Nodes: %d" % [player_pct, target_pct, total]
	
	if victory_progress_bar:
		var player_pct = float(counts[ServerNode.Owner.PLAYER]) / total * 100 if total > 0 else 0
		victory_progress_bar.value = player_pct
		# Color based on progress
		if player_pct >= 60:
			victory_progress_bar.modulate = Color(0.2, 1.0, 0.5)
		elif player_pct >= 30:
			victory_progress_bar.modulate = Color(0, 0.8, 0.9)
		else:
			victory_progress_bar.modulate = Color(1.0, 0.8, 0.2)

func update_server_info() -> void:
	if not selected_server:
		return
	
	if server_name_label:
		server_name_label.text = "> " + selected_server.server_name.to_upper()
	
	if server_owner_label:
		var owner_text = ""
		match selected_server.owner_type:
			ServerNode.Owner.PLAYER:
				owner_text = ":: STATUS: [CONTROLLED]"
				server_owner_label.modulate = Color(0.3, 1.0, 0.5)
			ServerNode.Owner.ENEMY:
				owner_text = ":: STATUS: [HOSTILE]"
				server_owner_label.modulate = Color(1.0, 0.3, 0.3)
			ServerNode.Owner.ALLY:
				owner_text = ":: STATUS: [ALLIED]"
				server_owner_label.modulate = Color(0.3, 0.5, 1.0)
			ServerNode.Owner.NEUTRAL:
				owner_text = ":: STATUS: [UNLINKED]"
				server_owner_label.modulate = Color(0.6, 0.6, 0.6)
		server_owner_label.text = owner_text
	
	if firewall_bar:
		firewall_bar.max_value = selected_server.max_firewall
		firewall_bar.value = selected_server.firewall_strength
		
		# Animate bar color based on health
		var health_ratio = selected_server.firewall_strength / selected_server.max_firewall
		if health_ratio > 0.6:
			firewall_bar.modulate = Color(0, 1.0, 0.8)
		elif health_ratio > 0.3:
			firewall_bar.modulate = Color(1.0, 0.8, 0)
		else:
			firewall_bar.modulate = Color(1.0, 0.2, 0.2)
	
	if firewall_label:
		firewall_label.text = "  Integrity: %.0f / %.0f units" % [selected_server.firewall_strength, selected_server.max_firewall]
	
	if power_label:
		power_label.text = "  Output: %.1f PWR" % selected_server.get_attack_power()
	
	# Update button states
	var is_player_owned = selected_server.owner_type == ServerNode.Owner.PLAYER
	
	if attack_button:
		attack_button.visible = is_player_owned
		
		if combat_manager and combat_manager.is_server_attacking(selected_server):
			attack_button.text = "[ ATTACKING... ]"
			attack_button.disabled = true
		else:
			attack_button.text = "[ INITIATE ATTACK ]"
			attack_button.disabled = false
	
	if cancel_button:
		cancel_button.visible = is_player_owned and combat_manager and combat_manager.is_server_attacking(selected_server)

func update_alliance_panel() -> void:
	if not alliance_manager:
		return
	
	if alliance_status_label:
		var status = alliance_manager.get_alliance_status_text()
		alliance_status_label.text = "> Link Status: " + status.to_upper()
		
		if alliance_manager.is_allied():
			alliance_status_label.modulate = Color(0.3, 1.0, 0.5)
		else:
			alliance_status_label.modulate = Color(0.6, 0.6, 0.6)
	
	if trust_bar:
		trust_bar.min_value = -100
		trust_bar.max_value = 100
		trust_bar.value = alliance_manager.get_ally_trust()
		
		# Color based on trust level
		var trust_val = alliance_manager.get_ally_trust()
		if trust_val > 50:
			trust_bar.modulate = Color(0, 1.0, 0.5)
		elif trust_val > 0:
			trust_bar.modulate = Color(0, 0.8, 1.0)
		elif trust_val > -50:
			trust_bar.modulate = Color(1.0, 0.8, 0)
		else:
			trust_bar.modulate = Color(1.0, 0.3, 0.3)
	
	if trust_label:
		trust_label.text = "  Coefficient: %.0f" % alliance_manager.get_ally_trust()
	
	if alliance_button:
		if alliance_manager.is_allied():
			alliance_button.text = "[ TERMINATE LINK ]"
		else:
			alliance_button.text = "[ REQUEST LINK ]"

func select_server(server: ServerNode) -> void:
	# Deselect previous
	if selected_server:
		selected_server.deselect()
		_clear_target_highlights()
	
	selected_server = server
	
	# Update minimap
	if minimap:
		minimap.set_selected_server(server)
	
	if server:
		server.select()
		server_info_panel.visible = true
		update_server_info()
		
		# Highlight available targets
		if server.owner_type == ServerNode.Owner.PLAYER:
			_highlight_available_targets(server)
			
		# Play select sound
		if Audio:
			Audio.play_ui_select()
	else:
		server_info_panel.visible = false

func _clear_target_highlights() -> void:
	if not network_manager: return
	for s in network_manager.servers:
		if s.has_method("set_target_highlight"):
			s.set_target_highlight(false)

func _highlight_available_targets(attacker: ServerNode) -> void:
	if not network_manager: return
	var targets = network_manager.get_adjacent_enemies(attacker)
	for t in targets:
		if t.has_method("set_target_highlight"):
			t.set_target_highlight(true)

func show_target_selection(attacker: ServerNode) -> void:
	if not network_manager:
		return
	
	selecting_target = true
	available_targets.clear()
	
	# Get valid targets (connected enemy servers)
	available_targets = network_manager.get_adjacent_enemies(attacker)
	
	if available_targets.size() == 0:
		target_label.text = " NO_TARGETS_FOUND"
		target_list.clear()
	else:
		target_label.text = " %s > TARGET" % attacker.server_name.to_upper()
		target_list.clear()
		for target in available_targets:
			target_list.add_item("> %s [FW:%.0f]" % [target.server_name, target.firewall_strength])
	
	target_panel.visible = true

func hide_target_selection() -> void:
	selecting_target = false
	target_panel.visible = false
	available_targets.clear()

func show_game_over(won: bool, stats: Dictionary = {}) -> void:
	game_over_panel.visible = true
	var cb = GameState and GameState.colorblind_mode
	
	if game_over_label:
		var text = ""
		if won:
			text = ">> VICTORY <<\n\nNETWORK DOMINANCE ACHIEVED\n"
			game_over_label.modulate = Color(0.2, 0.5, 1.0) if cb else Color(0.3, 1.0, 0.5)
		else:
			text = ">> SYSTEM FAILURE <<\n\nNETWORK COMPROMISED\n"
			game_over_label.modulate = Color(1.0, 0.5, 0.0) if cb else Color(1.0, 0.3, 0.3)
			
		if stats.size() > 0:
			text += "\n[ MATCH STATISTICS ]\n"
			var mins = int(stats.get("time_played", 0)) / 60
			var secs = int(stats.get("time_played", 0)) % 60
			text += "Time: %02d:%02d\n" % [mins, secs]
			text += "Nodes Captured: %d\n" % stats.get("nodes_captured", 0)
			text += "Nodes Lost: %d\n" % stats.get("nodes_lost", 0)
			text += "Attacks Launched: %d\n" % stats.get("attacks_launched", 0)
			text += "Alliances Formed: %d" % stats.get("alliances_formed", 0)
			
		game_over_label.text = text

func _on_attack_pressed() -> void:
	if Audio:
		Audio.play_ui_click()
	if selected_server and selected_server.owner_type == ServerNode.Owner.PLAYER:
		show_target_selection(selected_server)

func _on_cancel_pressed() -> void:
	if Audio:
		Audio.play_ui_click()
	if selected_server and combat_manager:
		combat_manager.player_cancel_attack(selected_server)

func _on_alliance_pressed() -> void:
	if Audio:
		Audio.play_ui_click()
	if alliance_manager:
		if alliance_manager.is_allied():
			alliance_manager.break_alliance()
			if Audio:
				Audio.play_alliance_broken()
		else:
			alliance_manager.request_alliance()

func _on_target_selected(index: int) -> void:
	if Audio:
		Audio.play_ui_click()
	if index < available_targets.size() and combat_manager and selected_server:
		var target = available_targets[index]
		combat_manager.player_attack(selected_server, target)
		hide_target_selection()

func _on_cancel_target_pressed() -> void:
	if Audio:
		Audio.play_ui_click()
	hide_target_selection()

func _on_restart_pressed() -> void:
	if Audio:
		Audio.play_ui_click()
	get_tree().reload_current_scene()
