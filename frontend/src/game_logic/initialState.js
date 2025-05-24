// frontend/src/game_logic/initialState.js

export const LOCAL_TILE_TYPES = { 
    EMPTY: 0, 
    FLOOR: 1, 
    WALL: 2, 
    ITEM_POTION: 3, 
    MONSTER_GOBLIN: 4,
    MONSTER_ORC: 5,
    MONSTER_SKELETON: 6,
    DOOR_CLOSED: 7,
    DOOR_OPEN: 8,
    STAIRS_DOWN: 10, 
    FOG: 11,
    ITEM_SCROLL_TELEPORT: 12, // Added
};

export const INITIAL_PLAYER_STATS = { 
    hp: 0, max_hp: 0, attack: 0, defense: 0, 
    // potions: 0, // Removed
    level: 1, xp: 0, xp_to_next_level: 100,
    inventory: [], // Added: List of InventoryItemDetail objects
    equipment: { // Added: Dict of slot to InventoryItemDetail object or null
        weapon: null,
        armor: null,
        // ring1: null, amulet: null, etc.
    }
};

export const initialState = {
  dungeonMap: null, 
  playerPos: null,
  tileDefinitions: LOCAL_TILE_TYPES, 
  gameMessage: { text: '', isError: false, duration: 0 },
  isLoading: true,
  playerStats: INITIAL_PLAYER_STATS,
  monsters: [], 
  isGameOver: false,
  currentDungeonLevel: 1, 
  // For UI interaction with inventory/equipment
  selectedInventoryItemIndex: null, 
};