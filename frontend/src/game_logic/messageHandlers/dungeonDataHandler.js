// frontend/src/game_logic/messageHandlers/dungeonDataHandler.js
import { INITIAL_PLAYER_STATS, LOCAL_TILE_TYPES } from '../initialState'; 

export function handleDungeonData(currentState, message) {
  console.log("[dungeonDataHandler] Received message to process:", message);

  const newState = { ...currentState }; 
  newState.isLoading = false; 
  newState.dungeonMap = message.map; 
  newState.playerPos = message.player_start_pos;
  
  newState.tileDefinitions = { ...LOCAL_TILE_TYPES, ...message.tile_types };
  
  newState.playerStats = message.player_stats || INITIAL_PLAYER_STATS; 
  newState.monsters = message.monsters || []; // Assign monsters from message
  newState.isGameOver = false; 
  newState.currentDungeonLevel = message.current_dungeon_level || currentState.currentDungeonLevel || 1;
  newState.selectedInventoryItemIndex = null;

  newState.gameMessage = { 
    text: `Entered Dungeon Level ${newState.currentDungeonLevel} (Seed: ${message.seed_used || 'N/A'}).`, 
    isError: false, 
    duration: 5000 
  };
  
  console.log("[dungeonDataHandler] New state after processing dungeon_data. isLoading:", newState.isLoading);
  // ADD THIS LOG:
  console.log("[dungeonDataHandler] Final newState.monsters before return:", newState.monsters);
  return newState;
}