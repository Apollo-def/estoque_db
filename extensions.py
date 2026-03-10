# Flask Extensions Configuration
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Initialize CSRF protection
csrf = CSRFProtect()

# Initialize Flask-Limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)
