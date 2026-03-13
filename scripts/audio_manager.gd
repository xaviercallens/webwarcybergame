extends Node
class_name AudioManager

# Audio buses
const MASTER_BUS := "Master"
const SFX_BUS := "SFX"
const MUSIC_BUS := "Music"

# Sound effect players (pooled)
var sfx_players: Array[AudioStreamPlayer] = []
var sfx_pool_size: int = 16

# Music player
@onready var music_player: AudioStreamPlayer = $MusicPlayer
@onready var ambient_player: AudioStreamPlayer = $AmbientPlayer

# Volume settings
var master_volume: float = 1.0
var sfx_volume: float = 0.8
var music_volume: float = 0.5

# Preloaded sounds (generated procedurally)
var sounds: Dictionary = {}

func _ready() -> void:
	# Create SFX player pool
	for i in range(sfx_pool_size):
		var player: AudioStreamPlayer = AudioStreamPlayer.new()
		player.bus = SFX_BUS
		add_child(player)
		sfx_players.append(player)
	
	# Generate all procedural sounds
	_generate_sounds()
	
	# Start ambient background
	call_deferred("_start_ambient")

func _generate_sounds() -> void:
	sounds["attack_launch"] = _create_laser_sound(0.3, 800.0, 400.0)
	sounds["attack_hit"] = _create_impact_sound(0.2, 200.0)
	sounds["shield_up"] = _create_shield_sound(0.4, true)
	sounds["shield_hit"] = _create_shield_sound(0.2, false)
	sounds["server_captured"] = _create_capture_sound(0.6)
	sounds["server_lost"] = _create_alarm_sound(0.5)
	sounds["ui_click"] = _create_click_sound(0.1)
	sounds["ui_hover"] = _create_hover_sound(0.05)
	sounds["ui_select"] = _create_select_sound(0.15)
	sounds["alliance_formed"] = _create_success_sound(0.5)
	sounds["alliance_broken"] = _create_warning_sound(0.4)
	sounds["victory"] = _create_victory_sound(1.5)
	sounds["defeat"] = _create_defeat_sound(1.5)

func _create_laser_sound(duration: float, start_freq: float, end_freq: float) -> AudioStreamWAV:
	var sample_rate: int = 44100
	var samples: int = int(duration * sample_rate)
	var data: PackedByteArray = PackedByteArray()
	data.resize(samples * 2)
	
	for i in range(samples):
		var t: float = float(i) / sample_rate
		var progress: float = float(i) / samples
		var freq: float = lerp(start_freq, end_freq, progress)
		var envelope: float = (1.0 - progress) * sin(progress * PI)
		var sample_val: float = sin(t * freq * TAU) * envelope
		sample_val += (randf() - 0.5) * 0.1 * envelope
		var value: int = int(clamp(sample_val * 32767, -32768, 32767))
		data[i * 2] = value & 0xFF
		data[i * 2 + 1] = (value >> 8) & 0xFF
	
	var stream: AudioStreamWAV = AudioStreamWAV.new()
	stream.format = AudioStreamWAV.FORMAT_16_BITS
	stream.mix_rate = sample_rate
	stream.data = data
	return stream

func _create_impact_sound(duration: float, base_freq: float) -> AudioStreamWAV:
	var sample_rate: int = 44100
	var samples: int = int(duration * sample_rate)
	var data: PackedByteArray = PackedByteArray()
	data.resize(samples * 2)
	
	for i in range(samples):
		var t: float = float(i) / sample_rate
		var progress: float = float(i) / samples
		var envelope: float = exp(-progress * 8)
		var sample_val: float = sin(t * base_freq * TAU) * envelope
		sample_val += sin(t * base_freq * 0.5 * TAU) * envelope * 0.5
		sample_val += (randf() - 0.5) * envelope * 0.3
		var value: int = int(clamp(sample_val * 32767, -32768, 32767))
		data[i * 2] = value & 0xFF
		data[i * 2 + 1] = (value >> 8) & 0xFF
	
	var stream: AudioStreamWAV = AudioStreamWAV.new()
	stream.format = AudioStreamWAV.FORMAT_16_BITS
	stream.mix_rate = sample_rate
	stream.data = data
	return stream

func _create_shield_sound(duration: float, rising: bool) -> AudioStreamWAV:
	var sample_rate: int = 44100
	var samples: int = int(duration * sample_rate)
	var data: PackedByteArray = PackedByteArray()
	data.resize(samples * 2)
	
	for i in range(samples):
		var t: float = float(i) / sample_rate
		var progress: float = float(i) / samples
		var freq: float = 0.0
		if rising:
			freq = lerp(300.0, 600.0, progress)
		else:
			freq = lerp(600.0, 300.0, progress)
		var envelope: float = sin(progress * PI)
		var sample_val: float = sin(t * freq * TAU) * envelope * 0.5
		sample_val += sin(t * freq * 1.5 * TAU) * envelope * 0.25
		var value: int = int(clamp(sample_val * 32767, -32768, 32767))
		data[i * 2] = value & 0xFF
		data[i * 2 + 1] = (value >> 8) & 0xFF
	
	var stream: AudioStreamWAV = AudioStreamWAV.new()
	stream.format = AudioStreamWAV.FORMAT_16_BITS
	stream.mix_rate = sample_rate
	stream.data = data
	return stream

func _create_capture_sound(duration: float) -> AudioStreamWAV:
	var sample_rate: int = 44100
	var samples: int = int(duration * sample_rate)
	var data: PackedByteArray = PackedByteArray()
	data.resize(samples * 2)
	
	var notes: Array[float] = [400.0, 500.0, 600.0, 800.0]
	for i in range(samples):
		var t: float = float(i) / sample_rate
		var progress: float = float(i) / samples
		var note_idx: int = int(progress * notes.size()) % notes.size()
		var freq: float = notes[note_idx]
		var note_progress: float = fmod(progress * notes.size(), 1.0)
		var envelope: float = sin(note_progress * PI)
		var sample_val: float = sin(t * freq * TAU) * envelope * 0.4
		var value: int = int(clamp(sample_val * 32767, -32768, 32767))
		data[i * 2] = value & 0xFF
		data[i * 2 + 1] = (value >> 8) & 0xFF
	
	var stream: AudioStreamWAV = AudioStreamWAV.new()
	stream.format = AudioStreamWAV.FORMAT_16_BITS
	stream.mix_rate = sample_rate
	stream.data = data
	return stream

func _create_alarm_sound(duration: float) -> AudioStreamWAV:
	var sample_rate: int = 44100
	var samples: int = int(duration * sample_rate)
	var data: PackedByteArray = PackedByteArray()
	data.resize(samples * 2)
	
	for i in range(samples):
		var t: float = float(i) / sample_rate
		var progress: float = float(i) / samples
		var freq: float = 600.0 if fmod(t * 4, 1.0) < 0.5 else 400.0
		var envelope: float = 1.0 - progress * 0.5
		var sample_val: float = sin(t * freq * TAU) * envelope * 0.5
		var value: int = int(clamp(sample_val * 32767, -32768, 32767))
		data[i * 2] = value & 0xFF
		data[i * 2 + 1] = (value >> 8) & 0xFF
	
	var stream: AudioStreamWAV = AudioStreamWAV.new()
	stream.format = AudioStreamWAV.FORMAT_16_BITS
	stream.mix_rate = sample_rate
	stream.data = data
	return stream

func _create_click_sound(duration: float) -> AudioStreamWAV:
	var sample_rate: int = 44100
	var samples: int = int(duration * sample_rate)
	var data: PackedByteArray = PackedByteArray()
	data.resize(samples * 2)
	
	for i in range(samples):
		var t: float = float(i) / sample_rate
		var progress: float = float(i) / samples
		var envelope: float = exp(-progress * 30)
		var sample_val: float = sin(t * 1000 * TAU) * envelope
		var value: int = int(clamp(sample_val * 32767, -32768, 32767))
		data[i * 2] = value & 0xFF
		data[i * 2 + 1] = (value >> 8) & 0xFF
	
	var stream: AudioStreamWAV = AudioStreamWAV.new()
	stream.format = AudioStreamWAV.FORMAT_16_BITS
	stream.mix_rate = sample_rate
	stream.data = data
	return stream

func _create_hover_sound(duration: float) -> AudioStreamWAV:
	var sample_rate: int = 44100
	var samples: int = int(duration * sample_rate)
	var data: PackedByteArray = PackedByteArray()
	data.resize(samples * 2)
	
	for i in range(samples):
		var t: float = float(i) / sample_rate
		var progress: float = float(i) / samples
		var envelope: float = sin(progress * PI)
		var sample_val: float = sin(t * 2000 * TAU) * envelope * 0.3
		var value: int = int(clamp(sample_val * 32767, -32768, 32767))
		data[i * 2] = value & 0xFF
		data[i * 2 + 1] = (value >> 8) & 0xFF
	
	var stream: AudioStreamWAV = AudioStreamWAV.new()
	stream.format = AudioStreamWAV.FORMAT_16_BITS
	stream.mix_rate = sample_rate
	stream.data = data
	return stream

func _create_select_sound(duration: float) -> AudioStreamWAV:
	var sample_rate: int = 44100
	var samples: int = int(duration * sample_rate)
	var data: PackedByteArray = PackedByteArray()
	data.resize(samples * 2)
	
	for i in range(samples):
		var t: float = float(i) / sample_rate
		var progress: float = float(i) / samples
		var freq: float = lerp(800.0, 1200.0, progress)
		var envelope: float = sin(progress * PI)
		var sample_val: float = sin(t * freq * TAU) * envelope * 0.4
		var value: int = int(clamp(sample_val * 32767, -32768, 32767))
		data[i * 2] = value & 0xFF
		data[i * 2 + 1] = (value >> 8) & 0xFF
	
	var stream: AudioStreamWAV = AudioStreamWAV.new()
	stream.format = AudioStreamWAV.FORMAT_16_BITS
	stream.mix_rate = sample_rate
	stream.data = data
	return stream

func _create_success_sound(duration: float) -> AudioStreamWAV:
	var sample_rate: int = 44100
	var samples: int = int(duration * sample_rate)
	var data: PackedByteArray = PackedByteArray()
	data.resize(samples * 2)
	
	var notes: Array[float] = [523.25, 659.25, 783.99, 1046.50]
	for i in range(samples):
		var t: float = float(i) / sample_rate
		var progress: float = float(i) / samples
		var note_idx: int = int(progress * notes.size()) % notes.size()
		var freq: float = notes[note_idx]
		var note_progress: float = fmod(progress * notes.size(), 1.0)
		var envelope: float = sin(note_progress * PI) * (1.0 - progress * 0.3)
		var sample_val: float = sin(t * freq * TAU) * envelope * 0.4
		sample_val += sin(t * freq * 2 * TAU) * envelope * 0.1
		var value: int = int(clamp(sample_val * 32767, -32768, 32767))
		data[i * 2] = value & 0xFF
		data[i * 2 + 1] = (value >> 8) & 0xFF
	
	var stream: AudioStreamWAV = AudioStreamWAV.new()
	stream.format = AudioStreamWAV.FORMAT_16_BITS
	stream.mix_rate = sample_rate
	stream.data = data
	return stream

func _create_warning_sound(duration: float) -> AudioStreamWAV:
	var sample_rate: int = 44100
	var samples: int = int(duration * sample_rate)
	var data: PackedByteArray = PackedByteArray()
	data.resize(samples * 2)
	
	for i in range(samples):
		var t: float = float(i) / sample_rate
		var progress: float = float(i) / samples
		var freq: float = 300.0 + sin(t * 10) * 50
		var envelope: float = (1.0 - progress)
		var sample_val: float = sin(t * freq * TAU) * envelope * 0.5
		var value: int = int(clamp(sample_val * 32767, -32768, 32767))
		data[i * 2] = value & 0xFF
		data[i * 2 + 1] = (value >> 8) & 0xFF
	
	var stream: AudioStreamWAV = AudioStreamWAV.new()
	stream.format = AudioStreamWAV.FORMAT_16_BITS
	stream.mix_rate = sample_rate
	stream.data = data
	return stream

func _create_victory_sound(duration: float) -> AudioStreamWAV:
	var sample_rate: int = 44100
	var samples: int = int(duration * sample_rate)
	var data: PackedByteArray = PackedByteArray()
	data.resize(samples * 2)
	
	var notes: Array[float] = [523.25, 659.25, 783.99, 659.25, 783.99, 1046.50]
	for i in range(samples):
		var t: float = float(i) / sample_rate
		var progress: float = float(i) / samples
		var note_idx: int = int(progress * notes.size()) % notes.size()
		var freq: float = notes[note_idx]
		var note_progress: float = fmod(progress * notes.size(), 1.0)
		var envelope: float = sin(note_progress * PI) * (1.0 - progress * 0.2)
		var sample_val: float = sin(t * freq * TAU) * envelope * 0.35
		sample_val += sin(t * freq * 0.5 * TAU) * envelope * 0.15
		sample_val += sin(t * freq * 2 * TAU) * envelope * 0.1
		var value: int = int(clamp(sample_val * 32767, -32768, 32767))
		data[i * 2] = value & 0xFF
		data[i * 2 + 1] = (value >> 8) & 0xFF
	
	var stream: AudioStreamWAV = AudioStreamWAV.new()
	stream.format = AudioStreamWAV.FORMAT_16_BITS
	stream.mix_rate = sample_rate
	stream.data = data
	return stream

func _create_defeat_sound(duration: float) -> AudioStreamWAV:
	var sample_rate: int = 44100
	var samples: int = int(duration * sample_rate)
	var data: PackedByteArray = PackedByteArray()
	data.resize(samples * 2)
	
	var notes: Array[float] = [493.88, 440.0, 392.0, 349.23, 293.66]
	for i in range(samples):
		var t: float = float(i) / sample_rate
		var progress: float = float(i) / samples
		var note_idx: int = int(progress * notes.size()) % notes.size()
		var freq: float = notes[note_idx]
		var note_progress: float = fmod(progress * notes.size(), 1.0)
		var envelope: float = sin(note_progress * PI) * (1.0 - progress * 0.3)
		var sample_val: float = sin(t * freq * TAU) * envelope * 0.4
		var value: int = int(clamp(sample_val * 32767, -32768, 32767))
		data[i * 2] = value & 0xFF
		data[i * 2 + 1] = (value >> 8) & 0xFF
	
	var stream: AudioStreamWAV = AudioStreamWAV.new()
	stream.format = AudioStreamWAV.FORMAT_16_BITS
	stream.mix_rate = sample_rate
	stream.data = data
	return stream

func _create_ambient_music() -> AudioStreamWAV:
	var sample_rate: int = 44100
	var duration: float = 30.0
	var samples: int = int(duration * sample_rate)
	var data: PackedByteArray = PackedByteArray()
	data.resize(samples * 2)
	
	for i in range(samples):
		var t: float = float(i) / sample_rate
		var sample_val: float = 0.0
		
		# Base drone
		sample_val += sin(t * 55 * TAU) * 0.15
		sample_val += sin(t * 82.5 * TAU) * 0.1
		
		# Slow modulation
		var mod: float = sin(t * 0.1 * TAU)
		sample_val += sin(t * (110 + mod * 5) * TAU) * 0.08
		
		# High frequency shimmer
		var shimmer: float = sin(t * 0.05 * TAU) * 0.5 + 0.5
		sample_val += sin(t * 880 * TAU) * 0.02 * shimmer
		sample_val += sin(t * 1320 * TAU) * 0.01 * shimmer
		
		# Occasional pulse
		if fmod(t, 4.0) < 0.1:
			sample_val += sin(t * 220 * TAU) * exp(-fmod(t, 4.0) * 20) * 0.1
		
		# Digital artifacts
		if fmod(t, 8.0) < 0.05:
			sample_val += (randf() - 0.5) * 0.1
		
		var value: int = int(clamp(sample_val * 32767, -32768, 32767))
		data[i * 2] = value & 0xFF
		data[i * 2 + 1] = (value >> 8) & 0xFF
	
	var stream: AudioStreamWAV = AudioStreamWAV.new()
	stream.format = AudioStreamWAV.FORMAT_16_BITS
	stream.mix_rate = sample_rate
	stream.loop_mode = AudioStreamWAV.LOOP_FORWARD
	stream.loop_end = samples
	stream.data = data
	return stream

func _start_ambient() -> void:
	if ambient_player:
		ambient_player.stream = _create_ambient_music()
		ambient_player.volume_db = linear_to_db(music_volume * 0.6)
		ambient_player.play()

# Public API
func play_sound(sound_name: String, volume_scale: float = 1.0) -> void:
	if sound_name not in sounds:
		return
	
	var player: AudioStreamPlayer = _get_available_player()
	if player:
		player.stream = sounds[sound_name]
		player.volume_db = linear_to_db(sfx_volume * volume_scale)
		player.play()

func play_attack_launch() -> void:
	play_sound("attack_launch")

func play_attack_hit() -> void:
	play_sound("attack_hit", 0.5)

func play_server_captured(by_player: bool) -> void:
	if by_player:
		play_sound("server_captured")
	else:
		play_sound("server_lost")

func play_ui_click() -> void:
	play_sound("ui_click", 0.6)

func play_ui_select() -> void:
	play_sound("ui_select", 0.7)

func play_alliance_formed() -> void:
	play_sound("alliance_formed")

func play_alliance_broken() -> void:
	play_sound("alliance_broken")

func play_victory() -> void:
	play_sound("victory")

func play_defeat() -> void:
	play_sound("defeat")

func play_shield_hit() -> void:
	play_sound("shield_hit", 0.4)

func _get_available_player() -> AudioStreamPlayer:
	for player in sfx_players:
		if not player.playing:
			return player
	return sfx_players[0]

func set_master_volume(volume: float) -> void:
	master_volume = clamp(volume, 0.0, 1.0)
	AudioServer.set_bus_volume_db(AudioServer.get_bus_index(MASTER_BUS), linear_to_db(master_volume))

func set_sfx_volume(volume: float) -> void:
	sfx_volume = clamp(volume, 0.0, 1.0)

func set_music_volume(volume: float) -> void:
	music_volume = clamp(volume, 0.0, 1.0)
	if music_player:
		music_player.volume_db = linear_to_db(music_volume)
	if ambient_player:
		ambient_player.volume_db = linear_to_db(music_volume * 0.6)
