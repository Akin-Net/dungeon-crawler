# PowerShell Script to Consolidate Current Project Context and Code

# --- BEGIN SCRIPT ---

param (
    [Parameter(Mandatory=$false)]
    [string[]]$IncludeItems = @(
        # Backend Core Logic
        "backend/app/core/tiles.py",
        "backend/app/core/config.py", 
        "backend/app/core/combat.py", 
        "backend/app/core/player.py", 
        "backend/app/core/map_manager.py", 
        "backend/app/core/entity_manager.py", 
        "backend/app/core/monsters/definitions.py",
        "backend/app/core/monsters/ai.py",
        "backend/app/core/items/definitions.py",
        "backend/app/core/items/effects.py",
        "backend/app/core/dungeon_generator.py",
        "backend/app/core/game_state.py",
        # Backend API and Schemas
        "backend/app/schemas.py",
        "backend/app/main.py",
        # Frontend Game Logic State & Handlers
        "frontend/src/game_logic/initialState.js",
        "frontend/src/game_logic/mainGameStateReducer.js",
        "frontend/src/game_logic/messageHandlers/combatHandler.js",
        "frontend/src/game_logic/messageHandlers/dungeonDataHandler.js",
        "frontend/src/game_logic/messageHandlers/errorHandler.js",
        "frontend/src/game_logic/messageHandlers/gameMessageHandler.js",
        "frontend/src/game_logic/messageHandlers/monsterHandler.js",
        "frontend/src/game_logic/messageHandlers/playerLeveledUpHandler.js",
        "frontend/src/game_logic/messageHandlers/playerMovementHandler.js",
        "frontend/src/game_logic/messageHandlers/playerStatsHandler.js",
        "frontend/src/game_logic/messageHandlers/tileChangeHandler.js",
        # Frontend Hooks
        "frontend/src/hooks/useGameWebSocket.js",
        "frontend/src/hooks/useGameState.js",
        # Frontend Utils
        "frontend/src/utils/mapUtils.js",
        # Frontend Main Components
        "frontend/src/App.jsx",
        "frontend/src/DungeonCanvas.jsx",
        "frontend/src/main.jsx",
        # Test files
        "backend/app/tests/test_combat.py",
        "backend/app/tests/test_player.py",
        "backend/app/tests/test_entity_manager.py",
        "backend/app/tests/test_map_manager.py",
        "backend/app/tests/test_game_state.py",         # ADDED
        "backend/app/tests/test_item_effects.py",      # ADDED
        "backend/app/tests/test_dungeon_generator.py", # ADDED
        "backend/app/tests/test_ai.py"                 # ADDED
    ),
    [Parameter(Mandatory=$false)]
    [string[]]$FileExtensions = @("*.py", "*.js", "*.jsx") 
)

# Get the directory where the script is located (should be your project root)
$ProjectRoot = (Get-Location).Path
Write-Host "Project Root Detected: $ProjectRoot"

# --- Static Context and Summary ---
$StaticContextAndSummary = @"
# Project Context and Code Snapshot for Roguelike Dungeon Crawler

JUST TAKE THE INFORMATION FOR THIS PROJECT IN, LET ME DEFINE THE NEXT STEPS, AND THEN WE CAN MOVE FORWARD.

## Current Project Status Summary (End of Session):

The web-based Roguelike Dungeon Crawler game has undergone extensive backend refactoring for modularity and stability, alongside frontend adjustments for correct rendering. Key systems are functional and unit testing has begun.

**Key Implemented Features & Systems:**

-   **Core Gameplay Loop:** Player movement, combat (bump attacks, monster retaliation), item pickup (potions, scrolls), inventory management (use, equip, unequip), and game over states are functional.
-   **Backend (Python/FastAPI):**
    -   WebSocket communication for real-time game updates.
    -   Pydantic models for robust data validation and schema definition (`schemas.py`).
    -   Centralized game parameter management (`core/config.py`).
    -   `GameState` class (`core/game_state.py`) orchestrates game logic, delegating to specialized managers.
    -   `Player` class (`core/player.py`) manages player state (stats, inventory, equipment, position, XP, leveling).
    -   `MapManager` class (`core/map_manager.py`) handles map data, Fog of War (FoW), Line of Sight (LoS), and pathfinding. FoW includes persistent memory of explored areas.
    -   `EntityManager` class (`core/entity_manager.py`) manages monster entities.
    -   `Combat` module (`core/combat.py`) centralizes attack calculations and resolution of combat outcomes.
    -   Procedural `DungeonGenerator` (`core/dungeon_generator.py`) uses its original, known-good algorithm for map creation, producing good layouts with doors. It places item and monster tiles, which GameState then processes.
    -   Modular design for:
        -   Tile definitions (`core/tiles.py`).
        -   Monster definitions (`core/monsters/definitions.py` using `config.py`) and AI (`core/monsters/ai.py` using a strategy pattern and `config.py`). Includes Goblins, Orcs, Skeletons with LKP and ranged/chaser behaviors.
        -   Item definitions (`core/items/definitions.py` using `config.py`) and effects (`core/items/effects.py` using a registry). Includes Health potions, teleport scrolls, dagger, armor.
-   **Frontend (React/Vite/JavaScript):**
    -   Canvas rendering for the dungeon, player, monsters (as distinct entities on top of map tiles), items, doors, and stairs.
    -   Custom hooks: `useGameWebSocket`, `useGameState` managing client-side state.
    -   Message handlers for various server updates, including `monster_appeared`.
    -   UI displays inventory, equipment, player stats.
-   **Player Progression:** XP, leveling with stat increases, full heal on level-up. Player stats, inventory, and equipment persist across dungeon levels.
-   **Dungeon Features:** Doors, Stairs (allowing descent to new levels).
-   **Bug Fixes & Refinements:** Resolved issues with monster visibility in FoW, player stat persistence, door integrity during monster movement, and numerous refactoring-related bugs.
-   **Unit Testing:** Initiated for backend core components (`combat.py`, `player.py`, `entity_manager.py`, `map_manager.py`) using `pytest`.

**Current Tech Stack:**
-   Frontend: React (with Vite), JavaScript, custom hooks, HTML5 Canvas.
-   Backend: Python, FastAPI, WebSockets, Pydantic, Pytest.

**Current Directory Structure (Relevant Parts):**
roguelike-game/
├── backend/
│   ├── app/
│   │   ├── core/
│   │   │   ├── tiles.py
│   │   │   ├── config.py
│   │   │   ├── combat.py
│   │   │   ├── player.py
│   │   │   ├── map_manager.py
│   │   │   ├── entity_manager.py
│   │   │   ├── monsters/
│   │   │   │   ├── definitions.py
│   │   │   │   └── ai.py
│   │   │   ├── items/
│   │   │   │   ├── definitions.py
│   │   │   │   └── effects.py
│   │   │   ├── dungeon_generator.py
│   │   │   └── game_state.py
│   │   ├── tests/ # ADDED
│   │   │   ├── test_combat.py
│   │   │   ├── test_player.py
│   │   │   ├── test_entity_manager.py
│   │   │   ├── test_map_manager.py
│   │   │   ├── test_game_state.py   # ADDED
│   │   │   ├── test_item_effects.py # ADDED
│   │   │   ├── test_dungeon_generator.py # ADDED
│   │   │   └── test_ai.py # ADDED
│   │   ├── schemas.py
│   │   └── main.py
│   ├── pyproject.toml # ADDED for pytest config
│   └── ...
├── frontend/
│   ├── src/
│   │   ├── hooks/
│   │   │   ├── useGameWebSocket.js
│   │   │   └── useGameState.js
│   │   ├── game_logic/
│   │   │   ├── initialState.js
│   │   │   ├── mainGameStateReducer.js
│   │   │   └── messageHandlers/ 
│   │   │       ├── combatHandler.js
│   │   │       ├── dungeonDataHandler.js
│   │   │       ├── errorHandler.js
│   │   │       ├── gameMessageHandler.js
│   │   │       ├── monsterHandler.js
│   │   │       ├── playerLeveledUpHandler.js
│   │   │       ├── playerMovementHandler.js
│   │   │       ├── playerStatsHandler.js
│   │   │       ├── tileChangeHandler.js
│   │   ├── utils/
│   │   │   └── mapUtils.js
│   │   ├── App.jsx
│   │   ├── DungeonCanvas.jsx
│   │   └── main.jsx
│   └── ...
└── ...

## Potential Future Implementations/Refinements:

(As listed previously - e.g., Advanced Monster AI, More Dungeon Features, Testing, New Features etc.)

## Latest Code Files:
"@

# --- Initialize the output string with the static context ---
$ConsolidatedOutput = $StaticContextAndSummary

# --- Function to process a single item (file or directory) ---
function Process-PathItem {
    param (
        [string]$PathItem,
        [string]$BaseProjectRoot,
        [string[]]$AllowedExtensions
    )

    $FullPath = ""
    if (Test-Path (Join-Path -Path $BaseProjectRoot -ChildPath $PathItem)) {
        $FullPath = Join-Path -Path $BaseProjectRoot -ChildPath $PathItem
    } elseif (Test-Path $PathItem) { 
        $FullPath = $PathItem
    } else {
        Write-Warning "Path item not found: $PathItem (relative to $BaseProjectRoot or absolute)"
        return "" 
    }

    $OutputString = ""

    if (Test-Path $FullPath -PathType Leaf) { 
        $File = Get-Item $FullPath
        $RelativePath = $File.FullName.Substring($BaseProjectRoot.Length).TrimStart("\/")
        $RelativePath = $RelativePath.Replace("\", "/") 
        
        $IncludeFile = $false
        foreach ($ExtPattern in $AllowedExtensions) {
            if ($File.Name -like $ExtPattern) {
                $IncludeFile = $true
                break
            }
        }

        if ($IncludeFile) {
            $FileContent = Get-Content -Raw -Path $File.FullName -ErrorAction SilentlyContinue
            # Check if Get-Content failed or returned empty, but distinguish from genuinely empty files
             if (-not $? -or (-not $FileContent -and (Get-Item $File.FullName).Length -gt 0)) {
                 $OutputString += @"

--- ERROR READING FILE: $RelativePath ---
Could not read content. Check permissions or if file is locked.
--- END ERROR ---
"@
                Write-Warning "Error reading file: $($File.FullName)"
            } else {
                $OutputString += @"

--- BEGIN FILE: $RelativePath ---
$FileContent
--- END FILE: $RelativePath ---
"@
            }
        }
    } elseif (Test-Path $FullPath -PathType Container) { 
        $RelativeDirPath = $FullPath.Substring($BaseProjectRoot.Length).TrimStart("\/")
        $RelativeDirPath = $RelativeDirPath.Replace("\", "/")
        $OutputString += @"

--- ENTERING DIRECTORY: $RelativeDirPath ---
"@
        # Recursively find files within the directory, applying filters
        Get-ChildItem -Path $FullPath -Recurse -File | Where-Object {
            $File = $_
            $IncludeFile = $false
            foreach ($ExtPattern in $AllowedExtensions) {
                if ($File.Name -like $ExtPattern) {
                    $IncludeFile = $true
                    break
                }
            }
            return $IncludeFile
        } | ForEach-Object {
            $SubFile = $_
            $SubRelativePath = $SubFile.FullName.Substring($BaseProjectRoot.Length).TrimStart("\/")
            $SubRelativePath = $SubRelativePath.Replace("\", "/")
            
            $SubFileContent = Get-Content -Raw -Path $SubFile.FullName -ErrorAction SilentlyContinue
            # Check if Get-Content failed or returned empty, but distinguish from genuinely empty files
            if (-not $? -or (-not $SubFileContent -and (Get-Item $SubFile.FullName).Length -gt 0)) {
                 $OutputString += @"

--- ERROR READING FILE: $SubRelativePath ---
Could not read content. Check permissions or if file is locked.
--- END ERROR ---
"@
                Write-Warning "Error reading file: $($SubFile.FullName)"
            } else {
                $OutputString += @"

--- BEGIN FILE: $SubRelativePath ---
$SubFileContent
--- END FILE: $SubRelativePath ---
"@
            }
        }
        $OutputString += @"
--- LEAVING DIRECTORY: $RelativeDirPath ---
"@
    }
    return $OutputString
}


# --- Loop through each specified directory or file ---
foreach ($Item in $IncludeItems) {
    $ConsolidatedOutput += Process-PathItem -PathItem $Item -BaseProjectRoot $ProjectRoot -AllowedExtensions $FileExtensions
}

# --- Output the final consolidated string ---
Write-Output $ConsolidatedOutput

# --- Optional: Attempt to copy to clipboard ---
try {
  Set-Clipboard -Value $ConsolidatedOutput -ErrorAction Stop
  Write-Host "`n---`nContent has also been copied to your clipboard.`n---"
} catch {
  Write-Warning "`n---`nAutomatic copy to clipboard failed. Please copy the output above manually.`n---"
  # Optionally output the content again here if clipboard failed, but Write-Output already did it.
  # Write-Host $ConsolidatedOutput # Avoids double output if primary Write-Output already happened.
}

Write-Host "`nInstructions: Copy the entire output above (starting from '# Project Context and Code Snapshot') and paste it into the new chat."

# --- END SCRIPT ---