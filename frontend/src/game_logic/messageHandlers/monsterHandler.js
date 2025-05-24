// frontend/src/game_logic/messageHandlers/monsterHandler.js

export function handleMonsterMoved(currentState, message) {
  // console.log("[handleMonsterMoved] START. currentState.monsters:", currentState.monsters, "Message:", message); 

  let newMonsters = currentState.monsters; 
  if (currentState.monsters && Array.isArray(currentState.monsters)) {
    newMonsters = currentState.monsters.map(m => {
      if (m.id === message.monster_id) {
        return { ...m, x: message.new_pos.x, y: message.new_pos.y };
      }
      return m;
    });
  } else {
    console.warn("[handleMonsterMoved] currentState.monsters was not an array or was null/undefined.", currentState.monsters);
    newMonsters = []; 
  }
  
  const newState = { ...currentState, monsters: newMonsters };
  // console.log("[handleMonsterMoved] END. newState.monsters:", newState.monsters); 
  return newState;
}

export function handleMonsterAppeared(currentState, message) {
  console.log("[handleMonsterAppeared] Received new monster:", message.monster_info);
  // Add the new monster to the list, avoiding duplicates if it somehow already exists
  const monsterExists = currentState.monsters.some(m => m.id === message.monster_info.id);
  if (monsterExists) {
    console.warn(`[handleMonsterAppeared] Monster ${message.monster_info.id} already exists. Updating instead.`);
    // Optionally, update existing monster data if it might have changed, though MonsterAppeared usually implies new.
    const updatedMonsters = currentState.monsters.map(m => 
      m.id === message.monster_info.id ? message.monster_info : m
    );
    return { ...currentState, monsters: updatedMonsters };
  } else {
    return { 
      ...currentState, 
      monsters: [...currentState.monsters, message.monster_info] 
    };
  }
}