from flask import Blueprint

bp = Blueprint('elementary', __name__)

from app.elementary import routes