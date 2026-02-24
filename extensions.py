# Instâncias das extensões Flask — importadas por app.py e pelos blueprints
# sem causar importação circular.
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address, default_limits=[])
