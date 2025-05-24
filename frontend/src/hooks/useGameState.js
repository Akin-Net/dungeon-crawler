// frontend/src/hooks/useGameState.js
import { useReducer, useEffect, useCallback, useRef } from 'react';
import { gameStateReducer } from '../game_logic/mainGameStateReducer'; 
import { initialState } from '../game_logic/initialState';

export function useGameState(messageBatchFromServer, sendMessageToServer) {
  const [state, dispatch] = useReducer(gameStateReducer, initialState);
  const gameMessageTimeoutRef = useRef(null);

  useEffect(() => {
    if (gameMessageTimeoutRef.current) clearTimeout(gameMessageTimeoutRef.current);
    if (state.gameMessage.text && state.gameMessage.duration > 0) {
      gameMessageTimeoutRef.current = setTimeout(() => {
        dispatch({ type: 'SET_GAME_MESSAGE', payload: { text: '', isError: false, duration: 0 } });
      }, state.gameMessage.duration);
    }
    return () => { if (gameMessageTimeoutRef.current) clearTimeout(gameMessageTimeoutRef.current); };
  }, [state.gameMessage]);

  useEffect(() => {
    if (!messageBatchFromServer || messageBatchFromServer.length === 0) return;
    messageBatchFromServer.forEach(individualMessage => {
      dispatch({ type: 'PROCESS_SERVER_MESSAGE', payload: individualMessage });
    });
  }, [messageBatchFromServer]);

  const requestNewDungeonGeneration = useCallback((seed, isNewLevel = false) => {
    console.log("[useGameState ACTION] requestNewDungeonGeneration called with seed:", seed, "isNewLevel:", isNewLevel);
    if (!isNewLevel) { 
        dispatch({ type: 'SET_LOADING', payload: true });
    }
    dispatch({ type: 'SET_GAME_MESSAGE', payload: { text: `Requesting dungeon (Seed: ${seed})...`, duration: 0 }}); 
    if (sendMessageToServer) {
        sendMessageToServer({ action: 'generate_dungeon', seed: seed });
    } else { 
        console.error("sendMessageToServer is not available in requestNewDungeonGeneration");
        dispatch({ type: 'SET_LOADING', payload: false }); 
        dispatch({ type: 'SET_GAME_MESSAGE', payload: {text: "Error: Cannot connect to server.", isError: true, duration: 0}});
    }
  }, [sendMessageToServer]);

  const attemptPlayerMove = useCallback((intendedX, intendedY) => {
    if (state.isGameOver) {
      dispatch({ type: 'SET_GAME_MESSAGE', payload: { text: "Game Over. Generate a new dungeon.", isError: true, duration: 0 }});
      return;
    }
    if (sendMessageToServer) {
        sendMessageToServer({ action: 'player_move', new_pos: { x: intendedX, y: intendedY } });
    } else {
        dispatch({ type: 'SET_GAME_MESSAGE', payload: {text: "Error: Cannot send move to server.", isError: true, duration: 0}});
    }
  }, [sendMessageToServer, state.isGameOver]);

  // const attemptUsePotion = useCallback(() => { // Deprecated
  //   // ...
  // }, [sendMessageToServer, state.isGameOver]);

  const attemptUseItem = useCallback((itemId) => {
    if (state.isGameOver) {
      dispatch({ type: 'SET_GAME_MESSAGE', payload: { text: "Game Over. Cannot use items.", isError: true, duration: 0 }});
      return;
    }
    if (!itemId) {
        dispatch({ type: 'SET_GAME_MESSAGE', payload: {text: "No item selected to use.", isError: true, duration: 3000}});
        return;
    }
    if (sendMessageToServer) {
        console.log(`[useGameState] Attempting to use item with ID: ${itemId}`);
        sendMessageToServer({ action: 'use_item', item_id: itemId });
        dispatch({type: 'CLEAR_SELECTED_INVENTORY_ITEM'}); // Clear selection after attempting use
    } else {
        dispatch({ type: 'SET_GAME_MESSAGE', payload: {text: "Error: Cannot send 'use item' action to server.", isError: true, duration: 0}});
    }
  }, [sendMessageToServer, state.isGameOver]);

  const attemptEquipItem = useCallback((itemId) => {
    if (state.isGameOver) {
      dispatch({ type: 'SET_GAME_MESSAGE', payload: { text: "Game Over. Cannot equip items.", isError: true, duration: 0 }});
      return;
    }
     if (!itemId) {
        dispatch({ type: 'SET_GAME_MESSAGE', payload: {text: "No item selected to equip.", isError: true, duration: 3000}});
        return;
    }
    if (sendMessageToServer) {
        console.log(`[useGameState] Attempting to equip item with ID: ${itemId}`);
        sendMessageToServer({ action: 'equip_item', item_id: itemId });
        dispatch({type: 'CLEAR_SELECTED_INVENTORY_ITEM'}); // Clear selection
    } else {
        dispatch({ type: 'SET_GAME_MESSAGE', payload: {text: "Error: Cannot send 'equip item' action to server.", isError: true, duration: 0}});
    }
  }, [sendMessageToServer, state.isGameOver]);

  const attemptUnequipItem = useCallback((slot) => {
    if (state.isGameOver) {
      dispatch({ type: 'SET_GAME_MESSAGE', payload: { text: "Game Over. Cannot unequip items.", isError: true, duration: 0 }});
      return;
    }
    if (!slot || !state.playerStats.equipment[slot]) {
        dispatch({ type: 'SET_GAME_MESSAGE', payload: {text: `Nothing equipped in ${slot} slot.`, isError: true, duration: 3000}});
        return;
    }
    if (sendMessageToServer) {
        console.log(`[useGameState] Attempting to unequip from slot: ${slot}`);
        sendMessageToServer({ action: 'unequip_item', slot: slot });
    } else {
        dispatch({ type: 'SET_GAME_MESSAGE', payload: {text: "Error: Cannot send 'unequip item' action to server.", isError: true, duration: 0}});
    }
  }, [sendMessageToServer, state.isGameOver, state.playerStats.equipment]);

  const selectInventoryItem = useCallback((index) => {
      dispatch({ type: 'SELECT_INVENTORY_ITEM', payload: index });
  }, []);


  return {
    dungeonMap: state.dungeonMap, playerPos: state.playerPos, tileDefinitions: state.tileDefinitions,
    gameMessage: state.gameMessage, isLoading: state.isLoading, playerStats: state.playerStats,
    monsters: state.monsters, isGameOver: state.isGameOver,
    currentDungeonLevel: state.currentDungeonLevel,
    inventory: state.playerStats.inventory, // Expose inventory
    equipment: state.playerStats.equipment, // Expose equipment
    selectedInventoryItemIndex: state.selectedInventoryItemIndex, // Expose selection
    requestNewDungeonGeneration, attemptPlayerMove, 
    attemptUseItem, attemptEquipItem, attemptUnequipItem, // New actions
    selectInventoryItem, // For UI interaction
  };
}