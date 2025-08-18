# === CRUD OPERATIONS ===
# crud.py
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from src.models.multiplayer import MultiplayerRoom, RoomParticipant, GameSession, PlayerAnswer
from src.schemas.multiplayer import RoomCreate, SubmitAnswerRequest
from src.utils.multiplayer.utils import generate_room_code, calculate_quiz_score
from typing import Optional, List
import json
from datetime import datetime


def create_room(db: Session, room_data: RoomCreate, user_id: int):
    room_code = generate_room_code()
    
    # Ensure unique room code
    while db.query(MultiplayerRoom).filter(MultiplayerRoom.room_code == room_code).first():
        room_code = generate_room_code()
    
    db_room = MultiplayerRoom(
        room_code=room_code,
        room_name=room_data.room_name,
        host_user_id=user_id,
        max_players=room_data.max_players,
        category_id=room_data.category_id,
        difficulty_level=room_data.difficulty_level,
        total_questions=room_data.total_questions,
        time_per_question=room_data.time_per_question,
        is_public=room_data.is_public,
        room_password=room_data.room_password,
        current_players=1
    )
    
    db.add(db_room)
    db.flush()
    
    # Add host as participant
    host_participant = RoomParticipant(
        room_id=db_room.id,
        user_id=user_id,
        is_host=True,
        is_ready=False
    )
    
    db.add(host_participant)
    db.commit()
    db.refresh(db_room)
    
    return db_room


def join_room(db: Session, room_code: str, user_id: int, password: Optional[str] = None):
    room = db.query(MultiplayerRoom).filter(
        and_(
            MultiplayerRoom.room_code == room_code,
            MultiplayerRoom.status == "waiting"
        )
    ).first()
    
    if not room:
        raise ValueError("Room not found or not available")
    
    # Check password if required
    if room.room_password and room.room_password != password:
        raise ValueError("Incorrect room password")
    
    # Check if user already in room
    existing = db.query(RoomParticipant).filter(
        and_(
            RoomParticipant.room_id == room.id,
            RoomParticipant.user_id == user_id,
            RoomParticipant.is_active
        )
    ).first()
    
    if existing:
        raise ValueError("You are already in this room")
    
    # Check room capacity
    if room.current_players >= room.max_players:
        raise ValueError("Room is full")
    
    # Add participant
    participant = RoomParticipant(
        room_id=room.id,
        user_id=user_id,
        is_host=False,
        is_ready=False
    )
    
    db.add(participant)
    
    # Update room player count
    room.current_players += 1
    
    db.commit()
    db.refresh(participant)
    
    return participant


def get_room_with_participants(db: Session, room_id: int):
    room = db.query(MultiplayerRoom).filter(MultiplayerRoom.id == room_id).first()
    if not room:
        return None
    
    participants = db.query(RoomParticipant).filter(
        and_(
            RoomParticipant.room_id == room_id,
            RoomParticipant.is_active
        )
    ).all()
    
    return {"room": room, "participants": participants}


def get_room_by_code(db: Session, room_code: str):
    return db.query(MultiplayerRoom).filter(MultiplayerRoom.room_code == room_code).first()


def update_player_ready(db: Session, room_id: int, user_id: int, is_ready: bool):
    participant = db.query(RoomParticipant).filter(
        and_(
            RoomParticipant.room_id == room_id,
            RoomParticipant.user_id == user_id,
            RoomParticipant.is_active
        )
    ).first()
    
    if not participant:
        raise ValueError("Participant not found")
    
    participant.is_ready = is_ready
    db.commit()
    
    # Check if all players are ready
    all_participants = db.query(RoomParticipant).filter(
        and_(
            RoomParticipant.room_id == room_id,
            RoomParticipant.is_active
        )
    ).all()
    
    all_ready = all(p.is_ready for p in all_participants) and len(all_participants) >= 2
    
    return {"participant": participant, "all_ready": all_ready}


def start_game_session(db: Session, room_id: int, question_ids: List[int]):
    room = db.query(MultiplayerRoom).filter(MultiplayerRoom.id == room_id).first()
    if not room:
        raise ValueError("Room not found")
    
    # Create game session
    game_session = GameSession(
        room_id=room_id,
        selected_questions=json.dumps(question_ids),
        current_question_index=0
    )
    
    db.add(game_session)
    
    # Update room status
    room.status = "in_progress"
    
    db.commit()
    db.refresh(game_session)
    
    return game_session


def submit_player_answer(db: Session, room_id: int, user_id: int, answer_data: SubmitAnswerRequest, correct_answer: str, time_limit: int):
    # Get participant
    participant = db.query(RoomParticipant).filter(
        and_(
            RoomParticipant.room_id == room_id,
            RoomParticipant.user_id == user_id,
            RoomParticipant.is_active
        )
    ).first()
    
    if not participant:
        raise ValueError("Participant not found")
    
    # Get current game session
    game_session = db.query(GameSession).filter(
        and_(
            GameSession.room_id == room_id,
            GameSession.status == "active"
        )
    ).first()
    
    if not game_session:
        raise ValueError("No active game session")
    
    # Check if already answered this question
    existing_answer = db.query(PlayerAnswer).filter(
        and_(
            PlayerAnswer.game_session_id == game_session.id,
            PlayerAnswer.participant_id == participant.id,
            PlayerAnswer.question_id == answer_data.question_id
        )
    ).first()
    
    if existing_answer:
        raise ValueError("Already answered this question")
    
    # Calculate score
    is_correct = answer_data.selected_answer == correct_answer
    score = calculate_quiz_score(is_correct, answer_data.time_taken, time_limit)
    
    # Create answer record
    player_answer = PlayerAnswer(
        game_session_id=game_session.id,
        participant_id=participant.id,
        question_id=answer_data.question_id,
        selected_answer=answer_data.selected_answer,
        is_correct=is_correct,
        time_taken=answer_data.time_taken,
        score_earned=score
    )
    
    db.add(player_answer)
    
    # Update participant stats
    participant.total_score += score
    if is_correct:
        participant.correct_answers += 1
    else:
        participant.wrong_answers += 1
    
    # Update average time
    total_answers = participant.correct_answers + participant.wrong_answers
    if total_answers == 1:
        participant.average_time = answer_data.time_taken
    else:
        participant.average_time = ((participant.average_time * (total_answers - 1)) + answer_data.time_taken) / total_answers
    
    db.commit()
    
    return {"answer": player_answer, "participant": participant}


def get_current_question_index(db: Session, room_id: int):
    game_session = db.query(GameSession).filter(
        and_(
            GameSession.room_id == room_id,
            GameSession.status == "active"
        )
    ).first()
    
    return game_session.current_question_index if game_session else 0


def advance_question(db: Session, room_id: int):
    game_session = db.query(GameSession).filter(
        and_(
            GameSession.room_id == room_id,
            GameSession.status == "active"
        )
    ).first()
    
    if game_session:
        game_session.current_question_index += 1
        db.commit()
        return game_session.current_question_index
    
    return 0


def finish_game(db: Session, room_id: int):
    room = db.query(MultiplayerRoom).filter(MultiplayerRoom.id == room_id).first()
    game_session = db.query(GameSession).filter(
        and_(
            GameSession.room_id == room_id,
            GameSession.status == "active"
        )
    ).first()
    
    if room:
        room.status = "finished"
    
    if game_session:
        game_session.status = "finished"
        game_session.finished_at = datetime.utcnow()
    
    db.commit()
    
    return get_final_leaderboard(db, room_id)


def get_final_leaderboard(db: Session, room_id: int):
    participants = db.query(RoomParticipant).filter(
        and_(
            RoomParticipant.room_id == room_id,
            RoomParticipant.is_active
        )
    ).order_by(
        RoomParticipant.total_score.desc(),
        RoomParticipant.correct_answers.desc(),
        RoomParticipant.average_time.asc()
    ).all()
    
    leaderboard = []
    for i, p in enumerate(participants):
        leaderboard.append({
            "rank": i + 1,
            "user_id": p.user_id,
            "total_score": p.total_score,
            "correct_answers": p.correct_answers,
            "wrong_answers": p.wrong_answers,
            "average_time": round(p.average_time, 2)
        })
    
    return leaderboard


def leave_room(db: Session, room_id: int, user_id: int):
    participant = db.query(RoomParticipant).filter(
        and_(
            RoomParticipant.room_id == room_id,
            RoomParticipant.user_id == user_id,
            RoomParticipant.is_active
        )
    ).first()
    
    if not participant:
        return None
    
    # Mark as inactive
    participant.is_active = False
    participant.left_at = datetime.utcnow()
    
    # Update room player count
    room = db.query(MultiplayerRoom).filter(MultiplayerRoom.id == room_id).first()
    if room:
        room.current_players = max(0, room.current_players - 1)
        
        # If host left, assign new host
        if participant.is_host and room.current_players > 0:
            new_host = db.query(RoomParticipant).filter(
                and_(
                    RoomParticipant.room_id == room_id,
                    RoomParticipant.is_active,
                    RoomParticipant.user_id != user_id
                )
            ).first()
            
            if new_host:
                new_host.is_host = True
    
    db.commit()
    return participant


def get_public_rooms(db: Session, skip: int = 0, limit: int = 20):
    return db.query(MultiplayerRoom).filter(
        and_(
            MultiplayerRoom.is_public,
            MultiplayerRoom.status == "waiting",
            MultiplayerRoom.current_players < MultiplayerRoom.max_players
        )
    ).offset(skip).limit(limit).all()
