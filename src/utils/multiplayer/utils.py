import string
import secrets


def generate_room_code(length: int = 8) -> str:
    """Generate unique room code like 'ABC123XY'"""
    # Mix of uppercase letters and numbers
    chars = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))


def calculate_quiz_score(is_correct: bool, time_taken: float, max_time: int) -> int:
    """Calculate score based on correctness and speed"""
    if not is_correct:
        return 0

    base_score = 100

    # Speed bonus: faster answers get more points
    remaining_time = max(0, max_time - time_taken)
    speed_bonus = int((remaining_time / max_time) * 50)

    return base_score + speed_bonus


def validate_room_capacity(current_players: int, max_players: int) -> bool:
    """Check if room can accept new player"""
    return current_players < max_players
