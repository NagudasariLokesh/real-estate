import os
import sys
import pytest
from unittest.mock import Mock, patch, MagicMock
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'api'))

os.environ['MONGO_URI'] = 'mongodb://localhost:27017/test'
os.environ['JWT_SECRET'] = 'test_secret_key'

VALID_OID = '507f1f77bcf86cd799439011'

with patch('pymongo.MongoClient'):
    import app


@pytest.fixture
def client():
    app.app.config['TESTING'] = True
    with app.app.test_client() as client:
        yield client


class TestHealthCheck:
    def test_app_exists(self, client):
        assert app.app is not None


class TestAuth:
    @patch('app.lands_collection')
    def test_login_success(self, mock_lands, client):
        response = client.post('/api/auth/login',
            json={'username': 'admin', 'password': 'admin123'},
            content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'token' in data

    @patch('app.lands_collection')
    def test_login_invalid_credentials(self, mock_lands, client):
        response = client.post('/api/auth/login',
            json={'username': 'wrong', 'password': 'wrong'},
            content_type='application/json')
        
        assert response.status_code == 401


class TestLands:
    @patch('app.lands_collection')
    def test_get_lands_empty(self, mock_lands, client):
        mock_lands.find.return_value = []
        
        response = client.get('/api/lands')
        
        assert response.status_code == 200

    @patch('app.lands_collection')
    def test_get_land_invalid_id(self, mock_lands, client):
        response = client.get('/api/lands/123')
        
        assert response.status_code == 400

    @patch('app.lands_collection')
    def test_get_land_not_found(self, mock_lands, client):
        mock_lands.find_one.return_value = None
        
        response = client.get(f'/api/lands/{VALID_OID}')
        
        assert response.status_code == 404


class TestPlots:
    @patch('app.plots_collection')
    def test_get_plots_empty(self, mock_plots, client):
        mock_plots.find.return_value = []
        
        response = client.get(f'/api/lands/{VALID_OID}/plots')
        
        assert response.status_code == 200

    @patch('app.plots_collection')
    def test_get_plots_invalid_id(self, mock_plots, client):
        response = client.get('/api/lands/123/plots')
        
        assert response.status_code == 400

    @patch('app.plots_collection')
    def test_get_plot_invalid_id(self, mock_plots, client):
        response = client.get('/api/plots/123')
        
        assert response.status_code == 400

    @patch('app.plots_collection')
    def test_get_plot_not_found(self, mock_plots, client):
        mock_plots.find_one.return_value = None
        
        response = client.get(f'/api/plots/{VALID_OID}')
        
        assert response.status_code == 404


class TestPlot3D:
    @patch('app.plot3d_collection')
    def test_get_plot_3d_invalid_id(self, mock_plot3d, client):
        response = client.get('/api/plots/123/3d')
        
        assert response.status_code == 400

    @patch('app.plot3d_collection')
    def test_get_plot_3d_not_found(self, mock_plot3d, client):
        mock_plot3d.find_one.return_value = None
        
        response = client.get(f'/api/plots/{VALID_OID}/3d')
        
        assert response.status_code == 404


class TestTokenRequired:
    @patch('app.lands_collection')
    def test_create_land_without_token(self, mock_lands, client):
        response = client.post('/api/lands',
            json={'name': 'New Land'},
            content_type='application/json')
        
        assert response.status_code == 401


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
