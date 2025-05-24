// frontend/src/DungeonCanvas.jsx
import React, { useRef, useEffect } from 'react';

const TILE_SIZE = 20;
const PLAYER_COLOR = 'red';
const FLOOR_COLOR = '#888'; 
const WALL_COLOR = '#333';
const EMPTY_COLOR = '#000'; 
const POTION_COLOR = 'lightblue';
const SCROLL_TELEPORT_COLOR = 'lightyellow';
const GOBLIN_COLOR = 'lightgreen'; 
const ORC_COLOR = 'darkgreen'; 
const SKELETON_COLOR = 'ivory'; 
const DOOR_CLOSED_COLOR = 'saddlebrown';
const DOOR_OPEN_COLOR = 'peru'; 
const STAIRS_DOWN_COLOR = 'purple'; 
const FOG_COLOR = '#1a1a1a'; 

const DungeonCanvas = ({ dungeonMap, playerPos, monsters, tileDefinitions }) => {
  const canvasRef = useRef(null);

  useEffect(() => {
    // Removed most debug logs for cleanup
    // if(tileDefinitions) {
    //     console.log("[DungeonCanvas useEffect] tileDefinitions.FOG value:", tileDefinitions.FOG);
    // }

    if (!dungeonMap || !dungeonMap.length || !dungeonMap[0] || !playerPos || !canvasRef.current || !tileDefinitions || !tileDefinitions.hasOwnProperty('FLOOR')) {
      return;
    }

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    const mapHeight = dungeonMap.length;
    const mapWidth = dungeonMap[0].length;

    canvas.width = mapWidth * TILE_SIZE;
    canvas.height = mapHeight * TILE_SIZE;
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // 1. Draw map tiles
    for (let y = 0; y < mapHeight; y++) {
      for (let x = 0; x < mapWidth; x++) {
        const tileId = dungeonMap[y][x]; 
        let colorToFill;

        if (tileId === tileDefinitions.FOG) {
          colorToFill = FOG_COLOR;
        } else if (tileId === tileDefinitions.FLOOR) {
          colorToFill = FLOOR_COLOR;
        } else if (tileId === tileDefinitions.WALL) {
          colorToFill = WALL_COLOR;
        } else if (tileId === tileDefinitions.DOOR_CLOSED) {
          colorToFill = DOOR_CLOSED_COLOR;
        } else if (tileId === tileDefinitions.DOOR_OPEN) {
          colorToFill = DOOR_OPEN_COLOR;
        } else if (tileId === tileDefinitions.STAIRS_DOWN) {
          colorToFill = STAIRS_DOWN_COLOR;
        } else if (tileId === tileDefinitions.ITEM_POTION) {
          colorToFill = POTION_COLOR;
        } else if (tileId === tileDefinitions.ITEM_SCROLL_TELEPORT) {
          colorToFill = SCROLL_TELEPORT_COLOR;
        } else if (tileId === tileDefinitions.EMPTY) { 
          colorToFill = EMPTY_COLOR;
        } else {
          // Fallback for any other revealed tile ID: render as floor
          colorToFill = FLOOR_COLOR; 
          // console.warn(`[DungeonCanvas] Unrecognized tile ID ${tileId} at (${x},${y}) for background. Rendering as floor.`);
        }
        
        ctx.fillStyle = colorToFill;
        ctx.fillRect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE);

        if (tileId !== tileDefinitions.FOG) {
            if (tileId === tileDefinitions.DOOR_CLOSED) { 
                ctx.fillStyle = 'black'; 
                ctx.fillRect(x * TILE_SIZE + TILE_SIZE * 0.7, y * TILE_SIZE + TILE_SIZE * 0.4, TILE_SIZE * 0.15, TILE_SIZE * 0.2);
            } else if (tileId === tileDefinitions.DOOR_OPEN) { 
                ctx.fillStyle = 'rgba(0,0,0,0.2)'; 
                ctx.fillRect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE);
            } else if (tileId === tileDefinitions.STAIRS_DOWN) { 
                ctx.fillStyle = 'black'; 
                for (let i = 0; i < 4; i++) {
                    ctx.fillRect(x * TILE_SIZE + TILE_SIZE * 0.2, y * TILE_SIZE + (i * TILE_SIZE * 0.25) + TILE_SIZE * 0.05, TILE_SIZE*0.6, TILE_SIZE*0.1);
                }
                ctx.beginPath();
                ctx.moveTo(x * TILE_SIZE + TILE_SIZE * 0.5, y * TILE_SIZE + TILE_SIZE * 0.85);
                ctx.lineTo(x * TILE_SIZE + TILE_SIZE * 0.3, y * TILE_SIZE + TILE_SIZE * 0.65);
                ctx.lineTo(x * TILE_SIZE + TILE_SIZE * 0.7, y * TILE_SIZE + TILE_SIZE * 0.65);
                ctx.closePath(); ctx.fill();
            } else if (tileId === tileDefinitions.ITEM_SCROLL_TELEPORT) { 
                ctx.fillStyle = 'rgba(0,0,0,0.5)'; ctx.font = `${TILE_SIZE * 0.6}px sans-serif`;
                ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
                ctx.fillText('S', x * TILE_SIZE + TILE_SIZE / 2, y * TILE_SIZE + TILE_SIZE / 2 + 1);
            } else if (tileId === tileDefinitions.ITEM_POTION) { 
                 ctx.fillStyle = 'rgba(200,0,0,0.7)'; ctx.font = `${TILE_SIZE * 0.6}px sans-serif`;
                ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
                ctx.fillText('P', x * TILE_SIZE + TILE_SIZE / 2, y * TILE_SIZE + TILE_SIZE / 2 +1);
            }
        }
      }
    }

    // 2. Draw monsters
    if (monsters && monsters.length > 0 && tileDefinitions && tileDefinitions.FOG !== undefined) {
      monsters.forEach(monster => {
        const tileValueAtMonster = (dungeonMap[monster.y] && dungeonMap[monster.y][monster.x] !== undefined) 
                                   ? dungeonMap[monster.y][monster.x] : 'OOB';
        const isVisibleTile = tileValueAtMonster !== tileDefinitions.FOG && tileValueAtMonster !== 'OOB';

        // Per-monster debug log - can be re-enabled if needed
        // console.log(
        //    `[DungeonCanvas] Monster ${monster.type} (ID ${monster.tile_id}) at (${monster.x},${monster.y}). ` +
        //    `TileValue: ${tileValueAtMonster}. IsVisibleCond: ${isVisibleTile}. ` + 
        //    `tileDefs.FOG: ${tileDefinitions.FOG}`
        // );

        if (isVisibleTile) {
          let monsterColor = 'magenta'; let monsterChar = 'X';   
          if (monster.tile_id === tileDefinitions.MONSTER_GOBLIN) {
            monsterColor = GOBLIN_COLOR; monsterChar = 'g';
          } else if (monster.tile_id === tileDefinitions.MONSTER_ORC) {
            monsterColor = ORC_COLOR; monsterChar = 'O';
          } else if (monster.tile_id === tileDefinitions.MONSTER_SKELETON) {
            monsterColor = SKELETON_COLOR; monsterChar = 'S'; 
          } 
          // else { // Warning for unrecognized monster tile_id can be noisy if defaults are acceptable
          //   console.warn(`[DungeonCanvas] Monster ${monster.type} (tile_id ${monster.tile_id}) no match for color/char.`);
          // }
          
          ctx.fillStyle = monsterColor;
          ctx.beginPath();
          ctx.arc(monster.x * TILE_SIZE + TILE_SIZE / 2, monster.y * TILE_SIZE + TILE_SIZE / 2, TILE_SIZE / 2.5, 0, 2 * Math.PI);
          ctx.fill(); 
          ctx.fillStyle = 'black'; ctx.font = `bold ${TILE_SIZE * 0.65}px monospace`; 
          ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
          ctx.fillText(monsterChar, monster.x * TILE_SIZE + TILE_SIZE / 2, monster.y * TILE_SIZE + TILE_SIZE / 2 + 1);
        }
      });
    }

    // 3. Draw player 
    if (playerPos && dungeonMap[playerPos.y] && dungeonMap[playerPos.y][playerPos.x] !== undefined && 
        dungeonMap[playerPos.y][playerPos.x] !== tileDefinitions.FOG) { 
        ctx.fillStyle = PLAYER_COLOR;
        ctx.beginPath();
        ctx.arc( playerPos.x * TILE_SIZE + TILE_SIZE / 2, playerPos.y * TILE_SIZE + TILE_SIZE / 2, TILE_SIZE / 3, 0, 2 * Math.PI);
        ctx.fill();
        ctx.fillStyle = 'white'; ctx.font = `bold ${TILE_SIZE * 0.6}px monospace`;
        ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
        ctx.fillText('@', playerPos.x * TILE_SIZE + TILE_SIZE / 2, playerPos.y * TILE_SIZE + TILE_SIZE / 2 + 1);
    }

  }, [dungeonMap, playerPos, monsters, tileDefinitions]);

  return <canvas ref={canvasRef} style={{ border: '1px solid black' }} />;
};

export default DungeonCanvas;