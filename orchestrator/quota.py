"""Classify usage-limit errors without exposing credentials."""
import re
from datetime import datetime, timedelta, timezone
PATTERNS = (r"rate.limit", r"usage.limit", r"quota.exceeded", r"too.many.requests", r"try.again.later", r"limit.reached")
def exceeded(text):
    return any(re.search(p, text, re.I) for p in PATTERNS)
def retry_after(minutes=60):
    return (datetime.now(timezone.utc) + timedelta(minutes=minutes)).isoformat()
