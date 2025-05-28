# backend/app/core/map_manager.py
from typing import Any, Dict, List, Optional, Tuple, Set, TYPE_CHECKING
import math
from collections import deque

from .tiles import (
    TILE_FLOOR, TILE_WALL, TILE_EMPTY, TILE_DOOR_CLOSED, TILE_DOOR_OPEN,
    TILE_FOG, TILE_ITEM_POTION, TILE_ITEM_SCROLL_TELEPORT, TILE_STAIRS_DOWN
)
from . import config as game_config
from .. import schemas

if TYPE_CHECKING:
    from .game_state import GameState 
    from .dungeon_generator import Room
    from .entity_manager import EntityManager
    from .player import Player # For player_pos type hint

class MapManager:
    def __init__(self, logger_parent_name: str = "MapManager"):
        self.actual_dungeon_map: Optional[List[List[int]]] = None
        self.dungeon_map_for_client: Optional[List[List[int]]] = None
        self.generated_rooms: List['Room'] = []
        self.visited_room_indices: Set[int] = set() 
        self.ever_revealed_tiles: Set[Tuple[int, int]] = set()
        # self.logger = logging.getLogger(logger_parent_name)

    def initialize_maps(self, actual_map: List[List[int]], client_map_width: int, client_map_height: int):
        self.actual_dungeon_map = actual_map
        self.dungeon_map_for_client = [[TILE_FOG for _ in range(client_map_width)] for _ in range(client_map_height)]
        self.visited_room_indices.clear()
        self.ever_revealed_tiles.clear()

    def set_generated_rooms(self, rooms: List['Room']):
        self.generated_rooms = rooms

    def get_room_at_pos(self, x: int, y: int) -> Optional[Tuple[int, 'Room']]:
        for i, room in enumerate(self.generated_rooms):
            if room.x1 <= x <= room.x2 and room.y1 <= y <= room.y2:
                return i, room
        return None

    def reveal_room_and_connected_corridors(self, room_index: int, gs: 'GameState') -> List[schemas.TileChangeServerResponse]:
        responses: List[schemas.TileChangeServerResponse] = [] 
        if not self.actual_dungeon_map or not self.dungeon_map_for_client or room_index >= len(self.generated_rooms):
            return responses
        if room_index in self.visited_room_indices:
            return responses
        
        self.visited_room_indices.add(room_index)
        room_to_reveal = self.generated_rooms[room_index]
        
        for y_coord in range(room_to_reveal.y1, room_to_reveal.y2 + 1):
            for x_coord in range(room_to_reveal.x1, room_to_reveal.x2 + 1):
                if 0 <= y_coord < len(self.actual_dungeon_map) and 0 <= x_coord < len(self.actual_dungeon_map[0]):
                    self.ever_revealed_tiles.add((x_coord, y_coord))
        
        q_corridor_reveal: deque[Tuple[int, int]] = deque()
        for y_r in range(room_to_reveal.y1 - 1, room_to_reveal.y2 + 2):
            for x_r in range(room_to_reveal.x1 - 1, room_to_reveal.x2 + 2):
                if not (0 <= y_r < len(self.actual_dungeon_map) and 0 <= x_r < len(self.actual_dungeon_map[0])): continue
                if room_to_reveal.is_inside(x_r, y_r): continue
                tile_at_boundary = self.actual_dungeon_map[y_r][x_r]
                if tile_at_boundary == TILE_DOOR_CLOSED or tile_at_boundary == TILE_DOOR_OPEN:
                    self.ever_revealed_tiles.add((x_r, y_r))
                    for dx, dy in [(0,1),(0,-1),(1,0),(-1,0)]:
                        nx,ny = x_r+dx, y_r+dy
                        if 0 <= ny < len(self.actual_dungeon_map) and 0 <= nx < len(self.actual_dungeon_map[0]) and \
                           self.actual_dungeon_map[ny][nx] == TILE_FLOOR and \
                           not room_to_reveal.is_inside(nx,ny) and (nx,ny) not in self.ever_revealed_tiles:
                            q_corridor_reveal.append((nx,ny)); break 
        
        visited_in_bfs = set() 
        while q_corridor_reveal:
            cx, cy = q_corridor_reveal.popleft()
            if (cx,cy) in visited_in_bfs: continue
            visited_in_bfs.add((cx,cy))
            self.ever_revealed_tiles.add((cx,cy))
            actual_tile = self.actual_dungeon_map[cy][cx]
            if actual_tile == TILE_DOOR_CLOSED or actual_tile == TILE_DOOR_OPEN:
                is_door_to_unvisited_room = False
                for dx, dy in [(0,1),(0,-1),(1,0),(-1,0)]:
                    nx,ny = cx+dx, cy+dy
                    adj_room_info = self.get_room_at_pos(nx,ny)
                    if adj_room_info and adj_room_info[0] not in self.visited_room_indices:
                        is_door_to_unvisited_room = True; break
                if is_door_to_unvisited_room: continue
            for dx, dy in [(0,1),(0,-1),(1,0),(-1,0)]:
                nx, ny = cx + dx, cy + dy
                if 0 <= ny < len(self.actual_dungeon_map) and 0 <= nx < len(self.actual_dungeon_map[0]) and \
                   (nx,ny) not in self.ever_revealed_tiles and \
                   self.actual_dungeon_map[ny][nx] not in [TILE_WALL, TILE_EMPTY] and \
                   not self.get_room_at_pos(nx,ny): 
                    q_corridor_reveal.append((nx,ny))
        return [] 

    def update_fov(self, center_pos: Dict[str, int]) -> List[schemas.TileChangeServerResponse]:
        player_view_radius = game_config.PLAYER_VIEW_RADIUS
        responses: List[schemas.TileChangeServerResponse] = []
        if not self.actual_dungeon_map or not self.dungeon_map_for_client or not center_pos:
            return responses
        
        map_h = len(self.actual_dungeon_map)
        map_w = len(self.actual_dungeon_map[0])
        px_center, py_center = center_pos["x"], center_pos["y"]
        new_client_map_view = [[TILE_FOG for _ in range(map_w)] for _ in range(map_h)]

        for x_revealed, y_revealed in self.ever_revealed_tiles:
            if 0 <= y_revealed < map_h and 0 <= x_revealed < map_w:
                 new_client_map_view[y_revealed][x_revealed] = self.actual_dungeon_map[y_revealed][x_revealed]
        
        for r_y in range(py_center - player_view_radius, py_center + player_view_radius + 1):
            for r_x in range(px_center - player_view_radius, px_center + player_view_radius + 1):
                if not (0 <= r_y < map_h and 0 <= r_x < map_w): continue
                if math.sqrt((r_x - px_center)**2 + (r_y - py_center)**2) > player_view_radius: continue
                if self.has_line_of_sight(center_pos, {"x": r_x, "y": r_y}):
                    actual_tile = self.actual_dungeon_map[r_y][r_x]
                    new_client_map_view[r_y][r_x] = actual_tile 
                    self.ever_revealed_tiles.add((r_x, r_y)) 

        for y_scan in range(map_h):
            for x_scan in range(map_w):
                if self.dungeon_map_for_client[y_scan][x_scan] != new_client_map_view[y_scan][x_scan]:
                    responses.append(schemas.TileChangeServerResponse(
                        pos=schemas.Position(x=x_scan,y=y_scan),
                        new_tile_type=new_client_map_view[y_scan][x_scan] ))
        self.dungeon_map_for_client = new_client_map_view 
        return responses

    def has_line_of_sight(self, start_pos: Dict[str, int], end_pos: Dict[str, int]) -> bool:
        current_map = self.actual_dungeon_map
        if not current_map: return False
        x0, y0 = start_pos["x"], start_pos["y"]
        x1, y1 = end_pos["x"], end_pos["y"]
        dx = abs(x1 - x0); dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1; sy = 1 if y0 < y1 else -1
        err = dx - dy
        current_x, current_y = x0, y0
        map_h = len(current_map); map_w = len(current_map[0])
        while True:
            if not (current_x == x0 and current_y == y0) and \
               not (current_x == x1 and current_y == y1):
                if 0 <= current_y < map_h and 0 <= current_x < map_w:
                    tile_at_current = current_map[current_y][current_x]
                    if tile_at_current == TILE_WALL or tile_at_current == TILE_DOOR_CLOSED:
                        return False
                else: return False # Out of bounds
            if current_x == x1 and current_y == y1: break
            e2 = 2 * err
            if e2 > -dy: err -= dy; current_x += sx
            if e2 < dx: err += dx; current_y += sy
        return True

    def find_path_bfs(self, start_pos: Dict[str,int], end_pos: Dict[str,int], entity_type: str, entity_manager: 'EntityManager', player_pos: Optional[Dict[str, int]]) -> Optional[List[Dict[str,int]]]:
        if not self.actual_dungeon_map : return None

        # If start and end are the same, path is just the start/end point
        if start_pos["x"] == end_pos["x"] and start_pos["y"] == end_pos["y"]:
            return [start_pos]

        # Check if the starting position itself is walkable for the entity.
        # If not, no path can begin from there unless it's also the end_pos (handled above).
        if not self.is_walkable_for_entity(start_pos["x"], start_pos["y"], entity_type, entity_manager, player_pos):
            # Allow player to pathfind "from" a closed door tile they are on to open it (target is door)
            # but general pathfinding *from* an unwalkable tile should fail.
            # However, for monsters, if they somehow start on an unwalkable tile, they shouldn't be able to path.
            if entity_type != "player" or self.actual_dungeon_map[start_pos["y"]][start_pos["x"]] != TILE_DOOR_CLOSED:
                 return None


        queue: deque[List[Dict[str,int]]] = deque([[start_pos]])
        visited: Set[Tuple[int,int]] = { (start_pos["x"], start_pos["y"]) }
        
        map_h = len(self.actual_dungeon_map); map_w = len(self.actual_dungeon_map[0])

        while queue:
            path = queue.popleft()
            current_node = path[-1]

            # Check if current_node is the end_pos (already done before loop for start_pos == end_pos)
            # This check is for subsequent nodes in the path.
            if current_node["x"] == end_pos["x"] and current_node["y"] == end_pos["y"]:
                return path
            
            for dx, dy in [(0,1), (0,-1), (1,0), (-1,0)]: # Orthogonal neighbors
                next_x, next_y = current_node["x"] + dx, current_node["y"] + dy

                if (next_x, next_y) not in visited:
                    is_target_node = (next_x == end_pos["x"] and next_y == end_pos["y"])
                    can_path_through = False

                    if is_target_node:
                        # If the destination is the player's current tile and entity is a monster, it's a valid target.
                        if entity_type == "monster" and player_pos and next_x == player_pos["x"] and next_y == player_pos["y"]:
                            can_path_through = True
                        # If it's the target node, use is_walkable_for_entity to see if the entity can *end* on this tile.
                        # This handles cases like player moving to a door or item.
                        elif self.is_walkable_for_entity(next_x, next_y, entity_type, entity_manager, player_pos):
                             can_path_through = True
                    # For non-target nodes in the path
                    elif self.is_walkable_for_entity(next_x, next_y, entity_type, entity_manager, player_pos):
                        can_path_through = True
                    
                    if can_path_through:
                        visited.add((next_x, next_y))
                        new_path = list(path)
                        new_path.append({"x": next_x, "y": next_y})
                        queue.append(new_path)
        return None

    def is_tile_passable(self, x: int, y: int, for_entity_type: str) -> bool:
        if not self.actual_dungeon_map: return False
        map_h = len(self.actual_dungeon_map); map_w = len(self.actual_dungeon_map[0])
        if not (0 <= y < map_h and 0 <= x < map_w): return False
        tile = self.actual_dungeon_map[y][x]
        if tile == TILE_WALL: return False
        if tile == TILE_DOOR_CLOSED: return for_entity_type == "player" # Only player can "pass" closed doors to open
        return tile in [
            TILE_FLOOR, TILE_DOOR_OPEN, TILE_ITEM_POTION, TILE_STAIRS_DOWN, TILE_ITEM_SCROLL_TELEPORT,
            TILE_EMPTY # Assuming EMPTY might be a revealed but not yet defined space, potentially walkable
        ]

    def is_walkable_for_entity(self, x: int, y: int, entity_type: str, entity_manager: 'EntityManager', player_pos: Optional[Dict[str, int]]) -> bool:
        if not self.actual_dungeon_map: return False
        map_h = len(self.actual_dungeon_map); map_w = len(self.actual_dungeon_map[0])
        if not (0 <= y < map_h and 0 <= x < map_w): return False
        
        # Check underlying tile passability first
        # For player pathfinding, if target is a closed door, is_tile_passable returns true, 
        # but actual movement logic in GameState handles opening it. For pathfinding, treat it as walkable endpoint.
        tile = self.actual_dungeon_map[y][x]
        if not self.is_tile_passable(x, y, entity_type):
            # Allow player to "pathfind to" a closed door (to open it). GameState handles the "open" action.
            if entity_type == "player" and tile == TILE_DOOR_CLOSED:
                 pass # Allow pathfinding to end on a closed door for player
            else:
                return False

        # Check for blocking entities
        # An entity cannot walk onto its own current location during path exploration (unless teleporting)
        # Note: player_pos is the player's *current* position. If entity_type is "player", this prevents pathing to current spot.
        if entity_type != "player_teleport":
            if entity_type == "player" and player_pos and player_pos["x"] == x and player_pos["y"] == y:
                 return False 
            # For monsters, player_pos is the *target's* (player's) position.
            # A monster *can* pathfind to the player's tile.
            # If we are checking a monster's ability to walk to (x,y) and (x,y) is the player's pos:
            # This is fine, the monster wants to reach the player.
            # Entity manager check below handles if another monster is at (x,y)
            
        # Is there another monster at (x,y)?
        other_monster_at_xy = entity_manager.get_monster_at(x,y)
        if other_monster_at_xy:
            if entity_type == "monster": # Monsters cannot walk into other monsters
                return False
            # Player cannot normally walk onto a monster for pathfinding (bump attack is separate)
            # unless it's the target of the path for an attack next move (handled by game_state logic)
            if entity_type == "player": 
                return False 
            # player_teleport already handled by specific check below.
        
        # Specific check for player_teleport: must be floor/open door AND no monster
        if entity_type == "player_teleport": 
            return tile in [TILE_FLOOR, TILE_DOOR_OPEN] and not other_monster_at_xy

        # General walkability based on tile type for the entity, assuming no other entity blocks
        if entity_type == "monster":
            # Monsters can walk on floor and open doors.
            # They can also pathfind *to* the player's tile (which is likely TILE_FLOOR).
            return tile in [TILE_FLOOR, TILE_DOOR_OPEN]
        
        elif entity_type == "player":
            # Player can walk on floor, open doors, items, stairs.
            # Player can pathfind *to* a closed door to open it.
            # Monster check already done above.
            return tile in [
                TILE_FLOOR, TILE_DOOR_OPEN, TILE_ITEM_POTION, TILE_ITEM_SCROLL_TELEPORT,
                TILE_STAIRS_DOWN, TILE_DOOR_CLOSED 
            ]
            
        return False # Default deny