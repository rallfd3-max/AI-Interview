def test_ping_person_left_and_recognition(enrolled, encoded):
    with enrolled.websocket_connect('/ws/recognition') as socket:
        socket.send_json({'type': 'ping', 'request_id': 'ping1'})
        assert socket.receive_json()['type'] == 'pong'
        for i in range(3):
            socket.send_json({'type': 'recognize', 'request_id': f'r{i}', 'session_id': 's', 'image_base64': encoded})
            result = socket.receive_json()
            assert result['stability']['consistent_frames'] == i + 1
            assert result['matched'] is (i == 2)
        assert result['stability']['confirmed']
        socket.send_json({'type': 'person_left', 'session_id': 's'})
        assert socket.receive_json()['type'] == 'clear'
        socket.send_json({'type': 'recognize', 'request_id': 'r0', 'session_id': 's', 'image_base64': encoded})
        assert socket.receive_json()['stability']['consistent_frames'] == 1


def test_ws_invalid_messages(client):
    with client.websocket_connect('/ws/recognition') as socket:
        for value in ['bad', '[]', '{"type":"unknown"}']:
            socket.send_text(value)
            assert socket.receive_json()['error']['code'] == 'INVALID_REQUEST'
        socket.send_json({'type': 'recognize', 'image_base64': '!!!', 'request_id': 'bad'})
        result = socket.receive_json()
        assert result['request_id'] == 'bad'
        assert result['error']['code'] == 'INVALID_BASE64'


def test_ws_rate_limit(client):
    client.app.state.runtime.settings.max_requests_per_second = 1
    with client.websocket_connect('/ws/recognition') as socket:
        socket.send_json({'type': 'ping'})
        assert socket.receive_json()['type'] == 'pong'
        socket.send_json({'type': 'ping'})
        assert socket.receive_json()['error']['code'] == 'RATE_LIMITED'


def test_legacy_glasses_photo_and_departure(enrolled, encoded):
    with enrolled.websocket_connect('/ws/recognition', headers={'X-Device-Id': 'legacy-glass'}) as socket:
        socket.send_json({'type': 'face', 'img': encoded, 'request_id': 'legacy-photo',
                          'face_count': 1, 'face_box': [0, 0, 32, 24]})
        result = socket.receive_json()
        assert result['type'] == 'person_info'
        assert result['id'] == 'student_001'
        assert result['name'] == '测试同学'
        assert result['request_id'] == 'legacy-photo'
        socket.send_json({'type': 'event', 'event': 'person_left'})
        assert socket.receive_json()['type'] == 'clear'


def test_legacy_empty_library_and_invalid_photo(client, encoded):
    with client.websocket_connect('/ws/recognition') as socket:
        socket.send_json({'type': 'face', 'img': encoded})
        result = socket.receive_json()
        assert result['type'] == 'error'
        assert result['code'] == 'unknown_face'
        socket.send_json({'type': 'face', 'img': '!!!', 'request_id': 'invalid-legacy'})
        result = socket.receive_json()
        assert result['type'] == 'error'
        assert result['code'] == 'INVALID_BASE64'
        assert result['request_id'] == 'invalid-legacy'


def test_audio_does_not_break_photo_connection(enrolled, encoded):
    with enrolled.websocket_connect('/ws/recognition') as socket:
        socket.send_json({'type': 'audio', 'data': 'audio-bytes', 'duration_ms': 1000})
        result = socket.receive_json()
        assert result['type'] == 'error'
        assert result['code'] == 'UNSUPPORTED_MESSAGE_TYPE'
        socket.send_json({'type': 'recognize', 'image_base64': encoded,
                          'request_id': 'photo-after-audio', 'stable_frames': 1})
        result = socket.receive_json()
        assert result['matched'] is True
        assert result['person']['person_id'] == 'student_001'


def test_current_glasses_payload(enrolled, encoded):
    with enrolled.websocket_connect('/ws/recognition') as socket:
        socket.send_json({'type': 'recognize', 'request_id': 'photo-001',
                          'device_id': 'phone-001', 'session_id': 'session-001',
                          'image_format': 'jpeg', 'image_base64': encoded, 'stable_frames': 1})
        result = socket.receive_json()
        assert result['type'] == 'recognition_result'
        assert result['request_id'] == 'photo-001'
        assert result['stability']['confirmed'] is True
        assert result['person']['person_id'] == 'student_001'
