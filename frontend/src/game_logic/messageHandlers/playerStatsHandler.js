// frontend/src/game_logic/messageHandlers/playerStatsHandler.js
export function handlePlayerStatsUpdate(currentState, message) {
  // The message.stats object from the server now includes:
  // hp, max_hp, attack, defense, level, xp, xp_to_next_level,
  // inventory: List[InventoryItemDetail],
  // equipment: Dict[str, Optional[InventoryItemDetail]]
  // console.log("[playerStatsHandler] Updating player stats:", message.stats);
  return { ...currentState, playerStats: message.stats };
}