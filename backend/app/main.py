# backend/app/main.py
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json
import logging
from typing import Any, Dict

from app.core.game_state import GameState
from app.schemas import (
    ServerResponse, # Import the Union type
    ErrorServerResponse, PlayerMoveClientPayload, GenerateDungeonClientPayload,
    UseItemClientPayload, EquipItemClientPayload, UnequipItemClientPayload,
    Position
)

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(name)s - %(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(debug=True)
origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
app.add_middleware(CORSMiddleware,allow_origins=origins,allow_credentials=True,allow_methods=["*"],allow_headers=["*"])

class ConnectionManager:
    def __init__(self): self.active_connections: list[WebSocket] = []
    async def connect(self, websocket: WebSocket): await websocket.accept(); self.active_connections.append(websocket); logger.info(f"WS {websocket.client} connected.")
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections: self.active_connections.remove(websocket)
manager = ConnectionManager()
active_games: dict[WebSocket, GameState] = {}

async def send_responses(websocket: WebSocket, responses: list[ServerResponse]): # Type hint uses imported ServerResponse
    for response_model in responses:
        if response_model:
            await websocket.send_json(response_model.model_dump(mode="json"))


@app.websocket("/ws/dungeon")
async def websocket_dungeon_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    game_state_instance = GameState(client_id=f"{websocket.client.host}:{websocket.client.port}")
    active_games[websocket] = game_state_instance

    try:
        while True:
            data = await websocket.receive_text()
            try:
                message_dict: Dict[str, Any] = json.loads(data)
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from {game_state_instance.client_id}: {data}")
                await websocket.send_json(ErrorServerResponse(message="Invalid JSON format.").model_dump(mode="json"))
                continue

            action = message_dict.get("action")
            responses_to_send: list[ServerResponse] = [] # Type hint uses imported ServerResponse
            current_gs = active_games.get(websocket)

            if not current_gs:
                logger.error(f"CRITICAL: No GameState for WS {websocket.client}. Closing.")
                await websocket.close(code=1011, reason="Internal server error: game state lost")
                break

            if action == "generate_dungeon":
                try:
                    payload = GenerateDungeonClientPayload(**message_dict)
                    seed_to_use = payload.seed
                except Exception as e_parse:
                    logger.warning(f"Invalid generate_dungeon payload: {message_dict}, error: {e_parse}")
                    responses_to_send.append(ErrorServerResponse(message="Invalid payload for generating dungeon."))
                else:
                    logger.info(f"Action 'generate_dungeon' for {current_gs.client_id} with seed: {seed_to_use}")
                    dungeon_response_model = current_gs.generate_new_dungeon(
                        seed=seed_to_use, width=50, height=30,
                        max_rooms=10, room_min=5, room_max=10
                    )
                    # generate_new_dungeon can return ErrorServerResponse or DungeonDataServerResponse
                    # both are part of the ServerResponse Union
                    if dungeon_response_model: # Ensure it's not None
                        responses_to_send.append(dungeon_response_model)
            
            elif action == "player_move":
                try:
                    payload = PlayerMoveClientPayload(**message_dict)
                    new_pos = payload.new_pos
                except Exception as e_parse:
                    logger.warning(f"Invalid player_move payload: {message_dict}, error: {e_parse}")
                    responses_to_send.append(ErrorServerResponse(message="Invalid payload for player move."))
                else:
                    move_responses_list = current_gs.handle_player_move(new_pos.x, new_pos.y)
                    responses_to_send.extend(move_responses_list)
            
            elif action == "use_item":
                try:
                    payload = UseItemClientPayload(**message_dict)
                except Exception as e_parse:
                    logger.warning(f"Invalid use_item payload: {message_dict}, error: {e_parse}")
                    responses_to_send.append(ErrorServerResponse(message="Invalid payload for use item."))
                else:
                    logger.info(f"Action 'use_item' for {current_gs.client_id}, item_id: {payload.item_id}")
                    item_responses_list = current_gs.handle_use_item(payload.item_id)
                    responses_to_send.extend(item_responses_list)

            elif action == "equip_item":
                try:
                    payload = EquipItemClientPayload(**message_dict)
                except Exception as e_parse:
                    logger.warning(f"Invalid equip_item payload: {message_dict}, error: {e_parse}")
                    responses_to_send.append(ErrorServerResponse(message="Invalid payload for equip item."))
                else:
                    logger.info(f"Action 'equip_item' for {current_gs.client_id}, item_id: {payload.item_id}")
                    equip_responses_list = current_gs.handle_equip_item(payload.item_id)
                    responses_to_send.extend(equip_responses_list)
            
            elif action == "unequip_item":
                try:
                    payload = UnequipItemClientPayload(**message_dict)
                except Exception as e_parse:
                    logger.warning(f"Invalid unequip_item payload: {message_dict}, error: {e_parse}")
                    responses_to_send.append(ErrorServerResponse(message="Invalid payload for unequip item."))
                else:
                    logger.info(f"Action 'unequip_item' for {current_gs.client_id}, slot: {payload.slot}")
                    unequip_responses_list = current_gs.handle_unequip_item(payload.slot)
                    responses_to_send.extend(unequip_responses_list)

            else:
                logger.warning(f"Unknown action '{action}' from {current_gs.client_id}")
                responses_to_send.append(ErrorServerResponse(message=f"Unknown action: {action}"))

            await send_responses(websocket, responses_to_send)

    except WebSocketDisconnect:
        client_id_log = active_games.get(websocket).client_id if websocket in active_games else str(websocket.client)
        logger.info(f"Client {client_id_log} disconnected.")
    except json.JSONDecodeError:
        logger.error(f"Outer JSONDecodeError (should be rare): {data if 'data' in locals() else 'Unknown'}") # type: ignore
    except Exception as e:
        client_id_log = active_games.get(websocket).client_id if websocket in active_games else str(websocket.client)
        logger.error(f"Outer unhandled error for {client_id_log}: {e}", exc_info=True)
        try: await websocket.send_json(ErrorServerResponse(message="Critical server error.").model_dump(mode="json"))
        except Exception: pass 
    finally:
        if websocket in active_games:
            client_id_log = active_games[websocket].client_id
            del active_games[websocket]
            logger.info(f"Cleaned up GameState for {client_id_log}.")
        manager.disconnect(websocket)

@app.get("/")
async def read_root(): return {"message": "Roguelike Backend is running."}