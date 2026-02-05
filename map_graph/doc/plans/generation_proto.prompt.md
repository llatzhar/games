# Implementation Plan: Map Generation Algorithm & Pyxel Map Viewer

## 1. Overview

This plan covers the implementation of a procedural map generation system and an interactive Pyxel-based map viewer. The map generation creates a graph structure of cities (nodes) and roads (edges) that expands over time through a "discovery" mechanism. The viewer provides visualization tools including zoom, pan, and generation history navigation.

## 2. Goals / Non-Goals

### Goals

- Implement the initial map generation (3-city equilateral triangle layout)
- Implement city placement algorithm (Centroid-based Radial Placement + Random Variance)
- Implement road generation algorithm (Nearest-First + Intersection Check + Fallback)
- Implement line segment intersection detection using CCW algorithm
- Create a Pyxel-based map viewer with:
  - Mouse wheel zoom in/out
  - Mouse drag panning
  - Generation history navigation buttons (forward/backward)
- Store generation history to allow stepping through map evolution
- Support configurable parameters via YAML

### Non-Goals

- Full game implementation (combat, units, AI)
- Network/multiplayer support
- Discovery trigger probability system (deferred to game loop integration phase)
- Terrain/biome visualization
- Save/load to persistent storage

## 3. Assumptions

- Python 3.9+ is the target runtime environment
- Pyxel 2.x is available and will be used for rendering
- The viewer is a standalone tool for algorithm verification, not the final game UI
- Map generation parameters will be tuned via YAML configuration file
- All coordinate calculations use floating-point; rendering converts to screen pixels
- Generation history is stored in memory (not persisted to disk)
- Single-window application; no multi-display support required

## 4. Constraints

- Pyxel has a fixed palette (16 colors) - visual design must accommodate this
- Pyxel uses integer pixel coordinates - floating-point map coordinates must be transformed
- Frame budget: rendering must complete within 16ms for 60 FPS target
- Road intersection check must handle edge cases (shared endpoints, collinear segments)
- City placement retry limit: 100 attempts before fallback

## 5. Proposed Approach

### 5.1 Architecture

The system is divided into three layers:

| Layer | Responsibility |
|-------|----------------|
| **Models** | Data structures for City, Road, Nation, MapState |
| **Generation** | Algorithms for city placement, road generation, geometry utilities |
| **Viewer** | Pyxel rendering, camera control, input handling, UI buttons |

### 5.2 Generation History

Each time a new city is added, the entire MapState is snapshotted and stored in a history list. The viewer can navigate this history using forward/backward buttons.

### 5.3 Coordinate System

- **World coordinates**: Floating-point, origin at (0, 0), units are abstract
- **Screen coordinates**: Integer pixels, origin at top-left
- **Transformation**: Apply camera offset (pan) and scale (zoom), then convert to int

## 6. Step-by-Step Plan

### Phase 1: Project Setup

| Step | Description |
|------|-------------|
| 1.1 | Create project directory structure |
| 1.2 | Create requirements.txt with dependencies (pyxel, pyyaml) |
| 1.3 | Create config/map_generation.yaml with default parameters |

### Phase 2: Data Models

| Step | Description |
|------|-------------|
| 2.1 | Implement City dataclass (id, x, y, owner_nation_id) |
| 2.2 | Implement Road dataclass (city_a_id, city_b_id) |
| 2.3 | Implement Nation dataclass (id, name, is_player) |
| 2.4 | Implement MapState class with cities list, roads list, helper methods |
| 2.5 | Implement MapHistory class to store snapshots of MapState |

### Phase 3: Geometry Utilities

| Step | Description |
|------|-------------|
| 3.1 | Implement Vec2 class or use tuple for 2D points |
| 3.2 | Implement CCW function for orientation test |
| 3.3 | Implement segments_intersect function |
| 3.4 | Implement distance and angle calculation utilities |

### Phase 4: City Placement Algorithm

| Step | Description |
|------|-------------|
| 4.1 | Implement initial_triangle_placement (3 cities in equilateral layout) |
| 4.2 | Implement calculate_centroid function |
| 4.3 | Implement find_placement_position (radial + variance) |
| 4.4 | Implement validate_city_position (min distance check) |
| 4.5 | Implement add_city_with_retry (up to 100 attempts) |

### Phase 5: Road Generation Algorithm

| Step | Description |
|------|-------------|
| 5.1 | Implement sort_cities_by_distance |
| 5.2 | Implement check_road_validity (length, intersection) |
| 5.3 | Implement generate_roads_for_new_city (nearest-first logic) |
| 5.4 | Implement fallback_connect (forced connection to nearest) |

### Phase 6: Pyxel Viewer - Camera System

| Step | Description |
|------|-------------|
| 6.1 | Implement Camera class with offset_x, offset_y, zoom properties |
| 6.2 | Implement world_to_screen coordinate transformation |
| 6.3 | Implement screen_to_world coordinate transformation |
| 6.4 | Implement handle_mouse_wheel for zoom control |
| 6.5 | Implement handle_mouse_drag for pan control |

### Phase 7: Pyxel Viewer - Rendering

| Step | Description |
|------|-------------|
| 7.1 | Implement draw_roads (lines between cities) |
| 7.2 | Implement draw_cities (circles with color by owner) |
| 7.3 | Implement draw_city_labels (optional city IDs) |
| 7.4 | Implement draw_ui (generation counter, buttons) |

### Phase 8: Pyxel Viewer - UI Controls

| Step | Description |
|------|-------------|
| 8.1 | Implement Button class (position, size, label, click detection) |
| 8.2 | Implement prev_generation button |
| 8.3 | Implement next_generation button |
| 8.4 | Implement add_city button (for manual testing) |
| 8.5 | Implement reset button (return to initial state) |

### Phase 9: Main Application

| Step | Description |
|------|-------------|
| 9.1 | Implement App class inheriting Pyxel patterns |
| 9.2 | Initialize Pyxel window with appropriate size |
| 9.3 | Load configuration from YAML |
| 9.4 | Create initial map state (3-city triangle) |
| 9.5 | Wire up update loop (input handling) |
| 9.6 | Wire up draw loop (rendering) |

### Phase 10: Integration and Testing

| Step | Description |
|------|-------------|
| 10.1 | Manual visual verification of initial triangle |
| 10.2 | Verify city placement expands outward correctly |
| 10.3 | Verify roads do not intersect (visual check) |
| 10.4 | Verify zoom and pan work smoothly |
| 10.5 | Verify generation navigation works correctly |

## 7. Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| City placement fails all 100 attempts | Low | High | Fallback: place at random position with forced road connection |
| Road intersection detection false positives/negatives | Medium | Medium | Add unit tests for edge cases; visual verification in viewer |
| Zoom causes cities to go off-screen | Medium | Low | Implement zoom limits; add "fit to view" button |
| Performance degrades with many cities | Low | Medium | Limit city count for viewer; optimize rendering if needed |
| Pyxel mouse wheel input not detected | Low | Medium | Verify Pyxel version supports mouse wheel; fallback to keyboard zoom |
| Floating-point precision issues in geometry | Low | Medium | Use epsilon comparisons for near-zero values |

## 8. Open Questions

| Question | Impact | Notes |
|----------|--------|-------|
| What is the maximum number of cities to support in the viewer? | Affects performance testing | Target 100 for visualization purposes |
| Should city colors be configurable or fixed per nation? | UI design | Default to fixed palette (Player=blue, Enemy=red) |
| Should the viewer support keyboard shortcuts for navigation? | UX | Could add arrow keys for pan, +/- for zoom |
| What screen resolution should the Pyxel window use? | Layout | Suggest 320x240 or 256x256 (retro aesthetic) or larger 640x480 |
| Should RNG seed be displayed/configurable in the viewer? | Debug capability | Useful for reproducing specific map layouts |
| Should the viewer auto-generate cities on a timer, or only on button click? | UX design | Manual button click preferred for step-by-step verification |

## 9. Completion Checklist

- [ ] Project structure created with all directories
- [ ] requirements.txt contains pyxel and pyyaml
- [ ] YAML configuration file exists with documented parameters
- [ ] City, Road, Nation, MapState models implemented
- [ ] CCW intersection algorithm implemented and tested
- [ ] Initial triangle placement works
- [ ] New city placement expands map outward
- [ ] Roads connect without intersection (except fallback)
- [ ] Camera pan works with mouse drag
- [ ] Camera zoom works with mouse wheel
- [ ] Generation history navigation (prev/next) works
- [ ] UI buttons render and respond to clicks
- [ ] 60 FPS maintained with up to 100 cities

## 10. File Structure

```
map_graph/
├── requirements.txt
├── config/
│   └── map_generation.yaml
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── city.py
│   │   ├── road.py
│   │   ├── nation.py
│   │   └── map_state.py
│   ├── generation/
│   │   ├── __init__.py
│   │   ├── city_placer.py
│   │   ├── road_generator.py
│   │   └── geometry.py
│   └── viewer/
│       ├── __init__.py
│       ├── app.py
│       ├── camera.py
│       ├── renderer.py
│       ├── input_handler.py
│       └── ui.py
└── tests/
    ├── __init__.py
    ├── test_geometry.py
    ├── test_city_placer.py
    └── test_road_generator.py
```

## 11. Configuration Parameters (map_generation.yaml)

| Parameter | Default | Description |
|-----------|---------|-------------|
| initial_triangle_radius | 100.0 | Distance from center to initial cities |
| min_distance_from_existing | 80.0 | Minimum distance for new city placement |
| max_distance_from_existing | 200.0 | Maximum distance for new city placement |
| placement_angle_variance | 30.0 | Angular variance in degrees |
| placement_max_attempts | 100 | Retry limit for valid placement |
| min_roads_per_city | 1 | Minimum roads for new city |
| max_roads_per_city | 3 | Maximum roads for new city |
| max_road_length | 150.0 | Maximum allowed road length |
| viewer_width | 480 | Pyxel window width |
| viewer_height | 360 | Pyxel window height |
| initial_zoom | 1.0 | Starting zoom level |
| zoom_min | 0.25 | Minimum zoom (zoomed out) |
| zoom_max | 4.0 | Maximum zoom (zoomed in) |
| zoom_step | 0.1 | Zoom change per wheel tick |
