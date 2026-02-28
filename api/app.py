import os
import json
from flask import Flask, jsonify, request
from flask_cors import CORS
from pymongo import MongoClient
from bson import ObjectId
import jwt
from datetime import datetime, timedelta
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

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        try:
            if token.startswith('Bearer '):
                token = token[7:]
            jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        except:
            return jsonify({'message': 'Token is invalid'}), 401
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
            'exp': datetime.utcnow() + timedelta(hours=24)
        }, JWT_SECRET, algorithm='HS256')
        return jsonify({'token': token})
    
    return jsonify({'message': 'Invalid credentials'}), 401

@app.route('/api/lands', methods=['GET'])
def get_lands():
    lands = list(lands_collection.find({}, {'_id': 1, 'name': 1, 'location': 1, 'total_area': 1, 'coordinates': 1}))
    return jsonify(lands, cls=JSONEncoder)

@app.route('/api/lands/<land_id>', methods=['GET'])
def get_land(land_id):
    land = lands_collection.find_one({'_id': ObjectId(land_id)})
    if not land:
        return jsonify({'message': 'Land not found'}), 404
    return jsonify(land, cls=JSONEncoder)

@app.route('/api/lands/<land_id>/plots', methods=['GET'])
def get_plots(land_id):
    plots = list(plots_collection.find({'land_id': ObjectId(land_id)}, {'_id': 1, 'plot_number': 1, 'area': 1, 'coordinates': 1, 'status': 1}))
    return jsonify(plots, cls=JSONEncoder)

@app.route('/api/plots/<plot_id>', methods=['GET'])
def get_plot(plot_id):
    plot = plots_collection.find_one({'_id': ObjectId(plot_id)})
    if not plot:
        return jsonify({'message': 'Plot not found'}), 404
    return jsonify(plot, cls=JSONEncoder)

@app.route('/api/plots/<plot_id>/3d', methods=['GET'])
def get_plot_3d(plot_id):
    plot_3d = plot3d_collection.find_one({'plot_id': ObjectId(plot_id)})
    if not plot_3d:
        return jsonify({'message': '3D model not found'}), 404
    return jsonify(plot_3d, cls=JSONEncoder)

@app.route('/api/lands', methods=['POST'])
@token_required
def create_land():
    data = request.get_json()
    land_id = lands_collection.insert_one(data).inserted_id
    return jsonify({'_id': str(land_id), 'message': 'Land created'}), 201

@app.route('/api/lands/<land_id>/plots', methods=['POST'])
@token_required
def create_plot(land_id):
    data = request.get_json()
    data['land_id'] = ObjectId(land_id)
    plot_id = plots_collection.insert_one(data).inserted_id
    return jsonify({'_id': str(plot_id), 'message': 'Plot created'}), 201

@app.route('/api/plots/<plot_id>/3d', methods=['POST'])
@token_required
def create_plot_3d(plot_id):
    data = request.get_json()
    data['plot_id'] = ObjectId(plot_id)
    plot3d_id = plot3d_collection.insert_one(data).inserted_id
    return jsonify({'_id': str(plot3d_id), 'message': '3D model created'}), 201

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
