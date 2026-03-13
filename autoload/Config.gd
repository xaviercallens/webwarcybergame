extends Node

var backend_url: String = ""

func _ready() -> void:
	backend_url = ProjectSettings.get_setting("moonlake/backend_url", "")
	
	if backend_url.is_empty():
		if OS.has_feature("web"):
			backend_url = JavaScriptBridge.eval("window.location.origin", true)
		else:
			backend_url = "http://localhost:8000"
	print("Backend URL: %s" % backend_url)

func api_url(path: String) -> String:
	if path.begins_with("/"):
		return backend_url + path
	return backend_url + "/" + path
