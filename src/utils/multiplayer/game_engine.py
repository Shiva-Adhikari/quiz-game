import asyncio
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import json
from src.utils.multiplayer.crud import advance_question, finish_game, get_final_leaderboard
from src.utils.multiplayer.websocket_manager import manager
from typing import List, Dict


class MultiplayerGameEngine:
    def __init__(self, room_id: int, db: Session):
        self.room_id = room_id
        self.db = db
        self.current_question_index = 0
        self.question_timer_task = None
        self.players_answered = set()
        self.question_start_time = None
        self.questions = []
        self.total_questions = 0
    
    async def start_game(self, questions: List[dict], time_per_question: int):
        self.questions = questions
        self.total_questions = len(questions)
        self.time_per_question = time_per_question
        
        # Notify all players game is starting
        await manager.send_to_room(self.room_id, "game_starting", {
            "total_questions": self.total_questions,
            "time_per_question": time_per_question
        })
        
        # Wait a moment then send first question
        await asyncio.sleep(3)
        await self.send_current_question()
    
    async def send_current_question(self):
        if self.current_question_index >= len(self.questions):
            await self.finish_game()
            return
        
        question = self.questions[self.current_question_index]
        self.question_start_time = datetime.utcnow()
        self.players_answered.clear()
        
        question_data = {
            "id": question["id"],
            "question_text": question["question_text"],
            "option_a": question["option_a"],
            "option_b": question["option_b"],
            "option_c": question["option_c"],
            "option_d": question["option_d"],
            "question_index": self.current_question_index + 1,
            "total_questions": self.total_questions,
            "time_limit": self.time_per_question
        }
        
        await manager.send_to_room(self.room_id, "question_sent", question_data)
        
        # Start question timer
        self.question_timer_task = asyncio.create_task(
            self.question_timeout()
        )
    
    async def process_player_answer(self, user_id: int, answer_data: dict):
        if user_id in self.players_answered:
            return False
        
        self.players_answered.add(user_id)
        
        # Broadcast that player answered
        await manager.send_to_room(self.room_id, "player_answered", {
            "user_id": user_id,
            "answered_count": len(self.players_answered)
        })
        
        # Check if all players answered
        from crud import get_room_with_participants
        room_data = get_room_with_participants(self.db, self.room_id)
        total_active_players = len(room_data["participants"])
        
        if len(self.players_answered) >= total_active_players:
            # Cancel timer and advance immediately
            if self.question_timer_task and not self.question_timer_task.done():
                self.question_timer_task.cancel()
            await self.finish_current_question()
        
        return True
    
    async def finish_current_question(self):
        # Get correct answer for current question
        current_question = self.questions[self.current_question_index]
        correct_answer = current_question["correct_answer"]
        
        # Get current scores
        from crud import get_room_with_participants
        room_data = get_room_with_participants(self.db, self.room_id)
        
        player_scores = []
        for participant in room_data["participants"]:
            player_scores.append({
                "user_id": participant.user_id,
                "score": participant.total_score,
                "correct_answers": participant.correct_answers
            })
        
        # Send question results
        await manager.send_to_room(self.room_id, "question_results", {
            "question_id": current_question["id"],
            "correct_answer": correct_answer,
            "explanation": current_question.get("explanation", ""),
            "player_scores": player_scores
        })
        
        # Wait a moment for players to see results
        await asyncio.sleep(4)
        
        # Advance to next question
        self.current_question_index += 1
        advance_question(self.db, self.room_id)
        
        if self.current_question_index >= len(self.questions):
            await self.finish_game()
        else:
            await self.send_current_question()
    
    async def question_timeout(self):
        # Wait for the question time limit
        await asyncio.sleep(self.time_per_question + 2)  # 2 second buffer
        await self.finish_current_question()
    
    async def finish_game(self):
        # Calculate final results
        leaderboard = finish_game(self.db, self.room_id)
        
        # Send final results
        await manager.send_to_room(self.room_id, "game_finished", {
            "leaderboard": leaderboard,
            "game_duration": (datetime.utcnow() - self.question_start_time).total_seconds() if self.question_start_time else 0
        })
        
        # Clean up
        if self.question_timer_task and not self.question_timer_task.done():
            self.question_timer_task.cancel()
