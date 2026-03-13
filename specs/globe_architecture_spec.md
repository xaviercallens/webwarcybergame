# Neo-Hack: Gridlock — 3D Globe Architecture Spec

**Version:** 2.0 (3D Pivot) | **Date:** March 13, 2026

---

## 1. The Vision

We are pivoting from a flat, 2D network (Pixi.js) to a **massive multiplayer 3D interactive Earth Globe** (Three.js), directly inspired by the GitHub Homepage Globe. 

Players and AI factions will be distributed across the planet. Real-time attacks will be visualized as **glowing arcs** soaring through the atmosphere between continents.

## 2. Technical Stack Changes

| Component | Previous (2D) | New (3D) |
|-----------|----------------|----------|
| **Renderer** | Pixi.js | `three`, `globe.gl` (built on `three-globe`) |
| **Coordinates**| 2D Cartesian `(x, y)` | Geographic `(lat, lng)` + Altitude |
| **Connections**| Straight 2D lines | 3D Bezier Arcs (`arcsData`) |
| **Camera** | 2D Pan/Zoom | 3D OrbitControls (Rotate, Zoom, Tilt) |
| **Map Gen** | Screen-space rings | Spherical distribution (Lat/Lng clusters) |

## 3. Visual Implementation Details

### 3.1 The Earth Base
- We will use `globe.gl` to render a highly performant Earth.
- Instead of a textured map, the landmasses will be constructed from a dense array of glowing points (or hex polygons) derived from GeoJSON data, achieving the "cyberpunk digital planet" look.
- **Halo & Atmosphere**: A custom shader glow will encompass the globe, matching the CSS design tokens (`--color-glow`).

### 3.2 Faction Nodes (Players & AI)
- Nodes will be mapped to specific geographic cities/regions (e.g., Tokyo, New York, Frankfurt).
- Rendered as glowing pillars or custom Three.js meshes rising out of the globe.
- **Colors**: Green (Player), Red (Enemy), Blue (Ally), Cyan (Neutral).

### 3.3 Combat & Arcs
- When an attack occurs, a 3D arc jumps from the origin coordinate to the destination coordinate.
- The arc's peak altitude scales with the distance between the two points.
- An animated particle (a glowing "packet") will travel along the arc to represent the data flow, resolving in an impact ripple upon hitting the target firewall.

## 4. Required Implementation Steps

### Phase 2 Rewrite: 3D Engine Setup
1. **Dependencies**: `npm remove pixi.js` → `npm install three globe.gl`.
2. **GeoJSON**: Obtain a lightweight TopoJSON/GeoJSON of Earth's landmasses to generate the dotted map surface.
3. **Renderer Class**: Rewrite `scripts/renderer.js` to instantiate `Globe()` from `globe.gl`, attach it to the `canvas-container`, and configure its atmosphere, lighting, and performance tiers.
4. **Interactions**: Map Globe.gl's built-in `onPointClick` to our `nodeClicked` event handlers.

### Phase 3 Update: Geographic Map Generation
1. **Coordinate System**: Update `game-engine.js` to assign `(lat, lng)` to nodes instead of `(x, y)`.
2. **Clustering**: Generate "Leagues" or sub-networks by clustering neutral/enemy nodes within a 2000km radius of the player's capital node.
3. **Arcs Update**: The game loop will pass active attacks to the renderer as `arcsData`, triggering the 3D animation sequence.

### Performance Considerations
- To maintain 60FPS like the GitHub globe, we will aggressively cull geometries, avoid expensive anti-aliasing if the pixel ratio is high, and use instanced meshes for the thousands of landmass dots.

---

## 5. Next Actions for Approval

If this specification aligns with your vision for a global, multi-league cyberpunk warfare experience, respond with your approval. 

I will immediately tear down the Pixi.js implementation and begin scaffolding the **Three.js + Globe.GL engine**.
