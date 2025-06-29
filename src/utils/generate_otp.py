# Standard library imports
import random


def generate_otp() -> int:
    return int(random.randint(100000, 999999))  # 6-digit OTP
