import pytest
from app import app
import os
import json
from unittest.mock import patch, MagicMock

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health_check(client):
    response = client.get('/health')
    assert response.status_code == 200
    assert 'status' in response.json
    assert response.json['status'] == 'healthy'

@pytest.mark.asyncio
async def test_stt_stream():
    with patch('deepgram.Deepgram') as mock_dg:
        mock_dg.return_value.transcription.live.v.return_value.listen = MagicMock()
        # Add your test implementation here

@pytest.mark.asyncio
async def test_tts_stream():
    with patch('app.get_tts_stream') as mock_tts:
        mock_tts.return_value = MagicMock()
        # Add your test implementation here

def test_rate_limiting(client):
    # Test rate limiting functionality
    for _ in range(101):  # Exceed the rate limit
        response = client.post('/api/v1/stt/stream')
    assert response.status_code == 429 