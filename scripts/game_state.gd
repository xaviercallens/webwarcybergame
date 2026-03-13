extends Node

# Global game state - passes data between scenes

var demo_mode: bool = false
var colorblind_mode: bool = false

# Settings
var master_volume: float = 1.0
var sfx_volume: float = 0.8
var music_volume: float = 0.5

const SETTINGS_PATH = "user://settings.cfg"

func _ready() -> void:
	load_settings()

func load_settings() -> void:
	var config = ConfigFile.new()
	var err = config.load(SETTINGS_PATH)
	if err == OK:
		master_volume = config.get_value("audio", "master", 1.0)
		sfx_volume = config.get_value("audio", "sfx", 0.8)
		music_volume = config.get_value("audio", "music", 0.5)
		colorblind_mode = config.get_value("accessibility", "colorblind", false)
		
		# Apply loaded audio settings if Audio is ready
		if get_node_or_null("/root/Audio"):
			_apply_audio_settings()

func save_settings() -> void:
	var config = ConfigFile.new()
	config.set_value("audio", "master", master_volume)
	config.set_value("audio", "sfx", sfx_volume)
	config.set_value("audio", "music", music_volume)
	config.set_value("accessibility", "colorblind", colorblind_mode)
	config.save(SETTINGS_PATH)

func _apply_audio_settings() -> void:
	var audio = get_node("/root/Audio")
	audio.set_master_volume(master_volume)
	audio.set_sfx_volume(sfx_volume)
	audio.set_music_volume(music_volume)
