from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from sqlalchemy.orm import Session
from typing import List
import json
import asyncio

from src.schemas.multiplayer import (
    RoomCreate, RoomResponse, RoomDetailResponse, JoinRoomRequest,
    PlayerReadyRequest, SubmitAnswerRequest, ParticipantResponse
)
from src.utils.multiplayer import crud
from src.utils.multiplayer.websocket_manager import manager
from src.utils.multiplayer.game_engine import MultiplayerGameEngine
from typing import Dict
from datetime import datetime
from src.utils.db import get_db
from src.utils.get_current_user import get_current_user


router = APIRouter(prefix="/multiplayer", tags=["multiplayer"])

# Store active game engines
active_games: Dict[int, MultiplayerGameEngine] = {}


@router.post("/rooms/create", response_model=RoomResponse)
def create_room(
    room_data: RoomCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        room = crud.create_room(db, room_data, current_user.id)
        return room
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/rooms/browse", response_model=List[RoomResponse])
def browse_rooms(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    rooms = crud.get_public_rooms(db, skip, limit)
    return rooms


@router.post("/rooms/join")
def join_room(
    join_data: JoinRoomRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        participant = crud.join_room(
            db, join_data.room_code, current_user.id, join_data.password
        )
        
        room = crud.get_room_by_code(db, join_data.room_code)
        
        return {
            "message": "Successfully joined room",
            "room_id": room.id,
            "room_code": room.room_code,
            "participant_id": participant.id
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to join room")


@router.get("/rooms/{room_id}", response_model=RoomDetailResponse)
def get_room_details(
    room_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    room_data = crud.get_room_with_participants(db, room_id)
    if not room_data:
        raise HTTPException(status_code=404, detail="Room not found")
    
    return RoomDetailResponse(
        room=room_data["room"],
        participants=room_data["participants"]
    )


@router.post("/rooms/{room_id}/ready")
async def set_ready_status(
    room_id: int,
    ready_data: PlayerReadyRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        result = crud.update_player_ready(db, room_id, current_user.id, ready_data.is_ready)
        
        # Broadcast ready status to all players in room
        # asyncio.create_task(
        await manager.send_to_room(room_id, "player_ready_status", {
            "user_id": current_user.id,
            "is_ready": ready_data.is_ready,
            "all_ready": result["all_ready"]
        })
        # )
        
        return {
            "message": "Ready status updated",
            "is_ready": ready_data.is_ready,
            "all_ready": result["all_ready"]
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/rooms/{room_id}/start")
async def start_game(
    room_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        # Verify user is host
        room_data = crud.get_room_with_participants(db, room_id)
        if not room_data:
            raise HTTPException(status_code=404, detail="Room not found")
        
        room = room_data["room"]
        if room.host_user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Only host can start the game")
        
        if room.status != "waiting":
            raise HTTPException(status_code=400, detail="Game already started or finished")
        
        # Check if all players are ready
        participants = room_data["participants"]
        all_ready = all(p.is_ready for p in participants) and len(participants) >= 2
        
        if not all_ready:
            raise HTTPException(status_code=400, detail="All players must be ready")
        
        # Get questions (this would normally query your Question table)
        # For now, using mock data structure
        mock_questions = generate_mock_questions(room.total_questions, room.difficulty_level)
        question_ids = [q["id"] for q in mock_questions]
        
        # Create game session
        game_session = crud.start_game_session(db, room_id, question_ids)
        
        # Create and start game engine
        game_engine = MultiplayerGameEngine(room_id, db)
        active_games[room_id] = game_engine
        
        # Start game asynchronously
        # asyncio.create_task(
        await game_engine.start_game(mock_questions, room.time_per_question)
        # )
        
        return {
            "message": "Game started",
            "game_session_id": game_session.id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to start game")


@router.post("/rooms/{room_id}/answer")
def submit_answer(
    room_id: int,
    answer: SubmitAnswerRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        # Get current question's correct answer (normally from Question table)
        correct_answer = get_mock_correct_answer(answer.question_id)
        
        room_data = crud.get_room_with_participants(db, room_id)
        if not room_data:
            raise HTTPException(status_code=404, detail="Room not found")
        
        room = room_data["room"]
        
        # Submit answer
        result = crud.submit_player_answer(
            db, room_id, current_user.id, answer, correct_answer, room.time_per_question
        )
        
        # Notify game engine
        if room_id in active_games:
            asyncio.create_task(
                active_games[room_id].process_player_answer(current_user.id, {
                    "question_id": answer.question_id,
                    "selected_answer": answer.selected_answer,
                    "time_taken": answer.time_taken
                })
            )
        
        return {
            "message": "Answer submitted",
            "is_correct": result["answer"].is_correct,
            "score_earned": result["answer"].score_earned,
            "total_score": result["participant"].total_score
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to submit answer")


@router.post("/rooms/{room_id}/leave")
def leave_room(
    room_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        participant = crud.leave_room(db, room_id, current_user.id)
        if not participant:
            raise HTTPException(status_code=404, detail="Not in this room")
        
        # Broadcast player left
        asyncio.create_task(
            manager.send_to_room(room_id, "player_left", {
                "user_id": current_user.id,
                "was_host": participant.is_host
            })
        )
        
        return {"message": "Left room successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to leave room")


@router.websocket("/rooms/{room_id}/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    room_id: int,
    user_id: int,  # This would normally come from JWT token in query params
    db: Session = Depends(get_db)
):
    await manager.connect(websocket, room_id, user_id)
    
    try:
        # Send welcome message
        await manager.send_to_user(room_id, user_id, "connected", {
            "message": "Connected to room",
            "room_id": room_id
        })
        
        # Notify others about new player
        await manager.send_to_room(room_id, "player_joined", {
            "user_id": user_id,
            "total_connections": manager.get_room_connections_count(room_id)
        })
        
        # Keep connection alive and handle messages
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle different message types
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
                elif message.get("type") == "chat":
                    # Broadcast chat message
                    await manager.send_to_room(room_id, "chat_message", {
                        "user_id": user_id,
                        "message": message.get("message", ""),
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON"
                }))
            except Exception as e:
                await websocket.send_text(json.dumps({
                    "type": "error", 
                    "message": f"Error: {str(e)}"
                }))
                
    except WebSocketDisconnect:
        pass
    finally:
        room_id_left, user_id_left = manager.disconnect(websocket)
        if room_id_left and user_id_left:
            # Handle player disconnect in database
            crud.leave_room(db, room_id_left, user_id_left)
            
            # Notify others
            await manager.send_to_room(room_id_left, "player_disconnected", {
                "user_id": user_id_left,
                "total_connections": manager.get_room_connections_count(room_id_left)
            })
            
            # Clean up game engine if room is empty
            if manager.get_room_connections_count(room_id_left) == 0 and room_id_left in active_games:
                del active_games[room_id_left]


# Helper functions for mock data (replace with actual database queries)
def generate_mock_questions(total_questions: int, difficulty: str):
    """Generate mock questions - replace with actual database query"""
    questions = []
    for i in range(total_questions):
        questions.append({
            "id": i + 1,
            "question_text": f"Sample {difficulty} question {i + 1}?",
            "option_a": "Option A",
            "option_b": "Option B", 
            "option_c": "Option C",
            "option_d": "Option D",
            "correct_answer": "A",  # Mock correct answer
            "explanation": f"Explanation for question {i + 1}",
            "difficulty": difficulty
        })
    return questions


def get_mock_correct_answer(question_id: int) -> str:
    """Get correct answer for question - replace with database query"""
    return "A"  # Mock correct answer
