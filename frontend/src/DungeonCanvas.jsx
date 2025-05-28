// frontend/src/DungeonCanvas.jsx
import React, { useRef, useEffect } from 'react';
import GoblinSprite from './components/sprites/GoblinSprite'; 
import OrcSprite from './components/sprites/OrcSprite';
import SkeletonSprite from './components/sprites/SkeletonSprite';
// Import PlayerSprite when you create it
// import PlayerSprite from '../../components/sprites/PlayerSprite'; 

const TILE_SIZE = 20; 

// ... (colors and getSpriteClass remain the same)
const getSpriteClass = (entityTypeOrPlayer, entityTileId, tileDefinitions) => {
  if (entityTypeOrPlayer === 'player') return 'sprite-player';
  if (tileDefinitions && entityTileId === tileDefinitions.MONSTER_GOBLIN) return 'sprite-goblin';
  if (tileDefinitions && entityTileId === tileDefinitions.MONSTER_ORC) return 'sprite-orc';
  if (tileDefinitions && entityTileId === tileDefinitions.MONSTER_SKELETON) return 'sprite-skeleton';
  return 'sprite-default'; 
};


const DungeonCanvas = ({ dungeonMap, playerPos, monsters, tileDefinitions }) => {
  const canvasRef = useRef(null);

  useEffect(() => { // Canvas drawing logic for map background + items
    // ... (this part should be fine, as it was working)
    if (!dungeonMap || !dungeonMap.length || !dungeonMap[0] || !canvasRef.current || !tileDefinitions || !tileDefinitions.hasOwnProperty('FLOOR')) {
      return;
    }
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const mapHeight = dungeonMap.length;
    const mapWidth = dungeonMap[0].length;
    canvas.width = mapWidth * TILE_SIZE;
    canvas.height = mapHeight * TILE_SIZE;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    for (let y = 0; y < mapHeight; y++) {
      for (let x = 0; x < mapWidth; x++) {
        const tileId = dungeonMap[y][x]; 
        let colorToFill;
        if (tileId === tileDefinitions.FOG) colorToFill = '#1a1a1a';
        else if (tileId === tileDefinitions.FLOOR) colorToFill = '#888';
        else if (tileId === tileDefinitions.WALL) colorToFill = '#333';
        else if (tileId === tileDefinitions.DOOR_CLOSED) colorToFill = 'saddlebrown';
        else if (tileId === tileDefinitions.DOOR_OPEN) colorToFill = 'peru';
        else if (tileId === tileDefinitions.STAIRS_DOWN) colorToFill = 'purple';
        else if (tileId === tileDefinitions.ITEM_POTION) colorToFill = 'lightblue';
        else if (tileId === tileDefinitions.ITEM_SCROLL_TELEPORT) colorToFill = 'lightyellow';
        else if (tileId === tileDefinitions.EMPTY) colorToFill = '#000';
        else colorToFill = '#888'; // Default to floor
        ctx.fillStyle = colorToFill;
        ctx.fillRect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE);
        if (tileId !== tileDefinitions.FOG) {
            if (tileId === tileDefinitions.DOOR_CLOSED) { ctx.fillStyle = 'black'; ctx.fillRect(x*TILE_SIZE + TILE_SIZE*0.7, y*TILE_SIZE + TILE_SIZE*0.4, TILE_SIZE*0.15, TILE_SIZE*0.2); }
            else if (tileId === tileDefinitions.DOOR_OPEN) { ctx.fillStyle = 'rgba(0,0,0,0.1)'; ctx.fillRect(x*TILE_SIZE, y*TILE_SIZE, TILE_SIZE, TILE_SIZE); }
            else if (tileId === tileDefinitions.STAIRS_DOWN) { ctx.fillStyle = 'black'; for(let i=0;i<4;i++){ ctx.fillRect(x*TILE_SIZE + TILE_SIZE*0.2, y*TILE_SIZE + (i*TILE_SIZE*0.25)+TILE_SIZE*0.05, TILE_SIZE*0.6, TILE_SIZE*0.1); } ctx.beginPath(); ctx.moveTo(x*TILE_SIZE+TILE_SIZE*0.5, y*TILE_SIZE+TILE_SIZE*0.85); ctx.lineTo(x*TILE_SIZE+TILE_SIZE*0.3, y*TILE_SIZE+TILE_SIZE*0.65); ctx.lineTo(x*TILE_SIZE+TILE_SIZE*0.7, y*TILE_SIZE+TILE_SIZE*0.65); ctx.closePath(); ctx.fill(); }
            else if (tileId === tileDefinitions.ITEM_SCROLL_TELEPORT) { ctx.fillStyle = 'rgba(0,0,0,0.5)'; ctx.font = `${TILE_SIZE*0.6}px sans-serif`; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText('S', x*TILE_SIZE + TILE_SIZE/2, y*TILE_SIZE + TILE_SIZE/2 + 1); }
            else if (tileId === tileDefinitions.ITEM_POTION) { ctx.fillStyle = 'rgba(200,0,0,0.7)'; ctx.font = `${TILE_SIZE*0.6}px sans-serif`; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText('P', x*TILE_SIZE + TILE_SIZE/2, y*TILE_SIZE + TILE_SIZE/2 + 1); }
        }
      }
    }
  }, [dungeonMap, tileDefinitions]); 

  const visibleMonsters = (monsters || []).filter(monster => {
    if (!dungeonMap || !dungeonMap[monster.y] || dungeonMap[monster.y][monster.x] === undefined || !tileDefinitions || tileDefinitions.FOG === undefined) return false; 
    return dungeonMap[monster.y][monster.x] !== tileDefinitions.FOG;
  });

  const isPlayerVisible = playerPos && dungeonMap && dungeonMap.length > playerPos.y && dungeonMap[playerPos.y] && dungeonMap[playerPos.y].length > playerPos.x && dungeonMap[playerPos.y][playerPos.x] !== undefined && tileDefinitions && tileDefinitions.FOG !== undefined && dungeonMap[playerPos.y][playerPos.x] !== tileDefinitions.FOG;

  return (
    <div 
        className="dungeon-container" 
        style={{ 
            position: 'relative', 
            width: dungeonMap && dungeonMap[0] ? dungeonMap[0].length * TILE_SIZE : 0, 
            height: dungeonMap ? dungeonMap.length * TILE_SIZE : 0,
            border: '1px solid black'
        }}
    >
      <canvas ref={canvasRef} />
      
      {visibleMonsters.map(monster => (
        <div
          key={monster.id}
          className={`game-sprite ${getSpriteClass(monster.type, monster.tile_id, tileDefinitions)}`}
          style={{
            left: `${monster.x * TILE_SIZE}px`,
            top: `${monster.y * TILE_SIZE}px`,
            width: `${TILE_SIZE}px`,
            height: `${TILE_SIZE}px`,
            ['--tile-size']: `${TILE_SIZE}px` 
          }}
          aria-label={monster.type} 
          role="img" 
        >
          {/* Render specific sprite component based on type */}
          {tileDefinitions && monster.tile_id === tileDefinitions.MONSTER_GOBLIN && <GoblinSprite />}
          {tileDefinitions && monster.tile_id === tileDefinitions.MONSTER_ORC && <OrcSprite />}
          {tileDefinitions && monster.tile_id === tileDefinitions.MONSTER_SKELETON && <SkeletonSprite />}
        </div>
      ))}

      {isPlayerVisible && playerPos && (
        <div
          className={`game-sprite sprite-player`} 
          style={{
            left: `${playerPos.x * TILE_SIZE}px`,
            top: `${playerPos.y * TILE_SIZE}px`,
            width: `${TILE_SIZE}px`,
            height: `${TILE_SIZE}px`,
            ['--tile-size']: `${TILE_SIZE}px` 
          }}
          aria-label="Player"
          role="img"
        >
          {/* <PlayerSprite />  // Or directly use spans if PlayerSprite is not created yet */}
          <span className="knight-component knight-helmet"></span>
          <span className="knight-component knight-torso"></span>
          <span className="knight-component knight-shield"></span>
          <span className="knight-component knight-sword"></span>
        </div>
      )}
    </div>
  );
};

export default DungeonCanvas;