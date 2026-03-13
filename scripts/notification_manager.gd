extends CanvasLayer
class_name NotificationManager

# Toast notification system for in-game events
# Displays cyberpunk-styled messages that fade in/out

signal notification_dismissed

const MAX_VISIBLE: int = 4
const DISPLAY_DURATION: float = 3.5
const FADE_DURATION: float = 0.4
const NOTIFICATION_HEIGHT: float = 50.0
const NOTIFICATION_GAP: float = 8.0

enum NotificationType {
	INFO,
	SUCCESS,
	WARNING,
	DANGER
}

var notification_container: VBoxContainer
var active_notifications: Array = []

func _ready() -> void:
	layer = 10  # Above other UI
	
	# Create container anchored at top-center
	var margin = MarginContainer.new()
	margin.set_anchors_preset(Control.PRESET_TOP_WIDE)
	margin.add_theme_constant_override("margin_top", 20)
	margin.add_theme_constant_override("margin_left", 200)
	margin.add_theme_constant_override("margin_right", 200)
	margin.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(margin)
	
	notification_container = VBoxContainer.new()
	notification_container.add_theme_constant_override("separation", int(NOTIFICATION_GAP))
	notification_container.mouse_filter = Control.MOUSE_FILTER_IGNORE
	margin.add_child(notification_container)

func notify(message: String, type: NotificationType = NotificationType.INFO) -> void:
	var toast = _create_toast(message, type)
	notification_container.add_child(toast)
	active_notifications.append(toast)
	
	# Limit visible notifications
	while active_notifications.size() > MAX_VISIBLE:
		var oldest = active_notifications.pop_front()
		if is_instance_valid(oldest):
			_dismiss_toast(oldest)
	
	# Fade in
	toast.modulate.a = 0.0
	var tween = create_tween()
	tween.tween_property(toast, "modulate:a", 1.0, FADE_DURATION)
	
	# Auto-dismiss after duration
	await get_tree().create_timer(DISPLAY_DURATION).timeout
	if is_instance_valid(toast):
		_dismiss_toast(toast)

func _dismiss_toast(toast: PanelContainer) -> void:
	if not is_instance_valid(toast):
		return
	if toast in active_notifications:
		active_notifications.erase(toast)
	
	var tween = create_tween()
	tween.tween_property(toast, "modulate:a", 0.0, FADE_DURATION)
	tween.tween_callback(toast.queue_free)

func _create_toast(message: String, type: NotificationType) -> PanelContainer:
	var panel = PanelContainer.new()
	panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	panel.custom_minimum_size = Vector2(0, NOTIFICATION_HEIGHT)
	
	# Style
	var style = StyleBoxFlat.new()
	style.bg_color = _get_bg_color(type)
	style.border_color = _get_border_color(type)
	style.set_border_width_all(2)
	style.set_corner_radius_all(4)
	style.content_margin_left = 16
	style.content_margin_right = 16
	style.content_margin_top = 8
	style.content_margin_bottom = 8
	style.shadow_color = Color(_get_border_color(type), 0.3)
	style.shadow_size = 6
	panel.add_theme_stylebox_override("panel", style)
	
	# Icon + message
	var hbox = HBoxContainer.new()
	hbox.mouse_filter = Control.MOUSE_FILTER_IGNORE
	hbox.add_theme_constant_override("separation", 12)
	panel.add_child(hbox)
	
	var icon_label = Label.new()
	icon_label.text = _get_icon(type)
	icon_label.add_theme_color_override("font_color", _get_border_color(type))
	icon_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	hbox.add_child(icon_label)
	
	var msg_label = Label.new()
	msg_label.text = message
	msg_label.add_theme_color_override("font_color", _get_text_color(type))
	msg_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	msg_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	hbox.add_child(msg_label)
	
	# Timestamp
	var time_label = Label.new()
	var time_dict = Time.get_time_dict_from_system()
	time_label.text = "[%02d:%02d]" % [time_dict["hour"], time_dict["minute"]]
	time_label.add_theme_color_override("font_color", Color(0.4, 0.6, 0.7, 0.6))
	time_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	hbox.add_child(time_label)
	
	return panel

func _get_bg_color(type: NotificationType) -> Color:
	match type:
		NotificationType.SUCCESS:
			return Color(0.02, 0.08, 0.04, 0.92)
		NotificationType.WARNING:
			return Color(0.08, 0.06, 0.02, 0.92)
		NotificationType.DANGER:
			return Color(0.08, 0.02, 0.02, 0.92)
		_:
			return Color(0.02, 0.05, 0.08, 0.92)

func _get_border_color(type: NotificationType) -> Color:
	var cb = GameState and GameState.colorblind_mode
	match type:
		NotificationType.SUCCESS:
			return Color(0.2, 0.5, 1.0, 0.8) if cb else Color(0.2, 1.0, 0.5, 0.8)
		NotificationType.WARNING:
			return Color(1.0, 0.8, 0.2, 0.8)
		NotificationType.DANGER:
			return Color(1.0, 0.5, 0.0, 0.8) if cb else Color(1.0, 0.3, 0.3, 0.8)
		_:
			return Color(0.0, 0.8, 0.9, 0.8)

func _get_text_color(type: NotificationType) -> Color:
	var cb = GameState and GameState.colorblind_mode
	match type:
		NotificationType.SUCCESS:
			return Color(0.4, 0.7, 1.0) if cb else Color(0.3, 1.0, 0.6)
		NotificationType.WARNING:
			return Color(1.0, 0.9, 0.4)
		NotificationType.DANGER:
			return Color(1.0, 0.7, 0.2) if cb else Color(1.0, 0.5, 0.5)
		_:
			return Color(0.6, 0.9, 1.0)

func _get_icon(type: NotificationType) -> String:
	match type:
		NotificationType.SUCCESS:
			return "[+]"
		NotificationType.WARNING:
			return "[!]"
		NotificationType.DANGER:
			return "[X]"
		_:
			return "[>]"

# Convenience methods for common notifications
func notify_server_captured(server_name: String) -> void:
	notify("SERVER CAPTURED: %s — Control secured" % server_name.to_upper(), NotificationType.SUCCESS)

func notify_server_lost(server_name: String) -> void:
	notify("NODE COMPROMISED: %s — Firewall breached" % server_name.to_upper(), NotificationType.DANGER)

func notify_alliance_formed() -> void:
	notify("ALLIANCE LINK ESTABLISHED — Blue faction synchronized", NotificationType.SUCCESS)

func notify_alliance_broken() -> void:
	notify("ALLIANCE SEVERED — Link terminated", NotificationType.WARNING)

func notify_under_attack(server_name: String) -> void:
	notify("INTRUSION DETECTED: %s — Hostile activity" % server_name.to_upper(), NotificationType.DANGER)

func notify_attack_launched(target_name: String) -> void:
	notify("ATTACK INITIATED: %s — Payload deployed" % target_name.to_upper(), NotificationType.INFO)
