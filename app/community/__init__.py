from flask import Blueprint

community_bp = Blueprint('community', __name__)

from app.community import routes
