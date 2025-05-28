// frontend/src/App.jsx
import React, { useState, useEffect, useCallback, useRef } from 'react';
import DungeonCanvas from './DungeonCanvas';
import { useGameWebSocket } from './hooks/useGameWebSocket';
import { useGameState } from './hooks/useGameState';
import './App.css';
import './components/sprites/sprites.css';

function App() {
  const { isConnected, messageBatch, sendMessage, error: wsError } = useGameWebSocket();
  const {
    dungeonMap, playerPos, tileDefinitions, 
    gameMessage, isLoading, 
    playerStats, 
    inventory, equipment, 
    monsters, 
    isGameOver, 
    currentDungeonLevel,
    selectedInventoryItemIndex, 
    requestNewDungeonGeneration, attemptPlayerMove,
    attemptUseItem, attemptEquipItem, attemptUnequipItem, 
    selectInventoryItem,
  } = useGameState(messageBatch, sendMessage);

  const [inputSeed, setInputSeed] = useState('');
  const [initialSeed] = useState(Math.floor(Math.random() * 100000));
  const initialDungeonRequestedRef = useRef(false);

  useEffect(() => {
    if (isConnected && !initialDungeonRequestedRef.current) {
      initialDungeonRequestedRef.current = true; 
      const seedValueFromInput = inputSeed.trim();
      let seedToUse = seedValueFromInput ? (isNaN(parseInt(seedValueFromInput,10)) ? initialSeed : parseInt(seedValueFromInput,10)) : initialSeed;
      requestNewDungeonGeneration(seedToUse, false); 
    }
  }, [isConnected, requestNewDungeonGeneration, initialSeed, inputSeed]); 

  const handleGenerateDungeon = () => {
    if (isLoading && !isGameOver) return; 
    let newSeedValue = parseInt(inputSeed, 10);
    if (isNaN(newSeedValue) || inputSeed.trim() === "") newSeedValue = Math.floor(Math.random() * 100000);
    setInputSeed(newSeedValue.toString());
    initialDungeonRequestedRef.current = true; 
    requestNewDungeonGeneration(newSeedValue, false); 
  };

  const handleKeyDown = useCallback((event) => {
    if (isGameOver) {
        if (event.key === 'Enter' || event.key.toLowerCase() === 'r') handleGenerateDungeon();
        return;
    }
    if (isLoading || !isConnected) return;

    if (event.key >= '1' && event.key <= '9') {
        const itemIndex = parseInt(event.key, 10) - 1;
        if (inventory && itemIndex < inventory.length) {
            selectInventoryItem(itemIndex);
            event.preventDefault(); return;
        }
    }
    
    if (event.key.toLowerCase() === 'u') { 
        if (selectedInventoryItemIndex !== null && inventory && inventory[selectedInventoryItemIndex]) {
            attemptUseItem(inventory[selectedInventoryItemIndex].id);
            event.preventDefault(); return;
        } else if (inventory && inventory.length > 0 && selectedInventoryItemIndex === null){
            const firstConsumable = inventory.find(item => item.consumable);
            if (firstConsumable) attemptUseItem(firstConsumable.id);
            else selectInventoryItem(0); 
            event.preventDefault(); return;
        }
    }

    if (event.key.toLowerCase() === 'e') { 
         if (selectedInventoryItemIndex !== null && inventory && inventory[selectedInventoryItemIndex]) {
            if (inventory[selectedInventoryItemIndex].equippable) {
                attemptEquipItem(inventory[selectedInventoryItemIndex].id);
            }
            event.preventDefault(); return;
        } else if (inventory && inventory.length > 0 && selectedInventoryItemIndex === null){
            const firstEquippable = inventory.find(item => item.equippable);
            if (firstEquippable) attemptEquipItem(firstEquippable.id);
            else selectInventoryItem(0);
            event.preventDefault(); return;
        }
    }
    if (event.shiftKey && event.key.toLowerCase() === 'w') { 
        if (equipment && equipment.weapon) {
            attemptUnequipItem('weapon');
            event.preventDefault(); return;
        }
    }
    if (event.shiftKey && event.key.toLowerCase() === 'a') { 
        if (equipment && equipment.armor) {
            attemptUnequipItem('armor');
            event.preventDefault(); return;
        }
    }

    if (!dungeonMap || !playerPos) return;
    let intendedX = playerPos.x, intendedY = playerPos.y, moveAttempted = false;
    switch (event.key) {
        case 'ArrowUp': case 'w': case 'W': intendedY -= 1; moveAttempted = true; break;
        case 'ArrowDown': case 's': case 'S': intendedY += 1; moveAttempted = true; break;
        case 'ArrowLeft': case 'a': case 'A': intendedX -= 1; moveAttempted = true; break;
        case 'ArrowRight': case 'd': case 'D': intendedX += 1; moveAttempted = true; break;
        default: 
            if(!event.shiftKey && !event.ctrlKey && !event.altKey && !(event.key >= '0' && event.key <= '9')) return;
            break; 
    }
    if (moveAttempted) { event.preventDefault(); attemptPlayerMove(intendedX, intendedY); }
  }, [isLoading, dungeonMap, playerPos, attemptPlayerMove, isConnected, isGameOver, handleGenerateDungeon, 
      inventory, equipment, selectedInventoryItemIndex, selectInventoryItem, 
      attemptUseItem, attemptEquipItem, attemptUnequipItem]);


  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  const uiShouldBeDisabled = isLoading || (!isConnected && !wsError);

  // ADD THIS LOG:
  console.log("[App.jsx] Rendering. isLoading:", isLoading, "monsters prop to pass:", monsters);

  return (
    <div className="App">
      <header className="App-header">
        <h1>Roguelike Dungeon Crawler</h1>
        <div className="controls">
          <label htmlFor="seedInput">Seed: </label>
          <input type="text" id="seedInput" value={inputSeed} onChange={(e) => setInputSeed(e.target.value)} disabled={uiShouldBeDisabled}/>
          <button onClick={handleGenerateDungeon} disabled={uiShouldBeDisabled}>
            {(uiShouldBeDisabled && !isGameOver) ? 'Working...' : (isGameOver ? 'New Game' : 'Generate Dungeon')}
          </button>
        </div>
        <div className="dungeon-level-display">Dungeon Level: {currentDungeonLevel}</div>
      </header>

      <main className="App-main">
        <div className="game-area">
          {playerStats && playerPos && !isGameOver && (
            <div className="player-stats-display">
              HP: {playerStats.hp}/{playerStats.max_hp} | ATK: {playerStats.attack} | DEF: {playerStats.defense}
              <br />
              Level: {playerStats.level} | XP: {playerStats.xp}/{playerStats.xp_to_next_level}
            </div>
          )}

          <div className="game-message-area" 
            style={{ minHeight: '20px', padding: '5px', marginTop: '10px', marginBottom: '10px', border: gameMessage.text ? '1px solid #555' : '1px solid transparent', backgroundColor: gameMessage.isError ? '#502020' : (gameMessage.text ? '#203020' : 'transparent'), color: gameMessage.isError ? 'orange' : 'lightgreen', visibility: gameMessage.text || wsError || (!isConnected && uiShouldBeDisabled && !isLoading) ? 'visible' : 'hidden' }}>
            {wsError ? `Connection Error: ${wsError}` : (!isConnected && uiShouldBeDisabled ? "Connecting..." : (gameMessage.text ? gameMessage.text : (isConnected && !isLoading ? "Connected." : "")))}
            {isLoading && !wsError && !gameMessage.text && "Loading dungeon data..."}
          </div>
          
          {dungeonMap && playerPos && isConnected && !isGameOver ? (
            <DungeonCanvas 
              dungeonMap={dungeonMap} 
              playerPos={playerPos} 
              monsters={monsters} 
              tileDefinitions={tileDefinitions} 
            />
          ) : (
            <p className="loading-message">
              {uiShouldBeDisabled && !wsError ? "Loading..." : (wsError ? "Connection failed." : (!isConnected ? "Disconnected." : (isGameOver ? "Game Over." : "No dungeon.")))}
            </p>
          )}
        </div>

        {!isGameOver && playerStats && (
          <aside className="sidebar">
            <div className="equipment-display">
              <h3>Equipment</h3>
              <div>Weapon: {equipment?.weapon ? `${equipment.weapon.name} (ATK +${equipment.weapon.attack_bonus || 0})` : 'None'} 
                   {equipment?.weapon && <button onClick={() => attemptUnequipItem('weapon')} title="Unequip (Shift+W)">X</button>}
              </div>
              <div>Armor: {equipment?.armor ? `${equipment.armor.name} (DEF +${equipment.armor.defense_bonus || 0})` : 'None'}
                   {equipment?.armor && <button onClick={() => attemptUnequipItem('armor')} title="Unequip (Shift+A)">X</button>}
              </div>
            </div>

            <div className="inventory-display">
              <h3>Inventory ({inventory?.length || 0} items)</h3>
              {inventory && inventory.length > 0 ? (
                <ul>
                  {inventory.map((item, index) => (
                    <li key={item.id} 
                        className={selectedInventoryItemIndex === index ? 'selected-item' : ''}
                        onClick={() => selectInventoryItem(index)}
                        title={item.description || item.name} >
                      {index + 1}. {item.name} {item.quantity > 1 ? `(x${item.quantity})` : ''}
                      {selectedInventoryItemIndex === index && (
                        <span className="item-actions">
                          {item.consumable && <button onClick={(e) => {e.stopPropagation(); attemptUseItem(item.id);}} title="Use (U)">Use</button>}
                          {item.equippable && <button onClick={(e) => {e.stopPropagation(); attemptEquipItem(item.id);}} title="Equip (E)">Equip</button>}
                        </span>
                      )}
                    </li>
                  ))}
                </ul>
              ) : <p>Empty</p>}
            </div>
          </aside>
        )}
      </main>
      
      <footer className="App-footer">
        <div className="instructions"> 
          <p>Arrows/WASD: Move. Number keys (1-9): Select item. 'U': Use selected. 'E': Equip selected. Shift+W/A: Unequip Weapon/Armor. {isGameOver ? "'R'/Enter for New Game." : ""}</p>
        </div>
      </footer>
    </div>
  );
}
export default App;