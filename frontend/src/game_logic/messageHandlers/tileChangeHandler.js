// frontend/src/game_logic/messageHandlers/tileChangeHandler.js

export function handleTileChange(currentState, message) {
  console.log("[handleTileChange] START. currentState.monsters:", currentState.monsters, "Message:", message); // DEBUG

  let newDungeonMap = currentState.dungeonMap; 

  if (currentState.dungeonMap && message.pos && message.hasOwnProperty('new_tile_type')) {
    const { x: changeX, y: changeY } = message.pos;
    const newTile = message.new_tile_type;

    newDungeonMap = currentState.dungeonMap.map((row, rowIndex) => {
      if (rowIndex === changeY) {
          const newRow = [...row];
          if (changeX >= 0 && changeX < newRow.length) newRow[changeX] = newTile;
          return newRow;
      }
      return row;
    });
  } else {
    console.warn("[tileChangeHandler] Skipped update due to missing data.", { mapExists: !!currentState.dungeonMap, msg: message });
  }
  
  const newState = { ...currentState, dungeonMap: newDungeonMap };
  console.log("[handleTileChange] END. newState.monsters:", newState.monsters); // DEBUG
  return newState;
}