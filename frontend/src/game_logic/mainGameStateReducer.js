// frontend/src/game_logic/mainGameStateReducer.js
import { handleDungeonData } from './messageHandlers/dungeonDataHandler';
import { handlePlayerMoved, handleInvalidMove } from './messageHandlers/playerMovementHandler';
import { handleTileChange } from './messageHandlers/tileChangeHandler';
import { handleMonsterMoved, handleMonsterAppeared } from './messageHandlers/monsterHandler'; // Added handleMonsterAppeared
import { handleGameMessage } from './messageHandlers/gameMessageHandler';
import { handlePlayerStatsUpdate } from './messageHandlers/playerStatsHandler';
import { handleCombatEvent, handleEntityDied, handlePlayerDied } from './messageHandlers/combatHandler';
import { handleError } from './messageHandlers/errorHandler'; 
import { handlePlayerLeveledUp } from './messageHandlers/playerLeveledUpHandler';

export function gameStateReducer(state, action) {
  // console.log("[MainReducer] Action received:", 
  //             "Type:", action.type, 
  //             "Payload Type (if message):", action.payload?.type,
  //             "Payload:", action.payload);


  switch (action.type) {
    case 'PROCESS_SERVER_MESSAGE':
      const message = action.payload;
      switch (message.type) {
        case 'dungeon_data':        return handleDungeonData(state, message);
        case 'player_moved':        return handlePlayerMoved(state, message);
        case 'invalid_move':        return handleInvalidMove(state, message);
        case 'tile_change':         return handleTileChange(state, message);
        case 'game_message':        return handleGameMessage(state, message);
        case 'player_stats_update': return handlePlayerStatsUpdate(state, message);
        case 'combat_event':        return handleCombatEvent(state, message);
        case 'entity_died':         return handleEntityDied(state, message);
        case 'player_died':         return handlePlayerDied(state, message);
        case 'monster_moved':       return handleMonsterMoved(state, message);
        case 'monster_appeared':    return handleMonsterAppeared(state, message); // New handler
        case 'player_leveled_up':   return handlePlayerLeveledUp(state, message);
        case 'error':               
        case 'parse_error':         
          return handleError(state, message); 
        default:
          console.warn(`[MainReducer] Unhandled server message sub-type: ${message.type}`, message);
          return state; 
      }
    case 'SET_LOADING':
      return { ...state, isLoading: action.payload };
    case 'SET_GAME_MESSAGE': 
      return { ...state, gameMessage: { text: action.payload.text, isError: action.payload.isError || false, duration: action.payload.duration === undefined ? 3000 : action.payload.duration }};
    case 'SELECT_INVENTORY_ITEM':
      return { ...state, selectedInventoryItemIndex: action.payload };
    case 'CLEAR_SELECTED_INVENTORY_ITEM':
      return { ...state, selectedInventoryItemIndex: null };
    default:
      console.warn("[MainReducer] Unhandled action type:", action.type);
      return state;
  }
}