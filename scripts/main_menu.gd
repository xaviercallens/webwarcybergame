extends Control
class_name MainMenu

@onready var play_button: Button = $VBoxContainer/ButtonsContainer/PlayButton
@onready var how_to_play_button: Button = $VBoxContainer/ButtonsContainer/HowToPlayButton
@onready var demo_button: Button = $VBoxContainer/ButtonsContainer/DemoButton
@onready var settings_button: Button = $VBoxContainer/ButtonsContainer/SettingsButton
@onready var quit_button: Button = $VBoxContainer/ButtonsContainer/QuitButton

@onready var settings_panel: PanelContainer = $SettingsPanel
@onready var master_slider: HSlider = $SettingsPanel/MarginContainer/VBoxContainer/MasterVolume/MasterSlider
@onready var sfx_slider: HSlider = $SettingsPanel/MarginContainer/VBoxContainer/SFXVolume/SFXSlider
@onready var music_slider: HSlider = $SettingsPanel/MarginContainer/VBoxContainer/MusicVolume/MusicSlider
@onready var back_button: Button = $SettingsPanel/MarginContainer/VBoxContainer/BackButton

@onready var title_label: Label = $VBoxContainer/TitleContainer/TitleLabel
@onready var subtitle_label: Label = $VBoxContainer/TitleContainer/SubtitleLabel

var title_pulse_time: float = 0.0

var colorblind_toggle: CheckButton

func _ready() -> void:
	settings_panel.visible = false
	
	# Dynamically add colorblind toggle to settings
	var vbox = $SettingsPanel/MarginContainer/VBoxContainer
	var cb_container = HBoxContainer.new()
	var cb_label = Label.new()
	cb_label.text = "Colorblind Mode"
	cb_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	cb_container.add_child(cb_label)
	colorblind_toggle = CheckButton.new()
	cb_container.add_child(colorblind_toggle)
	# Insert before the back button
	vbox.add_child(cb_container)
	vbox.move_child(cb_container, vbox.get_child_count() - 2)
	
	colorblind_toggle.toggled.connect(_on_colorblind_toggled)
	
	# Connect button signals
	play_button.pressed.connect(_on_play_pressed)
	how_to_play_button.pressed.connect(_on_how_to_play_pressed)
	demo_button.pressed.connect(_on_demo_pressed)
	settings_button.pressed.connect(_on_settings_pressed)
	quit_button.pressed.connect(_on_quit_pressed)
	back_button.pressed.connect(_on_back_pressed)
	
	# Connect slider signals
	master_slider.value_changed.connect(_on_master_volume_changed)
	sfx_slider.value_changed.connect(_on_sfx_volume_changed)
	music_slider.value_changed.connect(_on_music_volume_changed)
	
	# Initialize slider values from GameState
	if GameState:
		master_slider.value = GameState.master_volume * 100
		sfx_slider.value = GameState.sfx_volume * 100
		music_slider.value = GameState.music_volume * 100
		colorblind_toggle.button_pressed = GameState.colorblind_mode
	else:
		master_slider.value = 100
		sfx_slider.value = 80
		music_slider.value = 50
	
	# Focus play button
	play_button.grab_focus()

func _process(delta: float) -> void:
	# Animate title with pulsing glow effect
	title_pulse_time += delta
	var pulse: float = (sin(title_pulse_time * 2.0) + 1.0) / 2.0
	var glow_color: Color = Color(0.0, 1.0, 0.8).lerp(Color(0.0, 0.6, 1.0), pulse)
	title_label.add_theme_color_override("font_color", glow_color)

func _on_play_pressed() -> void:
	if Audio:
		Audio.play_ui_click()
	
	# Transition to game
	get_tree().change_scene_to_file("res://main.tscn")

func _on_how_to_play_pressed() -> void:
	if Audio:
		Audio.play_ui_click()
	
	# Transition to how to play screen
	get_tree().change_scene_to_file("res://scenes/how_to_play.tscn")

func _on_demo_pressed() -> void:
	if Audio:
		Audio.play_ui_click()
	
	# Set demo mode flag and go to game
	if GameState:
		GameState.demo_mode = true
	get_tree().change_scene_to_file("res://scenes/game.tscn")

func _on_settings_pressed() -> void:
	if Audio:
		Audio.play_ui_click()
	
	settings_panel.visible = true
	back_button.grab_focus()

func _on_quit_pressed() -> void:
	if Audio:
		Audio.play_ui_click()
	
	# Small delay for sound to play
	await get_tree().create_timer(0.1).timeout
	get_tree().quit()

func _on_back_pressed() -> void:
	if Audio:
		Audio.play_ui_click()
	
	settings_panel.visible = false
	settings_button.grab_focus()

func _on_master_volume_changed(value: float) -> void:
	var vol = value / 100.0
	if Audio:
		Audio.set_master_volume(vol)
	if GameState:
		GameState.master_volume = vol
		GameState.save_settings()

func _on_sfx_volume_changed(value: float) -> void:
	var vol = value / 100.0
	if Audio:
		Audio.set_sfx_volume(vol)
		Audio.play_ui_click()  # Preview sound
	if GameState:
		GameState.sfx_volume = vol
		GameState.save_settings()

func _on_music_volume_changed(value: float) -> void:
	var vol = value / 100.0
	if Audio:
		Audio.set_music_volume(vol)
	if GameState:
		GameState.music_volume = vol
		GameState.save_settings()

func _on_colorblind_toggled(button_pressed: bool) -> void:
	if Audio:
		Audio.play_ui_click()
	if GameState:
		GameState.colorblind_mode = button_pressed
		GameState.save_settings()

func _input(event: InputEvent) -> void:
	if event.is_action_pressed("ui_cancel"):
		if settings_panel.visible:
			_on_back_pressed()
