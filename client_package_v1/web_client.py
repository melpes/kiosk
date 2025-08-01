#!/usr/bin/env python3
"""
웹 기반 실시간 음성 클라이언트
"""

import sys
import json
import threading
import os
import time
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit

# 클라이언트 패키지 경로 추가
sys.path.insert(0, str(Path(__file__).parent))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'realtime-voice-client-secret'
socketio = SocketIO(app, cors_allowed_origins="*", logger=False, engineio_logger=False)

# 전역 클라이언트 인스턴스
client_instance = None
client_lock = threading.Lock()

class WebRealTimeClient:
    """웹 인터페이스용 실시간 클라이언트 래퍼"""
    
    def __init__(self, config_path="config.json"):
        self.config_path = config_path
        self.client = None
        self.is_running = False
        self.session_thread = None
        self.stop_event = threading.Event()
        self.load_config()
    
    def load_config(self):
        """설정 파일 로드"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config_data = json.load(f)
            print(f"✅ 설정 파일 로드 완료: {self.config_path}")
            print(f"🔗 서버 URL: {self.config_data.get('server', {}).get('url', 'Unknown')}")
        except Exception as e:
            print(f"⚠️ 설정 파일 로드 실패: {e}, 기본 설정 사용")
            self.config_data = {
                "server": {"url": "http://localhost:8001"},
                "audio": {"temp_dir": "temp_audio"}
            }
    
    def initialize_client(self):
        """클라이언트 초기화"""
        try:
            print("🔄 클라이언트 초기화 시작...")
            from examples.complete_realtime_client import CompleteRealTimeClient
            self.client = CompleteRealTimeClient(self.config_path)
            print("✅ 클라이언트 초기화 완료")
            return True
        except ImportError as e:
            error_msg = f'클라이언트 모듈 import 실패: {str(e)}'
            print(f"❌ {error_msg}")
            socketio.emit('error', {'message': error_msg})
            return False
        except Exception as e:
            error_msg = f'클라이언트 초기화 실패: {str(e)}'
            print(f"❌ {error_msg}")
            socketio.emit('error', {'message': error_msg})
            return False
    
    def start_session(self):
        """실시간 세션 시작"""
        if not self.client:
            if not self.initialize_client():
                return False
        
        try:
            # 서버 연결 확인
            if not self.client.check_server_connection():
                socketio.emit('error', {'message': f'서버 연결 실패: {self.config_data["server"]["url"]}'})
                return False
            
            # 마이크 테스트
            if not self.client.test_microphone_system():
                socketio.emit('warning', {'message': '마이크 테스트 실패했지만 계속 진행합니다'})
            
            # 콜백 설정
            self.setup_web_callbacks()
            
            # 세션 시작
            self.is_running = True
            self.stop_event.clear()
            socketio.emit('status', {'message': '실시간 음성 세션이 시작되었습니다', 'running': True})
            
            # 별도 스레드에서 실행
            self.session_thread = threading.Thread(target=self._run_session, daemon=True)
            self.session_thread.start()
            return True
            
        except Exception as e:
            socketio.emit('error', {'message': f'세션 시작 실패: {str(e)}'})
            return False
    
    def setup_web_callbacks(self):
        """웹 인터페이스용 콜백 설정"""
        def on_transcription(text, confidence=None):
            data = {'text': text}
            if confidence:
                data['confidence'] = confidence
            socketio.emit('transcription', data)
        
        def on_response(response_data):
            # 응답 데이터가 딕셔너리인 경우 처리
            if isinstance(response_data, dict):
                socketio.emit('response', response_data)
            else:
                socketio.emit('response', {'text': str(response_data)})
        
        def on_audio_received(audio_path, audio_type='tts'):
            try:
                # 오디오 파일 존재 확인
                if not os.path.exists(audio_path):
                    socketio.emit('error', {'message': f'오디오 파일을 찾을 수 없습니다: {audio_path}'})
                    return
                
                # 파일명 추출
                filename = os.path.basename(audio_path)
                
                # 오디오 파일 정보 전송
                audio_info = {
                    'path': audio_path,
                    'filename': filename,
                    'type': audio_type,
                    'url': f'/audio/{filename}',
                    'timestamp': time.time(),
                    'size': os.path.getsize(audio_path) if os.path.exists(audio_path) else 0
                }
                
                print(f"🔊 TTS 오디오 전송: {audio_info}")  # 디버그 로그
                socketio.emit('audio', audio_info)
                
            except Exception as e:
                socketio.emit('error', {'message': f'오디오 처리 오류: {str(e)}'})
        
        def on_server_info(info):
            # 서버 정보 전송
            socketio.emit('server_info', info)
        
        def on_processing_status(status):
            # 처리 상태 전송
            socketio.emit('processing_status', status)
        
        # 콜백 등록 - 다양한 방식으로 시도
        try:
            if hasattr(self.client, 'setup_callbacks'):
                self.client.setup_callbacks()
            
            # 직접 콜백 설정
            if hasattr(self.client, 'on_transcription'):
                self.client.on_transcription = on_transcription
            if hasattr(self.client, 'on_response'):
                self.client.on_response = on_response
            if hasattr(self.client, 'on_audio_received'):
                self.client.on_audio_received = on_audio_received
            if hasattr(self.client, 'on_server_info'):
                self.client.on_server_info = on_server_info
            if hasattr(self.client, 'on_processing_status'):
                self.client.on_processing_status = on_processing_status
            
            # 콜백 딕셔너리 방식
            if hasattr(self.client, 'callbacks'):
                self.client.callbacks.update({
                    'transcription': on_transcription,
                    'response': on_response,
                    'audio_received': on_audio_received,
                    'server_info': on_server_info,
                    'processing_status': on_processing_status
                })
            
            # 이벤트 핸들러 방식
            if hasattr(self.client, 'add_event_handler'):
                self.client.add_event_handler('transcription', on_transcription)
                self.client.add_event_handler('response', on_response)
                self.client.add_event_handler('audio_received', on_audio_received)
                self.client.add_event_handler('server_info', on_server_info)
                self.client.add_event_handler('processing_status', on_processing_status)
                
        except Exception as e:
            print(f"콜백 설정 오류: {e}")
            socketio.emit('warning', {'message': f'콜백 설정 중 오류: {str(e)}'})
    
    def _run_session(self):
        """세션 실행 (별도 스레드)"""
        try:
            # 세션 실행 루프
            while self.is_running and not self.stop_event.is_set():
                try:
                    if hasattr(self.client, 'process_audio_chunk'):
                        # 오디오 청크 처리 방식
                        self.client.process_audio_chunk()
                    elif hasattr(self.client, 'run_interactive_session'):
                        # 기존 방식 - 웹용으로 수정된 실행
                        self._run_interactive_web_session()
                        break  # 기존 방식은 한 번만 실행
                    else:
                        # 기본 대기
                        time.sleep(0.1)
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    socketio.emit('error', {'message': f'세션 처리 중 오류: {str(e)}'})
                    time.sleep(1)  # 오류 후 잠시 대기
                    
        except Exception as e:
            socketio.emit('error', {'message': f'세션 실행 중 오류: {str(e)}'})
        finally:
            self.is_running = False
            socketio.emit('status', {'message': '세션이 종료되었습니다', 'running': False})
    
    def _run_interactive_web_session(self):
        """웹용 인터랙티브 세션 실행"""
        try:
            # 원본 메서드들을 패치하여 웹 콜백 연결
            original_methods = {}
            
            # TTS 관련 메서드 패치
            if hasattr(self.client, '_play_tts_response'):
                original_methods['_play_tts_response'] = self.client._play_tts_response
                self.client._play_tts_response = self._web_play_tts_response
            
            if hasattr(self.client, 'play_tts_audio'):
                original_methods['play_tts_audio'] = self.client.play_tts_audio
                self.client.play_tts_audio = self._web_play_tts_audio
            
            # 마이크 매니저의 콜백 설정
            if hasattr(self.client, 'mic_manager') and hasattr(self.client.mic_manager, 'set_callbacks'):
                def on_audio_ready(audio_file_path):
                    socketio.emit('info', {'message': f'🎵 음성 파일 생성: {os.path.basename(audio_file_path)}'})
                
                self.client.mic_manager.set_callbacks(
                    on_audio_ready=on_audio_ready,
                    on_response_received=self._web_response_callback
                )
            
            # 원본 세션 실행
            self.client.run_interactive_session()
            
            # 원본 메서드 복원
            for method_name, original_method in original_methods.items():
                setattr(self.client, method_name, original_method)
                
        except Exception as e:
            socketio.emit('error', {'message': f'웹 세션 실행 오류: {str(e)}'})
    
    def _web_play_tts_response(self, tts_url):
        """웹용 TTS 응답 재생 (원본 메서드 오버라이드)"""
        try:
            print(f"🔊 웹 TTS URL 처리: {tts_url}")
            
            # TTS 파일 다운로드
            if hasattr(self.client.voice_client, 'download_tts_file'):
                tts_file_path = self.client.voice_client.download_tts_file(tts_url)
                if tts_file_path and os.path.exists(tts_file_path):
                    print(f"🔊 TTS 파일 다운로드 완료: {tts_file_path}")
                    
                    # 웹으로 오디오 정보 전송
                    filename = os.path.basename(tts_file_path)
                    audio_info = {
                        'path': tts_file_path,
                        'filename': filename,
                        'type': 'tts',
                        'url': f'/audio/{filename}',
                        'timestamp': time.time(),
                        'size': os.path.getsize(tts_file_path),
                        'original_url': tts_url
                    }
                    
                    print(f"🔊 TTS 오디오 정보 전송: {audio_info}")
                    socketio.emit('audio', audio_info)
                else:
                    socketio.emit('error', {'message': f'TTS 파일 다운로드 실패: {tts_url}'})
            else:
                socketio.emit('error', {'message': 'TTS 다운로드 기능을 사용할 수 없습니다'})
            
        except Exception as e:
            print(f"❌ 웹 TTS 처리 오류: {e}")
            socketio.emit('error', {'message': f'TTS 처리 오류: {str(e)}'})
    
    def _web_play_tts_audio(self, audio_path, *args, **kwargs):
        """웹용 TTS 오디오 재생 (로컬 파일)"""
        try:
            print(f"🔊 웹 TTS 재생 요청: {audio_path}")
            
            # 오디오 파일 존재 확인
            if not os.path.exists(audio_path):
                socketio.emit('error', {'message': f'TTS 오디오 파일을 찾을 수 없습니다: {audio_path}'})
                return
            
            # 웹으로 오디오 정보 전송
            filename = os.path.basename(audio_path)
            audio_info = {
                'path': audio_path,
                'filename': filename,
                'type': 'tts',
                'url': f'/audio/{filename}',
                'timestamp': time.time(),
                'size': os.path.getsize(audio_path)
            }
            
            print(f"🔊 TTS 오디오 정보 전송: {audio_info}")
            socketio.emit('audio', audio_info)
            
        except Exception as e:
            print(f"❌ 웹 TTS 재생 오류: {e}")
            socketio.emit('error', {'message': f'TTS 재생 오류: {str(e)}'})
    
    def _web_response_callback(self, response):
        """웹용 응답 콜백 (실제 클라이언트의 on_response_received 대체)"""
        try:
            print(f"🔄 웹 응답 콜백 호출: {type(response)}")
            
            # 응답 객체 처리
            if hasattr(response, 'success'):
                # 성공적인 응답
                if response.success:
                    response_data = {
                        'success': True,
                        'message': response.message if hasattr(response, 'message') else '',
                        'timestamp': time.time()
                    }
                    
                    # 주문 데이터 추가
                    if hasattr(response, 'order_data') and response.order_data:
                        response_data['order_data'] = response.order_data
                    
                    # UI 액션 추가
                    if hasattr(response, 'ui_actions') and response.ui_actions:
                        response_data['ui_actions'] = [
                            action.action_type for action in response.ui_actions
                        ]
                    
                    socketio.emit('response', response_data)
                    
                    # TTS 오디오 URL 처리
                    if hasattr(response, 'tts_audio_url') and response.tts_audio_url:
                        print(f"🔊 TTS URL 발견: {response.tts_audio_url}")
                        self._web_play_tts_response(response.tts_audio_url)
                
                else:
                    # 실패 응답
                    error_msg = response.error_info.error_message if hasattr(response, 'error_info') and response.error_info else '알 수 없는 오류'
                    socketio.emit('error', {'message': f'서버 오류: {error_msg}'})
                    
                    # 복구 방법 제안
                    if hasattr(response, 'error_info') and response.error_info and hasattr(response.error_info, 'recovery_actions'):
                        recovery_actions = response.error_info.recovery_actions
                        socketio.emit('info', {'message': f'복구 방법: {", ".join(recovery_actions)}'})
            
            else:
                # 단순 응답 처리
                if isinstance(response, dict):
                    socketio.emit('response', response)
                else:
                    socketio.emit('response', {'text': str(response)})
            
        except Exception as e:
            print(f"❌ 웹 응답 콜백 오류: {e}")
            socketio.emit('error', {'message': f'응답 처리 오류: {str(e)}'})
    
    def stop_session(self):
        """세션 중지"""
        self.is_running = False
        self.stop_event.set()
        
        # 클라이언트 중지
        if self.client:
            if hasattr(self.client, 'stop'):
                self.client.stop()
            if hasattr(self.client, 'cleanup'):
                self.client.cleanup()
        
        # 스레드 종료 대기
        if self.session_thread and self.session_thread.is_alive():
            self.session_thread.join(timeout=2.0)
        
        socketio.emit('status', {'message': '세션이 중지되었습니다', 'running': False})

# 전역 클라이언트 초기화 (지연 초기화)
web_client = None

def get_web_client():
    """웹 클라이언트 인스턴스 가져오기 (지연 초기화)"""
    global web_client
    if web_client is None:
        try:
            web_client = WebRealTimeClient()
            print("✅ 웹 클라이언트 초기화 완료")
        except Exception as e:
            print(f"❌ 웹 클라이언트 초기화 실패: {e}")
            # 기본 설정으로 재시도
            web_client = WebRealTimeClient()
    return web_client

@app.route('/')
def index():
    """메인 페이지"""
    return render_template('index.html')

@app.route('/favicon.ico')
def favicon():
    """Favicon 처리"""
    return '', 204  # No Content

@app.route('/test')
def test_page():
    """테스트 페이지"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>웹소켓 연결 테스트</title>
    </head>
    <body>
        <h1>웹소켓 연결 테스트</h1>
        <div id="status">연결 중...</div>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
        <script>
            const socket = io();
            socket.on('connect', function() {
                document.getElementById('status').innerHTML = '✅ 웹소켓 연결 성공!';
                console.log('웹소켓 연결됨');
            });
            socket.on('disconnect', function() {
                document.getElementById('status').innerHTML = '❌ 웹소켓 연결 해제됨';
                console.log('웹소켓 연결 해제됨');
            });
        </script>
    </body>
    </html>
    '''

@app.route('/config')
def get_config():
    """현재 설정 반환"""
    try:
        client = get_web_client()
        print(f"📋 설정 조회 요청: {client.config_data}")
        return jsonify(client.config_data)
    except Exception as e:
        print(f"❌ 설정 조회 실패: {e}")
        # 기본 설정 반환
        default_config = {
            "server": {"url": "http://localhost:8001"},
            "audio": {"temp_dir": "temp_audio"}
        }
        return jsonify(default_config)

@app.route('/config', methods=['POST'])
def update_config():
    """설정 업데이트"""
    try:
        client = get_web_client()
        new_config = request.json
        client.config_data.update(new_config)
        
        # 설정 파일 저장
        with open(client.config_path, 'w', encoding='utf-8') as f:
            json.dump(client.config_data, f, indent=2, ensure_ascii=False)
        
        return jsonify({'success': True, 'message': '설정이 업데이트되었습니다'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'설정 업데이트 실패: {str(e)}'})

@app.route('/audio/<filename>')
def serve_audio(filename):
    """오디오 파일 서빙"""
    try:
        client = get_web_client()
        # 여러 경로에서 오디오 파일 찾기
        possible_dirs = [
            client.config_data.get('audio', {}).get('temp_dir', 'temp_audio'),
            'temp_audio',
            'audio',
            '.',  # 현재 디렉토리
        ]
        
        for audio_dir in possible_dirs:
            if not os.path.exists(audio_dir):
                continue
                
            file_path = os.path.join(audio_dir, filename)
            if os.path.exists(file_path):
                print(f"🔊 오디오 파일 서빙: {file_path}")
                response = send_from_directory(audio_dir, filename)
                # CORS 헤더 추가
                response.headers['Access-Control-Allow-Origin'] = '*'
                response.headers['Cache-Control'] = 'no-cache'
                return response
        
        # 파일을 찾지 못한 경우
        print(f"❌ 오디오 파일을 찾을 수 없음: {filename}")
        print(f"검색한 디렉토리: {possible_dirs}")
        return jsonify({'error': f'오디오 파일을 찾을 수 없습니다: {filename}'}), 404
        
    except Exception as e:
        print(f"❌ 오디오 서빙 오류: {e}")
        return jsonify({'error': f'오디오 파일 서빙 오류: {str(e)}'}), 500

@app.route('/server-status')
def server_status():
    """서버 상태 확인"""
    try:
        client = get_web_client()
        if client.client and hasattr(client.client, 'check_server_connection'):
            is_connected = client.client.check_server_connection()
            server_url = client.config_data.get('server', {}).get('url', 'Unknown')
            return jsonify({
                'connected': is_connected,
                'server_url': server_url,
                'session_running': client.is_running
            })
        else:
            return jsonify({
                'connected': False,
                'server_url': client.config_data.get('server', {}).get('url', 'Unknown'),
                'session_running': client.is_running
            })
    except Exception as e:
        return jsonify({
            'connected': False,
            'error': str(e),
            'session_running': False
        })

@socketio.on('start_session')
def handle_start_session():
    """세션 시작 요청"""
    try:
        client = get_web_client()
        with client_lock:
            if client.is_running:
                emit('error', {'message': '이미 세션이 실행 중입니다'})
                return
            
            success = client.start_session()
            if not success:
                emit('error', {'message': '세션 시작에 실패했습니다'})
    except Exception as e:
        print(f"❌ 세션 시작 처리 오류: {e}")
        emit('error', {'message': f'세션 시작 처리 오류: {str(e)}'})

@socketio.on('stop_session')
def handle_stop_session():
    """세션 중지 요청"""
    try:
        client = get_web_client()
        with client_lock:
            client.stop_session()
    except Exception as e:
        print(f"❌ 세션 중지 처리 오류: {e}")
        emit('error', {'message': f'세션 중지 처리 오류: {str(e)}'})

@socketio.on('connect')
def handle_connect():
    """클라이언트 연결"""
    try:
        print("🌐 웹소켓 클라이언트 연결됨")
        
        client = get_web_client()
        
        # 연결 상태 전송
        emit('status', {
            'message': '웹 클라이언트에 연결되었습니다', 
            'running': client.is_running,
            'connected': True
        })
        
        # 서버 정보 전송
        server_url = client.config_data.get('server', {}).get('url', 'Unknown')
        emit('server_info', {
            'server_url': server_url,
            'connected': False,  # 아직 서버 연결 확인 안됨
            'session_running': client.is_running
        })
        
        print("✅ 웹소켓 연결 완료")
        
    except Exception as e:
        print(f"❌ 웹소켓 연결 처리 오류: {e}")
        emit('error', {'message': f'연결 처리 오류: {str(e)}'})

@socketio.on('disconnect')
def handle_disconnect():
    """클라이언트 연결 해제"""
    print("🌐 웹소켓 클라이언트 연결 해제됨")
    
    # 실행 중인 세션이 있으면 중지
    try:
        client = get_web_client()
        if client.is_running:
            with client_lock:
                client.stop_session()
    except Exception as e:
        print(f"❌ 연결 해제 시 세션 중지 오류: {e}")

@socketio.on('test_tts')
def handle_test_tts():
    """TTS 테스트"""
    try:
        print("🧪 TTS 테스트 요청 받음")
        
        # 테스트용 더미 오디오 정보 전송
        test_audio = {
            'path': 'test_audio.wav',
            'filename': 'test_audio.wav',
            'type': 'tts',
            'url': '/test-audio',
            'timestamp': time.time(),
            'size': 1024,
            'test': True
        }
        
        print(f"🧪 테스트 오디오 정보 전송: {test_audio}")
        emit('audio', test_audio)
        emit('info', {'message': 'TTS 테스트 신호 전송됨'})
        
    except Exception as e:
        print(f"❌ TTS 테스트 실패: {e}")
        emit('error', {'message': f'TTS 테스트 실패: {str(e)}'})

@app.route('/test-audio')
def serve_test_audio():
    """테스트용 오디오 생성"""
    try:
        import numpy as np
        import wave
        import tempfile
        
        # 간단한 사인파 생성 (440Hz, 1초)
        sample_rate = 44100
        duration = 1.0
        frequency = 440.0
        
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        audio_data = np.sin(2 * np.pi * frequency * t) * 0.3
        audio_data = (audio_data * 32767).astype(np.int16)
        
        # 임시 WAV 파일 생성
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        with wave.open(temp_file.name, 'w') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data.tobytes())
        
        return send_from_directory(os.path.dirname(temp_file.name), 
                                 os.path.basename(temp_file.name))
    except Exception as e:
        return jsonify({'error': f'테스트 오디오 생성 실패: {str(e)}'}), 500

if __name__ == '__main__':
    try:
        print("🌐 웹 기반 실시간 음성 클라이언트 시작")
        print("=" * 50)
        
        # 웹 클라이언트 초기화
        client = get_web_client()
        
        # 설정 확인
        print(f"📁 설정 파일: {client.config_path}")
        print(f"🔗 서버 URL: {client.config_data.get('server', {}).get('url', 'Unknown')}")
        
        # 필요한 디렉토리 생성
        audio_dir = client.config_data.get('audio', {}).get('temp_dir', 'temp_audio')
        if not os.path.exists(audio_dir):
            os.makedirs(audio_dir, exist_ok=True)
            print(f"📁 오디오 디렉토리 생성: {audio_dir}")
        
        print("📱 브라우저에서 http://localhost:5000 접속")
        print("=" * 50)
        
        # 웹 서버 시작
        socketio.run(
            app, 
            host='0.0.0.0', 
            port=5000, 
            debug=True,  # 디버깅을 위해 True로 변경
            allow_unsafe_werkzeug=True,  # 개발용
            log_output=True
        )
        
    except KeyboardInterrupt:
        print("\n👋 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 웹 서버 시작 실패: {e}")
        import traceback
        traceback.print_exc()