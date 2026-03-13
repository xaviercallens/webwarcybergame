extends Node2D
class_name AttackEffectsManager

# Attack effects manager using GPUParticles2D for visual effects
# Handles attack projectiles, impact explosions, and capture effects

@export var projectile_color_player: Color = Color(0.3, 1.0, 0.3)
@export var projectile_color_enemy: Color = Color(1.0, 0.3, 0.3)
@export var projectile_color_ally: Color = Color(0.3, 0.5, 1.0)

# Active projectile effects
var active_projectiles: Array[Dictionary] = []

# Pool of reusable particle systems
var impact_pool: Array[GPUParticles2D] = []
var capture_pool: Array[GPUParticles2D] = []
var trail_pool: Array[GPUParticles2D] = []

const POOL_SIZE: int = 20

func _ready() -> void:
	# Pre-create particle pools
	_create_particle_pools()

func _process(delta: float) -> void:
	# Update all active projectiles
	_update_projectiles(delta)
	# Redraw projectiles
	queue_redraw()

func _draw() -> void:
	# Draw all active projectiles
	for proj in active_projectiles:
		_draw_projectile(proj)

func _create_particle_pools() -> void:
	# Create impact effect pool
	for i in range(POOL_SIZE):
		var impact = _create_impact_particles()
		impact.emitting = false
		add_child(impact)
		impact_pool.append(impact)
	
	# Create capture effect pool
	for i in range(POOL_SIZE / 2):
		var capture = _create_capture_particles()
		capture.emitting = false
		add_child(capture)
		capture_pool.append(capture)
	
	# Create trail effect pool
	for i in range(POOL_SIZE):
		var trail = _create_trail_particles()
		trail.emitting = false
		add_child(trail)
		trail_pool.append(trail)

func _create_impact_particles() -> GPUParticles2D:
	var particles = GPUParticles2D.new()
	particles.amount = 24
	particles.lifetime = 0.4
	particles.one_shot = true
	particles.explosiveness = 0.95
	particles.randomness = 0.3
	
	var material = ParticleProcessMaterial.new()
	material.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_SPHERE
	material.emission_sphere_radius = 5.0
	material.direction = Vector3(0, 0, 0)
	material.spread = 180.0
	material.initial_velocity_min = 80.0
	material.initial_velocity_max = 150.0
	material.gravity = Vector3(0, 0, 0)
	material.damping_min = 50.0
	material.damping_max = 100.0
	material.scale_min = 3.0
	material.scale_max = 8.0
	material.color = Color(1.0, 0.5, 0.2)
	
	# Color gradient for impact
	var gradient = Gradient.new()
	gradient.set_color(0, Color(1.0, 1.0, 1.0, 1.0))
	gradient.set_color(1, Color(1.0, 0.3, 0.1, 0.0))
	var gradient_tex = GradientTexture1D.new()
	gradient_tex.gradient = gradient
	material.color_ramp = gradient_tex
	
	# Scale curve
	var scale_curve = Curve.new()
	scale_curve.add_point(Vector2(0, 1))
	scale_curve.add_point(Vector2(0.3, 0.8))
	scale_curve.add_point(Vector2(1, 0))
	var scale_tex = CurveTexture.new()
	scale_tex.curve = scale_curve
	material.scale_curve = scale_tex
	
	particles.process_material = material
	
	return particles

func _create_capture_particles() -> GPUParticles2D:
	var particles = GPUParticles2D.new()
	particles.amount = 48
	particles.lifetime = 0.8
	particles.one_shot = true
	particles.explosiveness = 0.9
	particles.randomness = 0.4
	
	var material = ParticleProcessMaterial.new()
	material.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_SPHERE
	material.emission_sphere_radius = 20.0
	material.direction = Vector3(0, -1, 0)
	material.spread = 180.0
	material.initial_velocity_min = 100.0
	material.initial_velocity_max = 200.0
	material.gravity = Vector3(0, 50, 0)
	material.damping_min = 20.0
	material.damping_max = 40.0
	material.scale_min = 4.0
	material.scale_max = 12.0
	
	# Color gradient for capture burst
	var gradient = Gradient.new()
	gradient.set_color(0, Color(1.0, 1.0, 1.0, 1.0))
	gradient.set_color(1, Color(0.5, 1.0, 0.5, 0.0))
	var gradient_tex = GradientTexture1D.new()
	gradient_tex.gradient = gradient
	material.color_ramp = gradient_tex
	
	# Scale curve
	var scale_curve = Curve.new()
	scale_curve.add_point(Vector2(0, 0.5))
	scale_curve.add_point(Vector2(0.2, 1.0))
	scale_curve.add_point(Vector2(1, 0))
	var scale_tex = CurveTexture.new()
	scale_tex.curve = scale_curve
	material.scale_curve = scale_tex
	
	particles.process_material = material
	
	return particles

func _create_trail_particles() -> GPUParticles2D:
	var particles = GPUParticles2D.new()
	particles.amount = 16
	particles.lifetime = 0.3
	particles.one_shot = false
	particles.explosiveness = 0.0
	particles.randomness = 0.2
	
	var material = ParticleProcessMaterial.new()
	material.emission_shape = ParticleProcessMaterial.EMISSION_SHAPE_POINT
	material.direction = Vector3(0, 0, 0)
	material.spread = 30.0
	material.initial_velocity_min = 10.0
	material.initial_velocity_max = 30.0
	material.gravity = Vector3(0, 0, 0)
	material.damping_min = 50.0
	material.damping_max = 80.0
	material.scale_min = 2.0
	material.scale_max = 5.0
	
	# Color gradient for trail
	var gradient = Gradient.new()
	gradient.set_color(0, Color(1.0, 1.0, 1.0, 0.8))
	gradient.set_color(1, Color(0.5, 0.8, 1.0, 0.0))
	var gradient_tex = GradientTexture1D.new()
	gradient_tex.gradient = gradient
	material.color_ramp = gradient_tex
	
	# Scale curve
	var scale_curve = Curve.new()
	scale_curve.add_point(Vector2(0, 1))
	scale_curve.add_point(Vector2(1, 0.2))
	var scale_tex = CurveTexture.new()
	scale_tex.curve = scale_curve
	material.scale_curve = scale_tex
	
	particles.process_material = material
	
	return particles

func spawn_attack_projectile(from_server: ServerNode, to_server: ServerNode) -> void:
	var color = _get_owner_color(from_server.owner_type)
	
	# Get a trail particle from pool
	var trail: GPUParticles2D = _get_from_pool(trail_pool)
	if trail:
		trail.position = from_server.position
		_set_particle_color(trail, color)
		trail.emitting = true
	
	var projectile = {
		"from": from_server,
		"to": to_server,
		"progress": 0.0,
		"speed": 250.0,
		"color": color,
		"trail": trail,
		"time": 0.0
	}
	active_projectiles.append(projectile)

func _update_projectiles(delta: float) -> void:
	var to_remove: Array[int] = []
	
	for i in range(active_projectiles.size()):
		var proj = active_projectiles[i]
		var from_server: ServerNode = proj["from"]
		var to_server: ServerNode = proj["to"]
		
		# Validate servers
		if not is_instance_valid(from_server) or not is_instance_valid(to_server):
			to_remove.append(i)
			continue
		
		# Update progress
		var distance = from_server.position.distance_to(to_server.position)
		var travel_time = distance / proj["speed"]
		proj["progress"] += delta / travel_time
		proj["time"] += delta
		
		# Update trail position
		var current_pos = from_server.position.lerp(to_server.position, proj["progress"])
		if proj["trail"] and is_instance_valid(proj["trail"]):
			proj["trail"].position = current_pos
		
		# Check if projectile reached target
		if proj["progress"] >= 1.0:
			# Spawn impact effect
			spawn_impact_effect(to_server.position, proj["color"])
			
			# Reset progress for continuous attack
			proj["progress"] = 0.0
	
	# Remove invalid projectiles (reverse order)
	for i in range(to_remove.size() - 1, -1, -1):
		var idx = to_remove[i]
		var proj = active_projectiles[idx]
		if proj["trail"] and is_instance_valid(proj["trail"]):
			proj["trail"].emitting = false
		active_projectiles.remove_at(idx)

func stop_projectile(from_server: ServerNode, to_server: ServerNode) -> void:
	for i in range(active_projectiles.size() - 1, -1, -1):
		var proj = active_projectiles[i]
		if proj["from"] == from_server and proj["to"] == to_server:
			if proj["trail"] and is_instance_valid(proj["trail"]):
				proj["trail"].emitting = false
			active_projectiles.remove_at(i)
			break

func stop_all_projectiles_from(server: ServerNode) -> void:
	for i in range(active_projectiles.size() - 1, -1, -1):
		var proj = active_projectiles[i]
		if proj["from"] == server:
			if proj["trail"] and is_instance_valid(proj["trail"]):
				proj["trail"].emitting = false
			active_projectiles.remove_at(i)

func _draw_projectile(proj: Dictionary) -> void:
	var from_server: ServerNode = proj["from"]
	var to_server: ServerNode = proj["to"]
	
	if not is_instance_valid(from_server) or not is_instance_valid(to_server):
		return
	
	var from_pos = from_server.position
	var to_pos = to_server.position
	var progress: float = proj["progress"]  # 0.0 to 1.0 continuously looping
	var color: Color = proj["color"]
	var time: float = proj["time"]
	
	var distance = from_pos.distance_to(to_pos)
	var direction = (to_pos - from_pos).normalized()
	var normal = Vector2(-direction.y, direction.x)
	
	# Draw continuous stream of chevrons along the path for sustained attack
	var chevron_count: int = int(distance / 40.0) + 1
	var chevron_size: float = 12.0
	var offset: float = fmod(progress * chevron_count, 1.0)
	
	for i in range(chevron_count):
		var t = (float(i) + offset) / float(chevron_count)
		if t > 1.0: t -= 1.0
		
		var center = from_pos.lerp(to_pos, t)
		
		# Fade out near the ends
		var alpha_mult = 1.0
		if t < 0.1: alpha_mult = t * 10.0
		elif t > 0.9: alpha_mult = (1.0 - t) * 10.0
		
		var pulse = (sin(time * 10.0 - t * PI * 4.0) + 1.0) / 2.0
		var current_color = color
		current_color.a = (0.5 + pulse * 0.5) * alpha_mult
		
		# Draw chevron ">>>"
		var tip = center + direction * chevron_size
		var left_wing = center - direction * chevron_size + normal * chevron_size * 0.8
		var right_wing = center - direction * chevron_size - normal * chevron_size * 0.8
		
		var points = PackedVector2Array([left_wing, tip, right_wing])
		draw_polyline(points, current_color, 3.0, true)
		
		# Inner bright core of chevron
		var core_color = Color.WHITE
		core_color.a = current_color.a * 0.8
		var points_core = PackedVector2Array([
			center - direction * (chevron_size * 0.5) + normal * chevron_size * 0.4,
			center + direction * (chevron_size * 0.5),
			center - direction * (chevron_size * 0.5) - normal * chevron_size * 0.4
		])
		draw_polyline(points_core, core_color, 1.5, true)

func spawn_impact_effect(pos: Vector2, color: Color) -> void:
	var impact = _get_from_pool(impact_pool)
	if impact:
		impact.position = pos
		_set_particle_color(impact, color)
		impact.restart()
		impact.emitting = true

func spawn_capture_effect(pos: Vector2, owner_type: ServerNode.Owner) -> void:
	var color = _get_owner_color(owner_type)
	
	var capture = _get_from_pool(capture_pool)
	if capture:
		capture.position = pos
		_set_particle_color(capture, color)
		capture.restart()
		capture.emitting = true
	
	# Also spawn multiple impact effects for dramatic effect
	for i in range(3):
		var offset = Vector2(randf_range(-30, 30), randf_range(-30, 30))
		spawn_impact_effect(pos + offset, color)

func _get_owner_color(owner: ServerNode.Owner) -> Color:
	var cb = GameState and GameState.colorblind_mode
	match owner:
		ServerNode.Owner.PLAYER:
			return Color(0.2, 0.5, 1.0) if cb else projectile_color_player
		ServerNode.Owner.ENEMY:
			return Color(1.0, 0.5, 0.0) if cb else projectile_color_enemy
		ServerNode.Owner.ALLY:
			return Color(0.9, 0.8, 0.2) if cb else projectile_color_ally
		_:
			return Color(0.5, 0.8, 1.0)

func _get_from_pool(pool: Array) -> GPUParticles2D:
	for p in pool:
		if not p.emitting:
			return p
	# All in use, return first one anyway
	if pool.size() > 0:
		return pool[0]
	return null

func _set_particle_color(particles: GPUParticles2D, color: Color) -> void:
	var material = particles.process_material as ParticleProcessMaterial
	if material:
		# Update the gradient to use the new color
		var gradient = Gradient.new()
		gradient.set_color(0, Color(1.0, 1.0, 1.0, 1.0))
		gradient.set_color(1, Color(color.r, color.g, color.b, 0.0))
		var gradient_tex = GradientTexture1D.new()
		gradient_tex.gradient = gradient
		material.color_ramp = gradient_tex
		material.color = color
