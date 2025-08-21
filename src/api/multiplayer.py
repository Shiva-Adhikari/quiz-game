from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
import json
import asyncio

from src.schemas.multiplayer import (
    RoomCreate, RoomResponse, RoomDetailResponse, JoinRoomRequest,
    PlayerReadyRequest, SubmitAnswerRequest, ParticipantResponse
)
import src.utils.multiplayer.crud as crud
from src.utils.multiplayer.websocket_manager import manager
from src.utils.multiplayer.game_engine import MultiplayerGameEngine
from typing import Dict
from datetime import datetime, timezone
from src.utils.db import get_db
from src.utils.get_current_user import get_current_user
from src.models.questions import Question


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
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to create room")


@router.get("/rooms/browse", response_model=List[RoomResponse])
def browse_rooms(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Browse only public rooms (no password required)"""
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
            "participant_id": participant.id,
            "room_type": "public" if room.is_public else "private"
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
        mock_questions = generate_mock_questions(db, room.total_questions, room.difficulty_level, room.category_id)
        question_ids = [q["id"] for q in mock_questions]

        # Create game session
        game_session = crud.start_game_session(db, room_id, question_ids)
        
        # Create and start game engine
        game_engine = MultiplayerGameEngine(room_id, db)
        active_games[room_id] = game_engine
        
        # Start game asynchronously
        await game_engine.start_game(mock_questions, room.time_per_question)
        
        return {
            "message": "Game started",
            "game_session_id": game_session.id,
            "questions": mock_questions
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to start game")


@router.post("/rooms/{room_id}/answer")
async def submit_answer(  # Make it async
    room_id: int,
    answer: SubmitAnswerRequest,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # First, get the room to ensure it exists and is in progress
        room_data = crud.get_room_with_participants(db, room_id)
        if not room_data:
            raise HTTPException(status_code=404, detail="Room not found")
        
        room = room_data["room"]
        
        # Check if room is in progress
        if room.status != "in_progress":
            raise HTTPException(status_code=400, detail="Game is not in progress")
        
        # Verify user is a participant
        user_is_participant = any(
            p.user_id == current_user.id and p.is_active 
            for p in room_data["participants"]
        )
        if not user_is_participant:
            raise HTTPException(status_code=403, detail="You are not a participant in this room")
        
        # Get current question's correct answer
        # You'll need to implement this based on your Question model
        correct_answer = get_correct_answer_for_question(db, answer.question_id)
        if not correct_answer:
            raise HTTPException(status_code=400, detail="Invalid question ID")
        
        # Submit answer
        result = crud.submit_player_answer(
            db, room_id, current_user.id, answer, correct_answer, room.time_per_question
        )
        
        # Notify game engine if it exists
        if room_id in active_games:
            await active_games[room_id].process_player_answer(current_user.id, {
                "question_id": answer.question_id,
                "selected_answer": answer.selected_answer,
                "time_taken": answer.time_taken
            })
        
        return {
            "message": "Answer submitted successfully",
            "is_correct": result["answer"].is_correct,
            "score_earned": result["answer"].score_earned,
            "total_score": result["participant"].total_score
        }
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Error in submit_answer: {e}")  # For debugging
        raise HTTPException(status_code=500, detail="Failed to submit answer")


@router.post("/rooms/{room_id}/leave")
async def leave_room(  # Make it async
    room_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # Check if room exists
        room_data = crud.get_room_with_participants(db, room_id)
        if not room_data:
            raise HTTPException(status_code=404, detail="Room not found")
        
        # Check if user is actually in the room
        user_participant = None
        for participant in room_data["participants"]:
            if participant.user_id == current_user.id and participant.is_active:
                user_participant = participant
                break
        
        if not user_participant:
            raise HTTPException(status_code=400, detail="You are not in this room")
        
        # Leave the room
        participant = crud.leave_room(db, room_id, current_user.id)
        if not participant:
            raise HTTPException(status_code=400, detail="Could not leave room")
        
        # Broadcast player left (await instead of create_task)
        await manager.send_to_room(room_id, "player_left", {
            "user_id": current_user.id,
            "was_host": participant.is_host,
            "player_name": getattr(current_user, 'username', f'User {current_user.id}')
        })
        
        # Clean up game engine if room becomes empty
        room_data_updated = crud.get_room_with_participants(db, room_id)
        if room_data_updated and room_data_updated["room"].current_players == 0:
            if room_id in active_games:
                # Cancel any ongoing game timers
                game_engine = active_games[room_id]
                if hasattr(game_engine, 'question_timer_task') and game_engine.question_timer_task:
                    game_engine.question_timer_task.cancel()
                del active_games[room_id]
        
        return {
            "message": "Left room successfully",
            "was_host": participant.is_host
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in leave_room: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to leave room: {str(e)}")


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
                        "timestamp": datetime.now(timezone.utc).isoformat()
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
def generate_mock_questions(db: Session, total_questions: int, difficulty: str, category_id: int):
    """Get real questions from database based on category and difficulty"""
    query = db.query(Question).filter(
        Question.category_id == category_id,
        Question.is_active
    )
    
    if difficulty != "mixed":
        query = query.filter(Question.difficulty_level == difficulty)
    
    questions = query.order_by(func.random()).limit(total_questions).all()
    
    return [{
        "id": q.id,
        "question_text": q.question_text,
        "option_a": q.option_a,
        "option_b": q.option_b,
        "option_c": q.option_c,
        "option_d": q.option_d,
        "correct_answer": q.correct_answer,
        "explanation": getattr(q, 'explanation', ''),
        "difficulty": q.difficulty_level
    } for q in questions]


# def get_mock_correct_answer(question_id: int) -> str:
    # """Get correct answer for question - replace with database query"""
    # return "A"  # Mock correct answer


# '''
# Helper function to get correct answer - implement this based on your Question model
def get_correct_answer_for_question(db: Session, question_id: int) -> str | None:
    """
    Get the correct answer for a given question ID
    Replace this with actual database query to your Question table
    """
    # Example implementation - replace with your actual Question model query
    question = db.query(Question).filter(Question.id == question_id).first()
    if question:
        return question.correct_answer
    return None
    
    # # Temporary mock implementation for testing
    # mock_answers = {
    #     1: "A", 2: "B", 3: "C", 4: "D", 5: "A",
    #     6: "B", 7: "C", 8: "D", 9: "A", 10: "B"
    # }
    # return mock_answers.get(question_id, "A")


'''
# Alternative: If you're storing questions in the game session
def get_correct_answer_from_session(db: Session, room_id: int, question_id: int) -> str:
    """
    Get correct answer from the game session's selected questions
    """
    game_session = db.query(GameSession).filter(
        and_(
            GameSession.room_id == room_id,
            GameSession.status == "active"
        )
    ).first()
    
    if not game_session or not game_session.selected_questions:
        return None
    
    try:
        questions = json.loads(game_session.selected_questions)
        for q in questions:
            if q.get("id") == question_id:
                return q.get("correct_answer")
    except (json.JSONDecodeError, TypeError):
        pass
    
    return None
'''


# Additional helper route to check room status (useful for debugging)
@router.get("/rooms/{room_id}/status")
def get_room_status(
    room_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current room status for debugging"""
    try:
        room_data = crud.get_room_with_participants(db, room_id)
        if not room_data:
            raise HTTPException(status_code=404, detail="Room not found")
        
        room = room_data["room"]
        participants = room_data["participants"]
        
        return {
            "room_id": room.id,
            "room_code": room.room_code,
            "status": room.status,
            "current_players": room.current_players,
            "max_players": room.max_players,
            "participants": [
                {
                    "user_id": p.user_id,
                    "is_host": p.is_host,
                    "is_active": p.is_active,
                    "is_ready": p.is_ready
                } for p in participants
            ],
            "user_in_room": any(
                p.user_id == current_user.id and p.is_active 
                for p in participants
            )
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get room status: {str(e)}")
