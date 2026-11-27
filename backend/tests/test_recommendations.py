from conftest import auth_header
from app.database import SessionLocal
from app.models import Pattern, PatternImage


def test_recommendations_require_login(client):
    assert client.get('/api/me/recommendations').status_code == 401


def test_preferences_exclusion_and_cold_start(client, user_token, admin_token):
    headers = auth_header(user_token)
    cold = client.get('/api/me/recommendations', headers=headers).json()
    assert cold['interactionCount'] == 0
    assert cold['items']
    with SessionLocal() as db:
        db.add(Pattern(id='similar-cloud', catalog='SIMILAR', name='云纹参考',
                       motif_type='云纹', dynasty='清', carrier='织锦',
                       source='manual', source_id='similar', has_image=True))
        db.flush()
        db.add(PatternImage(pattern_id='similar-cloud', external_url='https://example.com/image.jpg'))
        db.commit()
    response = client.post('/api/me/favorites/cleveland-101142', headers=headers)
    assert response.status_code == 201
    result = client.get('/api/me/recommendations', headers=headers).json()
    assert result['personalizationWeight'] == 0.08
    assert result['items'][0]['id'] == 'similar-cloud'
    assert result['items'][0]['contentScore'] == 1
    assert '云纹' in result['items'][0]['reason']
    assert 'cleveland-101142' not in {item['id'] for item in result['items']}
    other = client.get('/api/me/recommendations', headers=auth_header(admin_token)).json()
    assert other['interactionCount'] == 0
    assert client.get('/api/me/recommendations?limit=0', headers=headers).status_code == 422
    assert client.delete('/api/me/favorites/cleveland-101142', headers=headers).status_code == 204
    assert client.get('/api/me/recommendations', headers=headers).json()['interactionCount'] == 0
