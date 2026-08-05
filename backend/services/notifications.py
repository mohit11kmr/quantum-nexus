import logging

def send_alert(message: str, platform: str = "all") -> bool:
    """Telegram + Discord notification sender (placeholder)."""
    logging.info(f"Sending {platform} alert: {message}")
    print(f"[ALERT - {platform}] {message}")
    return True
