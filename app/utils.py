"""Utility functions for HRMS application."""


def generate_login_id(first_name: str, last_name: str, phone_no: str) -> str:
    """
    Generates a Login ID combining 4 uppercase letters from the name
    and 4 digits from the phone number.
    Example: Manoj Sarya + 9876543210 -> MANO3210
    """
    first = (first_name or "").strip()
    last = (last_name or "").strip()
    combined_name = f"{first}{last}"

    # Extract alphabetic characters and convert to uppercase
    letters = "".join(c for c in combined_name if c.isalpha()).upper()
    if not letters:
        letters = "EMP"
    name_part = letters[:4]

    # Extract digits from phone number (take first 4 digits)
    digits = "".join(c for c in str(phone_no or "") if c.isdigit())
    phone_part = digits[:4] if len(digits) >= 4 else digits.zfill(4)

    return f"{name_part}{phone_part}"
