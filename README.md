# Roguelike Dungeon Crawler

A web-based dungeon crawler game built with a Python/FastAPI backend and a React frontend.

## Project Status

The core gameplay loop is functional with significant backend refactoring completed for modularity and stability. Unit testing for key backend components is well underway.

## Tech Stack

*   **Backend:** Python, FastAPI, WebSockets, Pydantic, Pytest
*   **Frontend:** React (with Vite), JavaScript, HTML5 Canvas

## Features

*   Procedural dungeon generation with rooms, corridors, and doors.
*   Player movement and exploration with Fog of War and Line of Sight.
*   Basic combat system (bump to attack, monster retaliation).
*   Monster entities with different AI behaviors (Chaser, Ranged) and Last Known Player Position tracking.
*   Item system including consumables (potions, scrolls) and equippable gear (weapons, armor).
*   Inventory and Equipment management.
*   Player progression via XP and leveling, with stat increases and full heal on level up.
*   Stairs to descend to new dungeon levels (player state persists).
*   Game Over state.

## Architecture Highlights

### Backend (Python/FastAPI)

The backend is designed with a focus on modularity and uses WebSockets for real-time communication with the frontend.

*   **FastAPI:** Provides the web server framework and WebSocket endpoint.
*   **Pydantic:** Used for strict data validation and clear schema definition for messages sent between frontend and backend (`schemas.py`).
*   **`GameState` (`core/game_state.py`):** The central orchestrator of game logic. It holds the current state and delegates actions to specialized managers.
*   **`Player` (`core/player.py`):** Manages the player character's state, including position, stats, inventory, and equipment.
*   **`MapManager` (`core/map_manager.py`):** Handles dungeon map data, Fog of War, Line of Sight calculations, and pathfinding (`find_path_bfs`).
*   **`EntityManager` (`core/entity_manager.py`):** Manages all non-player entities in the dungeon (currently monsters).
*   **`DungeonGenerator` (`core/dungeon_generator.py`):** Implements the algorithm for creating dungeon layouts.
*   **`Combat` (`core/combat.py`):** Contains the logic for resolving attacks and calculating damage.
*   **`Config` (`core/config.py`):** Centralized file for game parameters (player stats, monster data, item values, generation parameters, etc.).
*   **Monsters (`core/monsters/`)**: Definitions (`definitions.py`) and AI strategies (`ai.py`).
*   **Items (`core/items/`)**: Definitions (`definitions.py`) and effect handlers (`effects.py`).

### Frontend (React/JavaScript)

The frontend manages the client-side state and renders the game world and UI.

*   **React/Vite:** Component-based UI framework and build tool.
*   **HTML5 Canvas:** Used for rendering the dungeon map, entities, and items.
*   **Custom Hooks:** `useGameWebSocket` and `useGameState` manage the WebSocket connection and client-side game state updates based on server messages.
*   **Message Handlers:** Modular functions process specific message types received from the server.

## Getting Started

(Instructions for setting up and running the project would go here)

## Unit Testing

Backend unit tests are written using `pytest` and cover core game logic components.

Current test coverage focuses on:

*   **Combat Logic** (`test_combat.py`)
*   **Player State Management** (`test_player.py`)
*   **Entity Management** (`test_entity_manager.py`)
*   **Map Management** (`test_map_manager.py` - basic FoV/LoS)
*   **Game State Orchestration** (`test_game_state.py` - covering dungeon generation, player movement interactions like combat/items/doors/stairs, item usage, equipping, and unequipping).
*   **Item Effects** (`test_item_effects.py` - healing and teleport effects).
*   **Dungeon Generation** (`test_dungeon_generator.py` - map dimensions, player start, room generation, entity placement, room connectivity).
*   **Monster AI Strategies** (`test_ai.py` - ChaserAI behavior in various states).

To run the tests, navigate to the `backend` directory and execute `pytest`.

```bash
cd backend
pytest