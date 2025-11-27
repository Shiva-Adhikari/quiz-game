# config/reserved_usernames.py
"""Reserved usernames that cannot be registered by users."""

RESERVED_USERNAMES = {
    # Tech companies
    "microsoft", "google", "apple", "amazon", "facebook", "meta",
    "twitter", "instagram", "youtube", "netflix", "spotify",
    
    # System reserved
    "admin", "administrator", "root", "system", "mod", "moderator",
    "support", "help", "api", "webmaster", "postmaster",
    
    # Protocol/Technical
    "www", "mail", "ftp", "smtp", "localhost", "api",
    
    # Generic reserved
    "official", "verified", "staff", "team", "about", "contact",
    "terms", "privacy", "legal", "billing",
    
    # Custom
    "brainbattle", "quiz", "quizgame", "brainwave",
}
