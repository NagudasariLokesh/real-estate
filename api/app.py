import os
import json
from flask import Flask, jsonify, request, Response
from flask_cors import CORS
from pymongo import MongoClient
from bson import ObjectId
from bson.errors import InvalidId
import jwt
from datetime import datetime, timezone, timedelta
from functools import wraps

app = Flask(__name__)
CORS(app)

MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/realestate')
JWT_SECRET = os.environ.get('JWT_SECRET', 'your_secret_key_here')

client = MongoClient(MONGO_URI)
db = client.get_default_database()

lands_collection = db.lands
plots_collection = db.plots
plot3d_collection = db.plot3d

class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

def to_json(data):
    return Response(
        json.dumps(data, cls=JSONEncoder),
        mimetype='application/json'
    )

def parse_object_id(id_str):
    try:
        return ObjectId(id_str)
    except InvalidId:
        return None

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return to_json({'message': 'Token is missing'}), 401
        try:
            if token.startswith('Bearer '):
                token = token[7:]
            jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        except:
            return to_json({'message': 'Token is invalid'}), 401
        return f(*args, **kwargs)
    return decorated

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if username == 'admin' and password == 'admin123':
        token = jwt.encode({
            'user': username,
            'exp': datetime.now(timezone.utc) + timedelta(hours=24)
        }, JWT_SECRET, algorithm='HS256')
        return to_json({'token': token})
    
    return to_json({'message': 'Invalid credentials'}), 401

@app.route('/api/lands', methods=['GET'])
def get_lands():
    lands = list(lands_collection.find({}, {'_id': 1, 'name': 1, 'location': 1, 'total_area': 1, 'coordinates': 1}))
    return to_json(lands)

@app.route('/api/lands/<land_id>', methods=['GET'])
def get_land(land_id):
    oid = parse_object_id(land_id)
    if not oid:
        return to_json({'message': 'Invalid land ID'}), 400
    land = lands_collection.find_one({'_id': oid})
    if not land:
        return to_json({'message': 'Land not found'}), 404
    return to_json(land)

@app.route('/api/lands/<land_id>/plots', methods=['GET'])
def get_plots(land_id):
    oid = parse_object_id(land_id)
    if not oid:
        return to_json({'message': 'Invalid land ID'}), 400
    plots = list(plots_collection.find({'land_id': oid}, {'_id': 1, 'plot_number': 1, 'area': 1, 'coordinates': 1, 'status': 1}))
    return to_json(plots)

@app.route('/api/plots/<plot_id>', methods=['GET'])
def get_plot(plot_id):
    oid = parse_object_id(plot_id)
    if not oid:
        return to_json({'message': 'Invalid plot ID'}), 400
    plot = plots_collection.find_one({'_id': oid})
    if not plot:
        return to_json({'message': 'Plot not found'}), 404
    return to_json(plot)

@app.route('/api/plots/<plot_id>/3d', methods=['GET'])
def get_plot_3d(plot_id):
    oid = parse_object_id(plot_id)
    if not oid:
        return to_json({'message': 'Invalid plot ID'}), 400
    plot_3d = plot3d_collection.find_one({'plot_id': oid})
    if not plot_3d:
        return to_json({'message': '3D model not found'}), 404
    return to_json(plot_3d)

@app.route('/api/lands', methods=['POST'])
@token_required
def create_land():
    data = request.get_json()
    land_id = lands_collection.insert_one(data).inserted_id
    return to_json({'_id': str(land_id), 'message': 'Land created'}), 201

@app.route('/api/lands/<land_id>/plots', methods=['POST'])
@token_required
def create_plot(land_id):
    data = request.get_json()
    oid = parse_object_id(land_id)
    if not oid:
        return to_json({'message': 'Invalid land ID'}), 400
    data['land_id'] = oid
    plot_id = plots_collection.insert_one(data).inserted_id
    return to_json({'_id': str(plot_id), 'message': 'Plot created'}), 201

@app.route('/api/plots/<plot_id>/3d', methods=['POST'])
@token_required
def create_plot_3d(plot_id):
    data = request.get_json()
    oid = parse_object_id(plot_id)
    if not oid:
        return to_json({'message': 'Invalid plot ID'}), 400
    data['plot_id'] = oid
    plot3d_id = plot3d_collection.insert_one(data).inserted_id
    return to_json({'_id': str(plot3d_id), 'message': '3D model created'}), 201

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
