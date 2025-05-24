# backend/app/core/dungeon_generator.py
import random
import math 
from typing import Optional, List, Set, Tuple, Deque, Dict, Any
from collections import deque 
from .tiles import (
    TILE_EMPTY, TILE_FLOOR, TILE_WALL, TILE_ITEM_POTION,
    TILE_MONSTER_GOBLIN, TILE_MONSTER_ORC, TILE_MONSTER_SKELETON,
    TILE_DOOR_CLOSED, TILE_DOOR_OPEN, TILE_STAIRS_DOWN,
    TILE_ITEM_SCROLL_TELEPORT 
)
from . import config as game_config
import logging 
logger = logging.getLogger(__name__) 

class Room:
    def __init__(self, x: int, y: int, width: int, height: int):
        self.x1 = x; self.y1 = y
        self.x2 = x + width - 1; self.y2 = y + height - 1
        self.width = width; self.height = height
        self.id = str(random.randint(1000,9999)) 
        self.doors_made: int = 0
    def center(self) -> Tuple[int, int]: return (self.x1 + self.x2) // 2, (self.y1 + self.y2) // 2
    def intersects(self, other_room: 'Room', padding: int = 0) -> bool:
        return (self.x1 - padding <= other_room.x2 and self.x2 + padding >= other_room.x1 and
                self.y1 - padding <= other_room.y2 and self.y2 + padding >= other_room.y1)
    def is_inside(self, x: int, y: int) -> bool: return self.x1 <= x <= self.x2 and self.y1 <= y <= self.y2

class DungeonGenerator:
    def __init__(self, map_width: int, map_height: int, seed: Optional[int] = None):
        self.map_width = map_width; self.map_height = map_height
        self.seed = seed
        self.map_data: List[List[int]] = [] 
        self.rooms: List[Room] = []
        self.player_start_pos: Optional[Tuple[int, int]] = None
        if self.seed is not None: random.seed(self.seed)
        self._initialize_map() 

    def _initialize_map(self): 
        self.map_data = [[TILE_EMPTY for _ in range(self.map_width)] for _ in range(self.map_height)]

    def _create_room_and_walls(self, room: Room):
        for y_coord in range(room.y1 - 1, room.y2 + 2): 
            for x_coord in range(room.x1 - 1, room.x2 + 2):
                if 0 <= y_coord < self.map_height and 0 <= x_coord < self.map_width:
                    if room.is_inside(x_coord,y_coord): self.map_data[y_coord][x_coord] = TILE_FLOOR
                    elif self.map_data[y_coord][x_coord] == TILE_EMPTY: self.map_data[y_coord][x_coord] = TILE_WALL
    
    def _can_place_door_at(self, x:int, y:int) -> bool:
        if not (0 <= y < self.map_height and 0 <= x < self.map_width and self.map_data[y][x] == TILE_WALL): return False
        door_neighbors = 0
        for dx_adj in range(-1,2):
            for dy_adj in range(-1,2):
                if dx_adj == 0 and dy_adj == 0: continue
                adj_x, adj_y = x + dx_adj, y + dy_adj
                if 0 <= adj_y < self.map_height and 0 <= adj_x < self.map_width and \
                   self.map_data[adj_y][adj_x] in [TILE_DOOR_CLOSED, TILE_DOOR_OPEN]: door_neighbors +=1
        return door_neighbors < 1 

    def _get_random_floor_tile_in_room(self, room: Room) -> Optional[Tuple[int, int]]:
        floor_tiles = [(r_x,r_y) for r_y in range(room.y1,room.y2+1) for r_x in range(room.x1,room.x2+1)
                       if 0<=r_y<self.map_height and 0<=r_x<self.map_width and self.map_data[r_y][r_x]==TILE_FLOOR]
        if floor_tiles: return random.choice(floor_tiles)
        logger.warning(f"Room {room.id} has no floor tiles. Center: ({room.center()}). Forcing floor at center.")
        cx,cy = room.center()
        if 0<=cy<self.map_height and 0<=cx<self.map_width: self.map_data[cy][cx]=TILE_FLOOR; return cx,cy
        return None 
    
    def _place_entities(self, num_items_total: int, num_monsters: int ):
        if not self.rooms: logger.warning("No rooms to place entities in."); return
        if not self.player_start_pos: logger.error("Player start not set for entities, cannot place entities."); return

        room_floor_tiles: List[Tuple[int,int]] = []
        for room in self.rooms:
            for y_coord_room in range(room.y1, room.y2 + 1): 
                for x_coord_room in range(room.x1, room.x2 + 1):
                    if 0 <= y_coord_room < self.map_height and 0 <= x_coord_room < self.map_width and \
                       self.map_data[y_coord_room][x_coord_room] == TILE_FLOOR and \
                       not (x_coord_room == self.player_start_pos[0] and y_coord_room == self.player_start_pos[1]):
                        room_floor_tiles.append((x_coord_room, y_coord_room))
        
        if not room_floor_tiles: logger.warning("No available floor tiles for entities after excluding player start."); return
        random.shuffle(room_floor_tiles) 
        
        item_count = 0
        item_placement_candidates = list(room_floor_tiles) # Work with a copy for item placement
        placeable_item_tiles = [TILE_ITEM_POTION, TILE_ITEM_SCROLL_TELEPORT]

        for _ in range(num_items_total):
            if not item_placement_candidates: break
            x, y = item_placement_candidates.pop(random.randrange(len(item_placement_candidates)))
            self.map_data[y][x] = random.choice(placeable_item_tiles)
            item_count += 1
        # if item_count < num_items_total: logger.debug(f"Placed {item_count}/{num_items_total} items.")

        monster_count = 0
        available_for_monsters = [ (x_m,y_m) for x_m,y_m in room_floor_tiles if self.map_data[y_m][x_m] == TILE_FLOOR ] # Re-filter after items
        random.shuffle(available_for_monsters)

        monster_types_to_place = [] 
        dist = game_config.DG_MONSTER_TYPE_DISTRIBUTION
        num_g = round(num_monsters * dist.get("goblin", 0.4)) 
        num_o = round(num_monsters * dist.get("orc", 0.35))
        num_s = num_monsters - num_g - num_o 
        
        num_g = max(0, num_g); num_o = max(0, num_o); num_s = max(0, num_s)
        current_total = num_g + num_o + num_s
        if current_total < num_monsters : num_g += (num_monsters - current_total)
        elif current_total > num_monsters: num_g = max(0, num_g - (current_total - num_monsters))

        monster_types_to_place.extend([TILE_MONSTER_GOBLIN] * num_g)
        monster_types_to_place.extend([TILE_MONSTER_ORC] * num_o)
        monster_types_to_place.extend([TILE_MONSTER_SKELETON] * num_s)
        random.shuffle(monster_types_to_place) 

        for i in range(min(len(monster_types_to_place), len(available_for_monsters))):
            x, y = available_for_monsters[i] 
            self.map_data[y][x] = monster_types_to_place[i] 
            monster_count += 1
        # if monster_count < num_monsters: logger.debug(f"Placed {monster_count}/{num_monsters} monsters.")


    def _carve_floor_path(self, x1:int,y1:int,x2:int,y2:int) -> List[Tuple[int,int]]:
        path:List[Tuple[int,int]]=[];cx,cy=x1,y1
        if 0<=y1<self.map_height and 0<=x1<self.map_width:self.map_data[y1][x1]=TILE_FLOOR
        if 0<=y2<self.map_height and 0<=x2<self.map_width:self.map_data[y2][x2]=TILE_FLOOR
        turn_x,turn_y=(x2,y1) if random.randint(0,1)==0 else (x1,y2)
        while cx!=turn_x or cy!=turn_y:
            path.append((cx,cy))
            if 0<=cy<self.map_height and 0<=cx<self.map_width and self.map_data[cy][cx]==TILE_EMPTY:self.map_data[cy][cx]=TILE_FLOOR
            if cx!=turn_x:cx+=1 if turn_x>cx else -1
            elif cy!=turn_y:cy+=1 if turn_y>cy else -1
            else:break
        path.append((turn_x,turn_y))
        if 0<=turn_y<self.map_height and 0<=turn_x<self.map_width and self.map_data[turn_y][turn_x]==TILE_EMPTY:self.map_data[turn_y][turn_x]=TILE_FLOOR
        cx,cy=turn_x,turn_y
        while cx!=x2 or cy!=y2:
            path.append((cx,cy))
            if 0<=cy<self.map_height and 0<=cx<self.map_width and self.map_data[cy][cx]==TILE_EMPTY:self.map_data[cy][cx]=TILE_FLOOR
            if cx!=x2:cx+=1 if x2>cx else -1
            elif cy!=y2:cy+=1 if y2>cy else -1
            else:break
        path.append((x2,y2))
        if 0<=y2<self.map_height and 0<=x2<self.map_width and self.map_data[y2][x2]==TILE_EMPTY:self.map_data[y2][x2]=TILE_FLOOR
        return list(dict.fromkeys(path))

    def _rebuild_all_walls(self):
        for y in range(self.map_height):
            for x in range(self.map_width):
                if self.map_data[y][x]==TILE_EMPTY:
                    is_adj=any(0<=y+dy<self.map_height and 0<=x+dx<self.map_width and self.map_data[y+dy][x+dx] in [TILE_FLOOR,TILE_DOOR_CLOSED,TILE_DOOR_OPEN] for dx,dy in [(0,1),(0,-1),(1,0),(-1,0)])
                    self.map_data[y][x]=TILE_WALL

    def _ensure_all_rooms_connected(self):
        if len(self.rooms) <= 1: return
        shuffled_rooms = list(self.rooms); random.shuffle(shuffled_rooms)
        for i in range(len(shuffled_rooms) - 1):
            room1, room2 = shuffled_rooms[i], shuffled_rooms[i+1]
            p1, p2 = self._get_random_floor_tile_in_room(room1), self._get_random_floor_tile_in_room(room2)
            if p1 and p2:
                path = self._carve_floor_path(p1[0], p1[1], p2[0], p2[1])
                for idx in range(len(path) -1):
                    cx_p, cy_p = path[idx]; nx_p, ny_p = path[idx+1]
                    if not room1.is_inside(cx_p,cy_p) and 0<=ny_p<self.map_height and 0<=nx_p<self.map_width and self.map_data[ny_p][nx_p]==TILE_WALL:
                        is_r1_wall = any(room1.is_inside(nx_p+drx,ny_p+dry) for drx,dry in [(0,1),(0,-1),(1,0),(-1,0)])
                        if is_r1_wall and self._can_place_door_at(nx_p,ny_p): self.map_data[ny_p][nx_p]=TILE_DOOR_CLOSED; break
                rev_path = list(reversed(path))
                for idx in range(len(rev_path) -1):
                    cx_p, cy_p = rev_path[idx]; nx_p, ny_p = rev_path[idx+1]
                    if not room2.is_inside(cx_p,cy_p) and 0<=ny_p<self.map_height and 0<=nx_p<self.map_width and self.map_data[ny_p][nx_p]==TILE_WALL:
                        is_r2_wall = any(room2.is_inside(nx_p+drx,ny_p+dry) for drx,dry in [(0,1),(0,-1),(1,0),(-1,0)])
                        if is_r2_wall and self._can_place_door_at(nx_p,ny_p): self.map_data[ny_p][nx_p]=TILE_DOOR_CLOSED; break
            # else: logger.warning(f"Could not connect rooms {room1.id} and {room2.id}")

    def generate_dungeon(self, max_rooms: int = game_config.DEFAULT_MAX_ROOMS, 
                         room_min_size: int = game_config.DEFAULT_ROOM_MIN_SIZE, 
                         room_max_size: int = game_config.DEFAULT_ROOM_MAX_SIZE
                        ) -> Tuple[List[List[int]], Optional[Tuple[int, int]]]:
        self._initialize_map() 
        self.rooms = []        
        self.player_start_pos = None
        
        if not self.rooms:
            w = random.randint(room_min_size, room_max_size); h = random.randint(room_min_size, room_max_size)
            x = random.randint(1, self.map_width-w-2); y = random.randint(1, self.map_height-h-2)
            first_room = Room(x,y,w,h)
            self.rooms.append(first_room); self._create_room_and_walls(first_room) 
            if not self.player_start_pos : self.player_start_pos = first_room.center()

        for _ in range(max_rooms -1):
            if not self.rooms: break 
            candidate_rooms = [r for r in self.rooms if r.doors_made < game_config.DG_MAX_DOORS_FOR_BUDDING_CANDIDATE] 
            if not candidate_rooms: candidate_rooms = self.rooms
            base_room = random.choice(candidate_rooms); placed_new = False
            for _attempt in range(game_config.DG_ROOM_BUDDING_ATTEMPTS): 
                w=random.randint(room_min_size,room_max_size); h=random.randint(room_min_size,room_max_size)
                side=random.randint(0,3); door_x,door_y,new_room_x,new_room_y = -1,-1,-1,-1
                if side==0:door_x=random.randint(base_room.x1,base_room.x2);door_y=base_room.y1-1;new_room_x=door_x-random.randint(0,w-1);new_room_y=door_y-h
                elif side==1:door_y=random.randint(base_room.y1,base_room.y2);door_x=base_room.x2+1;new_room_x=door_x+1;new_room_y=door_y-random.randint(0,h-1)
                elif side==2:door_x=random.randint(base_room.x1,base_room.x2);door_y=base_room.y2+1;new_room_x=door_x-random.randint(0,w-1);new_room_y=door_y+1
                else:door_y=random.randint(base_room.y1,base_room.y2);door_x=base_room.x1-1;new_room_x=door_x-w;new_room_y=door_y-random.randint(0,h-1)
                if not(0<door_y<self.map_height-1 and 0<door_x<self.map_width-1):continue
                if not(new_room_x>=1 and new_room_x+w<self.map_width-1 and new_room_y>=1 and new_room_y+h<self.map_height-1 ):continue
                new_room = Room(new_room_x,new_room_y,w,h)
                if any(new_room.intersects(r_obj,padding=0) for r_obj in self.rooms):continue
                can_bud = True
                if self.map_data[door_y][door_x] not in [TILE_EMPTY,TILE_WALL]:can_bud=False
                empty_count=sum(1 for ry_ in range(new_room.y1,new_room.y2+1) for rx_ in range(new_room.x1,new_room.x2+1) if self.map_data[ry_][rx_]==TILE_EMPTY)
                if empty_count<(w*h*game_config.DG_ROOM_REQUIRED_EMPTY_RATIO):can_bud=False 
                original_door_tile=self.map_data[door_y][door_x]
                if original_door_tile==TILE_EMPTY:self.map_data[door_y][door_x]=TILE_WALL
                door_placeable=self._can_place_door_at(door_x,door_y)
                if original_door_tile==TILE_EMPTY:self.map_data[door_y][door_x]=TILE_EMPTY
                if can_bud and door_placeable:
                    self.rooms.append(new_room);self._create_room_and_walls(new_room)
                    self.map_data[door_y][door_x]=TILE_DOOR_CLOSED
                    base_room.doors_made+=1;placed_new=True;break
            # if not placed_new: logger.debug(f"Could not bud a new room from {base_room.id}")
        
        self._ensure_all_rooms_connected()
        self._rebuild_all_walls() 
        
        if self.player_start_pos is None and self.rooms: self.player_start_pos = self.rooms[0].center()
        if self.player_start_pos and \
           (not (0<=self.player_start_pos[1]<self.map_height and 0<=self.player_start_pos[0]<self.map_width) or \
            self.map_data[self.player_start_pos[1]][self.player_start_pos[0]]!=TILE_FLOOR):
            # logger.warning("Player start position invalid or not floor. Attempting to fix.")
            found_floor=False
            if self.rooms:
                 center_first_room=self.rooms[0].center()
                 if 0<=center_first_room[1]<self.map_height and 0<=center_first_room[0]<self.map_width and self.map_data[center_first_room[1]][center_first_room[0]]==TILE_FLOOR:
                    self.player_start_pos=center_first_room; found_floor=True
            if not found_floor:
                for r_idx_s in range(self.map_height):
                    for c_idx_s in range(self.map_width):
                        if self.map_data[r_idx_s][c_idx_s]==TILE_FLOOR: self.player_start_pos=(c_idx_s,r_idx_s);found_floor=True;break
                    if found_floor:break
            if not found_floor and self.player_start_pos:
                 if 0<=self.player_start_pos[1]<self.map_height and 0<=self.player_start_pos[0]<self.map_width:self.map_data[self.player_start_pos[1]][self.player_start_pos[0]]=TILE_FLOOR
            if not self.player_start_pos:
                self.player_start_pos=(self.map_width//2,self.map_height//2)
                if 0<=self.player_start_pos[1]<self.map_height and 0<=self.player_start_pos[0]<self.map_width: self.map_data[self.player_start_pos[1]][self.player_start_pos[0]]=TILE_FLOOR
                else: self.map_data[0][0]=TILE_FLOOR;self.player_start_pos=(0,0) # Should not happen
                logger.error(f"Player start pos was None even after fallbacks, defaulted to {self.player_start_pos}")
        
        num_r = len(self.rooms) if self.rooms else 0
        items_min = max(game_config.DG_ITEMS_MIN_ABS_COUNT, num_r // game_config.DG_ITEMS_ROOM_DIVISOR_FOR_MIN if game_config.DG_ITEMS_ROOM_DIVISOR_FOR_MIN > 0 else num_r)
        items_max_calc_base = (num_r // game_config.DG_ITEMS_ROOM_DIVISOR_FOR_MAX if game_config.DG_ITEMS_ROOM_DIVISOR_FOR_MAX > 0 else num_r) + game_config.DG_ITEMS_MAX_ADDEND
        items_max = max(items_min + 1, items_max_calc_base) 
        final_num_items = random.randint(items_min, items_max) if items_min <= items_max else items_min

        monsters_min_calc_base = (num_r // game_config.DG_MONSTERS_ROOM_DIVISOR_FOR_MIN if game_config.DG_MONSTERS_ROOM_DIVISOR_FOR_MIN > 0 else num_r) + game_config.DG_MONSTERS_MIN_ADDEND
        monsters_min = max(game_config.DG_MONSTERS_MIN_ABS_COUNT, monsters_min_calc_base)
        monsters_max_calc_base = (num_r // game_config.DG_MONSTERS_ROOM_DIVISOR_FOR_MAX if game_config.DG_MONSTERS_ROOM_DIVISOR_FOR_MAX > 0 else num_r) + game_config.DG_MONSTERS_MAX_ADDEND
        monsters_max = max(monsters_min, monsters_max_calc_base) 
        final_num_monsters = random.randint(monsters_min, monsters_max) if monsters_min <= monsters_max else monsters_min
        
        self._place_entities(num_items_total=final_num_items, num_monsters=final_num_monsters)
        # Stairs are handled by GameState for this version of the generator
        
        return self.map_data, self.player_start_pos

    def _find_connected_rooms_bfs(self, start_room_idx: int) -> Set[int]: 
        if not self.rooms or start_room_idx >= len(self.rooms): return set()
        start_tile_bfs_tuple = self._get_random_floor_tile_in_room(self.rooms[start_room_idx]) 
        if not start_tile_bfs_tuple: 
            center_bfs = self.rooms[start_room_idx].center()
            if 0 <= center_bfs[1] < self.map_height and 0 <= center_bfs[0] < self.map_width and \
               (self.map_data[center_bfs[1]][center_bfs[0]] == TILE_FLOOR or self.map_data[center_bfs[1]][center_bfs[0]] == TILE_DOOR_OPEN):
                start_tile_bfs_tuple = center_bfs
            else: return {start_room_idx} 
        q_bfs: Deque[Tuple[int,int]] = deque([start_tile_bfs_tuple])
        visited_floor_tiles: Set[Tuple[int,int]] = {q_bfs[0]}
        reachable_room_indices: Set[int] = set() 
        if start_room_idx < len(self.rooms) and self.rooms[start_room_idx].is_inside(q_bfs[0][0], q_bfs[0][1]):
             reachable_room_indices.add(start_room_idx)
        head_bfs = 0
        while head_bfs < len(q_bfs): 
            cx, cy = q_bfs[head_bfs]; head_bfs += 1
            for r_idx, r_obj in enumerate(self.rooms):
                if r_obj.is_inside(cx, cy): reachable_room_indices.add(r_idx)
            for dx, dy in [(0,1), (0,-1), (1,0), (-1,0)]: 
                nx, ny = cx + dx, cy + dy
                if 0 <= ny < self.map_height and 0 <= nx < self.map_width and \
                   (self.map_data[ny][nx] == TILE_FLOOR or self.map_data[ny][nx] == TILE_DOOR_OPEN) and \
                   (nx,ny) not in visited_floor_tiles:
                    visited_floor_tiles.add((nx,ny)); q_bfs.append((nx,ny))
        return reachable_room_indices
    
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO) # Changed to INFO for less verbose default test run
    for test_seed in [None, 123, 456, 7890, 112233, 18128, 62063]: 
        print(f"\n--- Generating dungeon with seed: {test_seed} ---")
        gen = DungeonGenerator(map_width=60, map_height=40, seed=test_seed) 
        dungeon, start_pos = gen.generate_dungeon() # Use config defaults
        
        if dungeon is None or start_pos is None or (dungeon and not dungeon[0]): print("Dungeon generation failed."); continue
        if start_pos: print(f"Player start: {start_pos}")
        else: print("Player start position is None!")
        print(f"Number of rooms created: {len(gen.rooms)}")
        tile_chars = {
            TILE_WALL: "#", TILE_FLOOR: ".", TILE_EMPTY: " ", TILE_ITEM_POTION: "P", 
            TILE_ITEM_SCROLL_TELEPORT: "S", TILE_MONSTER_GOBLIN: "g", TILE_MONSTER_ORC: "O", 
            TILE_MONSTER_SKELETON: "K", TILE_DOOR_CLOSED: "+", TILE_DOOR_OPEN: "-", TILE_STAIRS_DOWN: ">",}
        for r_idx, row in enumerate(dungeon):
            line = [tile_chars.get(tile, "?") for tile in row]
            if start_pos and r_idx == start_pos[1] and start_pos[0] < len(line): line[start_pos[0]] = "@"
            print("".join(line))
        if gen.rooms:
            all_connected_indices: Set[int] = set()
            if gen.rooms and len(gen.rooms) > 0 : all_connected_indices = gen._find_connected_rooms_bfs(0)
            print(f"Rooms connected to room 0: {len(all_connected_indices)} out of {len(gen.rooms)}")
            if len(all_connected_indices) < len(gen.rooms): print("WARNING: Not all rooms connected!")
            else: print("All rooms appear connected.")
        print("-" * 30)