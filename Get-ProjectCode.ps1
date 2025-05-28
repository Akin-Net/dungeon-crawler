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
        # Frontend Sprite Components & CSS (NEW)
        "frontend/src/components/sprites/PlayerSprite.jsx",    # Assuming you'll create this for consistency
        "frontend/src/components/sprites/GoblinSprite.jsx",
        "frontend/src/components/sprites/OrcSprite.jsx",       # Assuming you'll create this
        "frontend/src/components/sprites/SkeletonSprite.jsx",  # Assuming you'll create this
        "frontend/src/components/sprites/sprites.css",
        # Backend Test files
        "backend/app/tests/test_combat.py",
        "backend/app/tests/test_player.py",
        "backend/app/tests/test_entity_manager.py",
        "backend/app/tests/test_map_manager.py",
        "backend/app/tests/test_game_state.py",
        "backend/app/tests/test_item_effects.py",
        "backend/app/tests/test_dungeon_generator.py",
        "backend/app/tests/test_ai.py",
        # Frontend Test Files
        "frontend/src/game_logic/messageHandlers/__tests__/combatHandler.test.js",
        "frontend/src/game_logic/messageHandlers/__tests__/dungeonDataHandler.test.js",
        "frontend/src/game_logic/messageHandlers/__tests__/errorHandler.test.js",
        "frontend/src/game_logic/messageHandlers/__tests__/gameMessageHandler.test.js",
        "frontend/src/game_logic/messageHandlers/__tests__/monsterHandler.test.js",
        "frontend/src/game_logic/messageHandlers/__tests__/playerLeveledUpHandler.test.js",
        "frontend/src/game_logic/messageHandlers/__tests__/playerMovementHandler.test.js",
        "frontend/src/game_logic/messageHandlers/__tests__/playerStatsHandler.test.js",
        "frontend/src/game_logic/messageHandlers/__tests__/tileChangeHandler.test.js",
        "frontend/src/hooks/__tests__/useGameState.test.js",
        "frontend/src/hooks/__tests__/useGameWebSocket.test.js",
        "frontend/src/__tests__/DungeonCanvas.test.jsx" # Added this existing test file
    ),
    [Parameter(Mandatory=$false)]
    [string[]]$FileExtensions = @("*.py", "*.js", "*.jsx", "*.css") # Added *.css
)

# Get the directory where the script is located (should be your project root)
$ScriptDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = $ScriptDirectory # Assuming script is in project root
# If script is in a subfolder like '.scripts', adjust $ProjectRoot accordingly:
# $ProjectRoot = Join-Path -Path $ScriptDirectory -ChildPath ".."
# $ProjectRoot = Resolve-Path $ProjectRoot # Normalize path

Write-Host "Project Root Detected: $ProjectRoot"

# --- Static Context and Summary ---
$StaticContextAndSummary = @"
# Project Context and Code Snapshot for Roguelike Dungeon Crawler

JUST TAKE THE INFORMATION FOR THIS PROJECT IN, LET ME DEFINE THE NEXT STEPS, AND THEN WE CAN MOVE FORWARD.

## Current Project Status Summary (End of Session):

The web-based Roguelike Dungeon Crawler game has undergone extensive backend refactoring for modularity and stability. Frontend work includes moving towards CSS-based sprites for entities, overlaying them on a canvas-rendered map. Key systems are functional and unit testing is ongoing.

**Key Implemented Features & Systems:**

-   **Core Gameplay Loop:** Player movement, combat, item pickup, inventory management, and game over states are functional.
-   **Backend (Python/FastAPI):**
    -   WebSocket communication, Pydantic schemas, centralized config.
    -   `GameState`, `Player`, `MapManager`, `EntityManager`, `Combat`, `DungeonGenerator` modules.
    -   Modular tile, monster (with AI), and item (with effects) definitions.
-   **Frontend (React/Vite/JavaScript):**
    -   Canvas rendering for the map background and tile-based items.
    -   **CSS Sprites:** Entities (Player, Monsters) are rendered as HTML elements styled with CSS, positioned over the canvas. Work is in progress to refine these CSS-only sprites.
    -   Custom hooks: `useGameWebSocket`, `useGameState`.
    -   Message handlers for server updates.
    -   UI displays inventory, equipment, player stats.
-   **Player Progression & Dungeon Features:** XP, leveling, doors, stairs are functional.
-   **Unit Testing:** Extensive backend (`pytest`) and frontend (`Vitest`) unit tests.

**Current Tech Stack:**
-   Frontend: React (with Vite), JavaScript, CSS, Vitest, Testing Library.
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
│   │   ├── tests/ 
│   │   │   ├── test_combat.py
│   │   │   ├── test_player.py
│   │   │   ├── test_entity_manager.py
│   │   │   ├── test_map_manager.py
│   │   │   ├── test_game_state.py   
│   │   │   ├── test_item_effects.py 
│   │   │   ├── test_dungeon_generator.py 
│   │   │   └── test_ai.py 
│   │   ├── schemas.py
│   │   └── main.py
│   ├── pyproject.toml 
│   └── ...
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   └── sprites/      # NEW directory for sprite components
│   │   │       ├── PlayerSprite.jsx
│   │   │       ├── GoblinSprite.jsx
│   │   │       ├── OrcSprite.jsx
│   │   │       ├── SkeletonSprite.jsx
│   │   │       └── sprites.css # CSS for these components
│   │   ├── hooks/
│   │   │   ├── __tests__/
│   │   │   │   ├── useGameWebSocket.test.js
│   │   │   │   └── useGameState.test.js
│   │   │   ├── useGameWebSocket.js
│   │   │   └── useGameState.js
│   │   ├── game_logic/
│   │   │   ├── __tests__/
│   │   │   │   ├── combatHandler.test.js
│   │   │   │   ├── dungeonDataHandler.test.js
│   │   │   │   ├── errorHandler.test.js
│   │   │   │   ├── gameMessageHandler.test.js
│   │   │   │   ├── monsterHandler.test.js
│   │   │   │   ├── playerLeveledUpHandler.test.js
│   │   │   │   ├── playerMovementHandler.test.js
│   │   │   │   └── playerStatsHandler.test.js
│   │   │   ├── initialState.js
│   │   │   ├── mainGameStateReducer.js
│   │   │   └── messageHandlers/ 
│   │   ├── utils/
│   │   │   └── mapUtils.js
│   │   ├── __tests__/          # For component tests like DungeonCanvas.test.jsx
│   │   │   └── DungeonCanvas.test.jsx
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
    # Check if PathItem is relative to BaseProjectRoot first
    $AttemptRelative = Join-Path -Path $BaseProjectRoot -ChildPath $PathItem
    if (Test-Path $AttemptRelative) {
        $FullPath = $AttemptRelative
    } elseif (Test-Path $PathItem) { # Then check if it's an absolute path
        $FullPath = $PathItem
    } else {
        Write-Warning "Path item not found: $PathItem (tried relative to $BaseProjectRoot and absolute)"
        return "" 
    }

    $OutputString = ""

    if (Test-Path $FullPath -PathType Leaf) { 
        $File = Get-Item $FullPath
        # Ensure BaseProjectRoot ends with a path separator for correct substring length, or normalize
        $NormalizedBaseProjectRoot = $BaseProjectRoot
        if (-not ($NormalizedBaseProjectRoot.EndsWith("\") -or $NormalizedBaseProjectRoot.EndsWith("/"))) {
            $NormalizedBaseProjectRoot += Get-Location | Select-Object -ExpandProperty Provider | ForEach-Object {$_.PathSeparator}
        }
        # Ensure paths use forward slashes for consistency in the output
        $RelativePath = $File.FullName.Substring($NormalizedBaseProjectRoot.Length).Replace("\", "/")
        
        $IncludeFile = $false
        foreach ($ExtPattern in $AllowedExtensions) {
            if ($File.Name -like $ExtPattern) {
                $IncludeFile = $true
                break
            }
        }

        if ($IncludeFile) {
            $FileContent = Get-Content -Raw -Path $File.FullName -ErrorAction SilentlyContinue
            if (-not $?) { 
                 $OutputString += @"

--- ERROR READING FILE: /$RelativePath ---
Could not read content. Get-Content failed. Check permissions or if file is locked/exists.
--- END ERROR ---
"@
                Write-Warning "Error reading file (Get-Content failed): $($File.FullName)"
            } elseif (-not $FileContent -and (Get-Item $File.FullName).Length -gt 0) { 
                 $OutputString += @"

--- ERROR READING FILE: /$RelativePath ---
File has size but Get-Content -Raw returned empty. Possible encoding issue or very large file.
--- END ERROR ---
"@
                Write-Warning "Error: File $($File.FullName) has size but no content was retrieved."
            } else { 
                $OutputString += @"

--- BEGIN FILE: /$RelativePath ---
$FileContent
--- END FILE: /$RelativePath ---
"@
            }
        }
    } elseif (Test-Path $FullPath -PathType Container) { 
        $NormalizedBaseProjectRoot = $BaseProjectRoot
        if (-not ($NormalizedBaseProjectRoot.EndsWith("\") -or $NormalizedBaseProjectRoot.EndsWith("/"))) {
            $NormalizedBaseProjectRoot += Get-Location | Select-Object -ExpandProperty Provider | ForEach-Object {$_.PathSeparator}
        }
        $RelativeDirPath = $FullPath.Substring($NormalizedBaseProjectRoot.Length).Replace("\", "/")
        $OutputString += @"

--- ENTERING DIRECTORY: /$RelativeDirPath ---
"@
        Get-ChildItem -Path $FullPath -File -Recurse | ForEach-Object { 
            $SubFile = $_
            $IncludeSubFile = $false
            foreach ($ExtPattern in $AllowedExtensions) {
                if ($SubFile.Name -like $ExtPattern) {
                    $IncludeSubFile = $true
                    break
                }
            }

            if ($IncludeSubFile) {
                $SubRelativePath = $SubFile.FullName.Substring($NormalizedBaseProjectRoot.Length).Replace("\", "/")
                
                $SubFileContent = Get-Content -Raw -Path $SubFile.FullName -ErrorAction SilentlyContinue
                 if (-not $?) { 
                    $OutputString += @"

--- ERROR READING FILE: /$SubRelativePath ---
Could not read content. Get-Content failed. Check permissions or if file is locked/exists.
--- END ERROR ---
"@
                    Write-Warning "Error reading file (Get-Content failed): $($SubFile.FullName)"
                } elseif (-not $SubFileContent -and (Get-Item $SubFile.FullName).Length -gt 0) {
                    $OutputString += @"

--- ERROR READING FILE: /$SubRelativePath ---
File has size but Get-Content -Raw returned empty.
--- END ERROR ---
"@
                    Write-Warning "Error: File $($SubFile.FullName) has size but no content was retrieved."
                } else {
                    $OutputString += @"

--- BEGIN FILE: /$SubRelativePath ---
$SubFileContent
--- END FILE: /$SubRelativePath ---
"@
                }
            }
        }
        $OutputString += @"
--- LEAVING DIRECTORY: /$RelativeDirPath ---
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
}

Write-Host "`nInstructions: Copy the entire output above (starting from '# Project Context and Code Snapshot') and paste it into the new chat."

# --- END SCRIPT ---