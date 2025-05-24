// No React needed here, it's a pure utility function

export function checkMapConnectivity(mapData, startX, startY, tileDefs) {
  if (!mapData || !mapData.length || !mapData[0] || !tileDefs || !tileDefs.hasOwnProperty('FLOOR')) {
    console.warn("Connectivity Check (mapUtils): Invalid input data (map, start, or tileDefs).");
    return true; // Or false, depending on how you want to handle bad input
  }
  
  const height = mapData.length;
  const width = mapData[0].length;
  
  if (!(startX >= 0 && startX < width && startY >= 0 && startY < height)) {
    console.error("Connectivity Check (mapUtils): Start position is out of bounds!");
    return false;
  }
  // It's okay if start isn't floor for the check, BFS will just not explore from it initially if so.
  // But it's better if it is floor.
  if (mapData[startY][startX] !== tileDefs.FLOOR) {
    console.warn(`Connectivity Check (mapUtils): Start position (${startX},${startY}) is not on a FLOOR tile (it's ${mapData[startY][startX]}). May give inaccurate results if no other floor is reachable.`);
  }

  const visited = Array(height).fill(null).map(() => Array(width).fill(false));
  const q = [];
  
  if (startX >= 0 && startX < width && startY >= 0 && startY < height) {
      // Only start BFS if the start tile is actually floor
      if(mapData[startY][startX] === tileDefs.FLOOR) {
        q.push([startX, startY]);
        visited[startY][startX] = true;
      } else {
        // If start is not floor, we can't start BFS from there.
        // This implies either a bad start_pos or a map with no floor at start.
        // The check will likely fail if there's other floor, which is correct.
      }
  } else {
      console.error("Connectivity Check (mapUtils): Start position invalid, cannot begin BFS.");
      return false;
  }

  let reachableFloorCount = 0;
  let totalFloorTilesInMap = 0;

  for (let r = 0; r < height; r++) {
    for (let c = 0; c < width; c++) {
      if (mapData[r][c] === tileDefs.FLOOR) {
        totalFloorTilesInMap++;
      }
    }
  }

  if (totalFloorTilesInMap === 0) {
    console.log("Connectivity Check (mapUtils): No floor tiles in the map.");
    return true; // Vacuously connected
  }
  
  // If queue is empty (e.g. start wasn't floor), and there IS floor elsewhere, it's disconnected
  if (q.length === 0 && totalFloorTilesInMap > 0) {
      console.log("Connectivity Check (mapUtils): Start tile not floor, and other floor exists. Likely disconnected.");
      return false;
  }


  let head = 0;
  while(head < q.length){
      const [x,y] = q[head++];

      // Current tile (x,y) is already confirmed to be floor and part of the queue
      reachableFloorCount++;

      const neighbors = [[0, 1], [0, -1], [1, 0], [-1, 0]];
      for (const [dx, dy] of neighbors) {
          const nx = x + dx;
          const ny = y + dy;
          if (nx >= 0 && nx < width && ny >= 0 && ny < height &&
              !visited[ny][nx] && mapData[ny][nx] === tileDefs.FLOOR) {
              visited[ny][nx] = true;
              q.push([nx, ny]);
          }
      }
  }
  
  console.log(`Connectivity Check (mapUtils): Total floor tiles: ${totalFloorTilesInMap}, Reachable floor from start: ${reachableFloorCount}`);
  
  return reachableFloorCount >= totalFloorTilesInMap;
}