#!/usr/bin/env python3
"""
웹 기반 실시간 음성 클라이언트 - 간단 버전
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
socketio = SocketIO(app, cors_allowed_origins="*")

class WebRealTimeClient:
    """웹 인터페이스용 실시간 클라이언트 래퍼"""
    
    def __init__(self, config_path="config.json"):
        self.config_path = config_path
        self.client = None
        self.is_running = False
        self.tts_file_cache = {}  # TTS 파일 경로 캐시
        self.load_config()
    
    def load_config(self):
        """설정 파일 로드"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config_data = json.load(f)
        except Exception as e:
            self.config_data = {
                "server": {"url": "http://localhost:8001"},
                "audio": {"temp_dir": "temp_audio"}
            }
    
    def initialize_client(self):
        """클라이언트 초기화"""
        try:
            from examples.complete_realtime_client import CompleteRealTimeClient
            self.client = CompleteRealTimeClient(self.config_path)
            return True
        except Exception as e:
            socketio.emit('error', {'message': f'클라이언트 초기화 실패: {str(e)}'})
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
            
            # 웹용 콜백 설정
            self.setup_web_callbacks()
            
            # 세션 시작
            self.is_running = True
            socketio.emit('status', {'message': '실시간 음성 세션이 시작되었습니다', 'running': True})
            
            # 별도 스레드에서 실행
            threading.Thread(target=self._run_session, daemon=True).start()
            return True
            
        except Exception as e:
            socketio.emit('error', {'message': f'세션 시작 실패: {str(e)}'})
            return False
    
    def setup_web_callbacks(self):
        """웹용 콜백 설정"""
        try:
            # 마이크 매니저의 콜백 설정
            if hasattr(self.client, 'mic_manager') and hasattr(self.client.mic_manager, 'set_callbacks'):
                def on_audio_ready(audio_file_path):
                    socketio.emit('info', {'message': f'🎵 음성 파일 생성: {os.path.basename(audio_file_path)}'})
                
                def on_response_received(response):
                    try:
                        print(f"📨 서버 응답 수신: {type(response)}")
                        print(f"📨 응답 객체 속성: {dir(response)}")
                        
                        if hasattr(response, 'success') and response.success:
                            # 응답 데이터 구성
                            response_data = {}
                            
                            # 응답 텍스트
                            if hasattr(response, 'message'):
                                response_data['text'] = response.message
                                print(f"💬 응답 텍스트: {response.message}")
                            
                            # 모든 속성 확인 (디버깅용)
                            print("🔍 응답 객체의 모든 속성:")
                            for attr in dir(response):
                                if not attr.startswith('_'):
                                    try:
                                        value = getattr(response, attr)
                                        if not callable(value):
                                            print(f"   {attr}: {value}")
                                    except:
                                        pass
                            
                            # 주문 정보 처리 - 다양한 필드명 확인
                            order_data = None
                            order_fields = ['order_data', 'order', 'order_info', 'cart', 'items']
                            
                            # 먼저 order_data 필드가 명시적으로 None인지 확인
                            has_order_field = False
                            for field in order_fields:
                                if hasattr(response, field):
                                    has_order_field = True
                                    field_value = getattr(response, field)
                                    if field_value:
                                        print(f"🛒 주문 필드 발견: {field} = {field_value}")
                                        order_data = field_value
                                        break
                                    elif field == 'order_data':
                                        # order_data가 명시적으로 None인 경우 (결제 완료 후 등)
                                        print(f"🛒 주문 필드 {field}가 None으로 설정됨 - 주문 정보 초기화")
                                        break
                            
                            if order_data:
                                order_info = self.extract_order_info(order_data)
                                if order_info:
                                    response_data['order_data'] = order_info
                                    print(f"🛒 추출된 주문 정보: {order_info}")
                                    
                                    # 별도로 주문 업데이트 이벤트도 전송
                                    socketio.emit('order_update', order_info)
                                else:
                                    print("❌ 주문 정보 추출 실패")
                                    response_data['order_data'] = None
                                    socketio.emit('order_update', None)
                            elif has_order_field:
                                # 주문 필드가 있지만 None이거나 빈 경우 - 명시적으로 null 전송
                                print("🛒 주문 데이터가 비어있음 - 주문 정보 창 숨김")
                                response_data['order_data'] = None
                                socketio.emit('order_update', None)
                            else:
                                print("⚠️ 주문 데이터를 찾을 수 없음")
                            
                            # UI 액션 처리
                            if hasattr(response, 'ui_actions') and response.ui_actions:
                                print(f"🎯 UI 액션 발견: {len(response.ui_actions)}개")
                                ui_actions_data = []
                                for action in response.ui_actions:
                                    if hasattr(action, 'to_dict'):
                                        action_dict = action.to_dict()
                                    else:
                                        # UIAction 객체가 아닌 경우 딕셔너리로 변환
                                        action_dict = {
                                            'action_type': action.action_type,
                                            'data': action.data,
                                            'priority': getattr(action, 'priority', 0),
                                            'requires_user_input': getattr(action, 'requires_user_input', False),
                                            'timeout_seconds': getattr(action, 'timeout_seconds', None)
                                        }
                                    ui_actions_data.append(action_dict)
                                    print(f"   - {action.action_type}: {action.data}")
                                
                                response_data['ui_actions'] = ui_actions_data
                                # UI 액션별 개별 이벤트도 전송
                                socketio.emit('ui_actions', ui_actions_data)
                            
                            # 응답 전송
                            socketio.emit('response', response_data)
                            
                            # TTS URL 처리
                            if hasattr(response, 'tts_audio_url') and response.tts_audio_url:
                                print(f"🔊 TTS URL 발견: {response.tts_audio_url}")
                                self.handle_tts_url(response.tts_audio_url)
                        else:
                            # 오류 응답
                            error_msg = response.error_info.error_message if hasattr(response, 'error_info') and response.error_info else '알 수 없는 오류'
                            socketio.emit('error', {'message': f'서버 오류: {error_msg}'})
                            
                    except Exception as e:
                        print(f"❌ 응답 처리 오류: {e}")
                        import traceback
                        traceback.print_exc()
                        socketio.emit('error', {'message': f'응답 처리 오류: {str(e)}'})
                
                # 콜백 설정
                self.client.mic_manager.set_callbacks(
                    on_audio_ready=on_audio_ready,
                    on_response_received=on_response_received
                )
                print("✅ 마이크 매니저 콜백 설정 완료")
            
            # 원본 _play_tts_response 메서드를 웹용으로 교체
            if hasattr(self.client, '_play_tts_response'):
                def web_play_tts_response(tts_url):
                    self.handle_tts_url(tts_url)
                
                # 메서드 교체
                self.client._play_tts_response = web_play_tts_response
                print("✅ TTS 콜백 설정 완료")
            else:
                print("⚠️ _play_tts_response 메서드를 찾을 수 없습니다")
                
        except Exception as e:
            print(f"❌ 웹 콜백 설정 오류: {e}")
            socketio.emit('error', {'message': f'콜백 설정 오류: {str(e)}'})
    
    def handle_tts_url(self, tts_url):
        """TTS URL 처리"""
        try:
            print(f"🔊 TTS URL 처리: {tts_url}")
            
            # TTS 파일 다운로드
            if hasattr(self.client.voice_client, 'download_tts_file'):
                tts_file_path = self.client.voice_client.download_tts_file(tts_url)
                if tts_file_path and os.path.exists(tts_file_path):
                    print(f"🔊 TTS 파일 다운로드 완료: {tts_file_path}")
                    
                    filename = os.path.basename(tts_file_path)
                    
                    # TTS 파일 경로를 캐시에 저장
                    self.tts_file_cache[filename] = tts_file_path
                    print(f"🔊 TTS 파일 캐시에 저장: {filename} -> {tts_file_path}")
                    
                    # 로컬 temp_audio 디렉토리로 파일 복사 (백업용)
                    try:
                        local_audio_dir = self.config_data.get('audio', {}).get('temp_dir', 'temp_audio')
                        if not os.path.exists(local_audio_dir):
                            os.makedirs(local_audio_dir, exist_ok=True)
                        
                        local_file_path = os.path.join(local_audio_dir, filename)
                        
                        # 파일 복사
                        import shutil
                        shutil.copy2(tts_file_path, local_file_path)
                        print(f"🔊 TTS 파일 복사 완료: {local_file_path}")
                    except Exception as copy_error:
                        print(f"⚠️ TTS 파일 복사 실패 (원본 파일 사용): {copy_error}")
                    
                    # 웹으로 오디오 정보 전송
                    audio_info = {
                        'path': tts_file_path,
                        'filename': filename,
                        'type': 'tts',
                        'url': f'/audio/{filename}',
                        'timestamp': time.time(),
                        'original_url': tts_url
                    }
                    
                    print(f"🔊 웹으로 TTS 오디오 전송: {audio_info}")
                    socketio.emit('audio', audio_info)
                else:
                    print(f"❌ TTS 파일 다운로드 실패: {tts_url}")
                    socketio.emit('error', {'message': f'TTS 파일 다운로드 실패: {tts_url}'})
            else:
                print("❌ TTS 다운로드 기능을 사용할 수 없습니다")
                socketio.emit('error', {'message': 'TTS 다운로드 기능을 사용할 수 없습니다'})
        except Exception as e:
            print(f"❌ TTS URL 처리 오류: {e}")
            socketio.emit('error', {'message': f'TTS URL 처리 오류: {str(e)}'})
    
    def extract_order_info(self, order_data):
        """주문 정보 추출"""
        try:
            print(f"🔍 주문 데이터 분석 시작")
            print(f"🔍 데이터 타입: {type(order_data)}")
            print(f"🔍 데이터 내용: {order_data}")
            
            # OrderData 객체인 경우 (실제 서버 응답)
            if hasattr(order_data, 'items') and hasattr(order_data, 'total_amount'):
                print("📦 OrderData 객체 감지됨")
                
                items = []
                for item in order_data.items:
                    print(f"🍔 아이템 처리 중: {item}")
                    
                    # 옵션 정보 처리
                    options_text = ""
                    if isinstance(item, dict):
                        if 'options' in item and item['options']:
                            options_list = []
                            for key, value in item['options'].items():
                                options_list.append(f"{key}: {value}")
                            if options_list:
                                options_text = f" ({', '.join(options_list)})"
                        
                        item_info = {
                            'name': item.get('name', '알 수 없는 메뉴') + options_text,
                            'quantity': item.get('quantity', 1),
                            'price': item.get('total_price', item.get('price', 0)),
                            'category': item.get('category', ''),
                            'item_id': item.get('item_id', '')
                        }
                    else:
                        # 객체 속성으로 접근
                        if hasattr(item, 'options') and item.options:
                            options_list = []
                            for key, value in item.options.items():
                                options_list.append(f"{key}: {value}")
                            if options_list:
                                options_text = f" ({', '.join(options_list)})"
                        
                        item_info = {
                            'name': getattr(item, 'name', '알 수 없는 메뉴') + options_text,
                            'quantity': getattr(item, 'quantity', 1),
                            'price': getattr(item, 'total_price', getattr(item, 'price', 0)),
                            'category': getattr(item, 'category', ''),
                            'item_id': getattr(item, 'item_id', '')
                        }
                    
                    items.append(item_info)
                    print(f"✅ 아이템 추가: {item_info}")
                
                # OrderData 객체에서 정보 추출
                order_info = {
                    'items': items,
                    'total': getattr(order_data, 'total_amount', 0),
                    'status': getattr(order_data, 'status', 'pending'),
                    'order_id': getattr(order_data, 'order_id', ''),
                    'item_count': getattr(order_data, 'item_count', len(items)),
                    'requires_confirmation': getattr(order_data, 'requires_confirmation', False),
                    'created_at': getattr(order_data, 'created_at', ''),
                    'updated_at': getattr(order_data, 'updated_at', ''),
                    'timestamp': time.time()
                }
                
                print(f"✅ 주문 정보 추출 완료: {len(items)}개 아이템, 총 {order_info['total']}원")
                return order_info
            
            # 딕셔너리 형태의 주문 데이터 처리 (기존 로직)
            elif isinstance(order_data, dict):
                print("📋 딕셔너리 데이터 처리 중...")
                items = []
                total = 0
                
                # items 필드가 있는 경우
                if 'items' in order_data:
                    for item in order_data['items']:
                        if isinstance(item, dict):
                            # 옵션 처리
                            options_text = ""
                            if 'options' in item and item['options']:
                                options_list = []
                                for key, value in item['options'].items():
                                    options_list.append(f"{key}: {value}")
                                if options_list:
                                    options_text = f" ({', '.join(options_list)})"
                            
                            item_info = {
                                'name': item.get('name', '알 수 없는 메뉴') + options_text,
                                'quantity': item.get('quantity', 1),
                                'price': item.get('total_price', item.get('price', 0)),
                                'category': item.get('category', ''),
                                'item_id': item.get('item_id', '')
                            }
                            items.append(item_info)
                            total += item_info['price']
                
                if items:
                    return {
                        'items': items,
                        'total': order_data.get('total_amount', total),
                        'status': order_data.get('status', 'pending'),
                        'order_id': order_data.get('order_id', ''),
                        'item_count': order_data.get('item_count', len(items)),
                        'timestamp': time.time()
                    }
            
            # 문자열인 경우 (기존 로직)
            elif isinstance(order_data, str):
                print("📝 문자열 데이터 처리 중...")
                try:
                    import json
                    parsed_data = json.loads(order_data)
                    return self.extract_order_info(parsed_data)
                except:
                    return {
                        'items': [{'name': order_data, 'quantity': 1, 'price': 0}],
                        'total': 0,
                        'status': 'processing',
                        'timestamp': time.time()
                    }
            
            print("⚠️ 지원되지 않는 주문 데이터 형식")
            return None
            
        except Exception as e:
            print(f"❌ 주문 정보 추출 오류: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _run_session(self):
        """세션 실행 (별도 스레드)"""
        try:
            if hasattr(self.client, 'run_interactive_session'):
                self.client.run_interactive_session()
        except Exception as e:
            socketio.emit('error', {'message': f'세션 실행 중 오류: {str(e)}'})
        finally:
            self.is_running = False
            socketio.emit('status', {'message': '세션이 종료되었습니다', 'running': False})
    
    def stop_session(self):
        """세션 중지"""
        self.is_running = False
        if self.client and hasattr(self.client, 'stop'):
            self.client.stop()
        socketio.emit('status', {'message': '세션이 중지되었습니다', 'running': False})

# 전역 클라이언트 초기화
web_client = WebRealTimeClient()

@app.route('/')
def index():
    """메인 페이지"""
    return render_template('index_simple.html')

@app.route('/favicon.ico')
def favicon():
    return '', 204

@app.route('/config')
def get_config():
    """현재 설정 반환"""
    return jsonify(web_client.config_data)

@app.route('/config', methods=['POST'])
def update_config():
    """설정 업데이트"""
    try:
        new_config = request.json
        web_client.config_data.update(new_config)
        
        # 설정 파일 저장
        with open(web_client.config_path, 'w', encoding='utf-8') as f:
            json.dump(web_client.config_data, f, indent=2, ensure_ascii=False)
        
        return jsonify({'success': True, 'message': '설정이 업데이트되었습니다'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'설정 업데이트 실패: {str(e)}'})

@app.route('/audio/<filename>')
def serve_audio(filename):
    """오디오 파일 서빙"""
    try:
        # 여러 경로에서 오디오 파일 찾기
        possible_dirs = [
            web_client.config_data.get('audio', {}).get('temp_dir', 'temp_audio'),
            'temp_audio',
            'audio',
            '.',  # 현재 디렉토리
            # Windows 임시 디렉토리도 확인
            os.path.join(os.environ.get('TEMP', ''), 'voice_client_audio'),
            os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Temp', 'voice_client_audio'),
        ]
        
        print(f"🔍 오디오 파일 검색: {filename}")
        
        # 먼저 캐시에서 확인
        if filename in web_client.tts_file_cache:
            cached_path = web_client.tts_file_cache[filename]
            if os.path.exists(cached_path):
                print(f"🔊 캐시에서 오디오 파일 발견: {cached_path}")
                response = send_from_directory(os.path.dirname(cached_path), filename)
                # CORS 헤더 추가
                response.headers['Access-Control-Allow-Origin'] = '*'
                response.headers['Cache-Control'] = 'no-cache'
                response.headers['Content-Type'] = 'audio/wav'
                return response
            else:
                print(f"⚠️ 캐시된 파일이 존재하지 않음: {cached_path}")
                del web_client.tts_file_cache[filename]
        
        # 캐시에 없으면 일반 디렉토리에서 검색
        for audio_dir in possible_dirs:
            if not audio_dir or not os.path.exists(audio_dir):
                continue
                
            file_path = os.path.join(audio_dir, filename)
            print(f"   검색 중: {file_path}")
            
            if os.path.exists(file_path):
                print(f"🔊 오디오 파일 발견: {file_path}")
                response = send_from_directory(audio_dir, filename)
                # CORS 헤더 추가
                response.headers['Access-Control-Allow-Origin'] = '*'
                response.headers['Cache-Control'] = 'no-cache'
                response.headers['Content-Type'] = 'audio/wav'
                return response
        
        # 파일을 찾지 못한 경우
        print(f"❌ 오디오 파일을 찾을 수 없음: {filename}")
        print(f"검색한 디렉토리: {[d for d in possible_dirs if d and os.path.exists(d)]}")
        return jsonify({'error': f'오디오 파일을 찾을 수 없습니다: {filename}'}), 404
        
    except Exception as e:
        print(f"❌ 오디오 서빙 오류: {e}")
        return jsonify({'error': f'오디오 파일 서빙 오류: {str(e)}'}), 500

@socketio.on('start_session')
def handle_start_session():
    """세션 시작 요청"""
    if web_client.is_running:
        emit('error', {'message': '이미 세션이 실행 중입니다'})
        return
    
    success = web_client.start_session()
    if not success:
        emit('error', {'message': '세션 시작에 실패했습니다'})

@socketio.on('stop_session')
def handle_stop_session():
    """세션 중지 요청"""
    web_client.stop_session()

@socketio.on('connect')
def handle_connect():
    """클라이언트 연결"""
    emit('status', {'message': '웹 클라이언트에 연결되었습니다', 'running': web_client.is_running})

@socketio.on('test_tts')
def handle_test_tts():
    """TTS 테스트"""
    try:
        test_audio = {
            'path': 'test_audio.wav',
            'filename': 'test_audio.wav',
            'type': 'tts',
            'url': '/test-audio',
            'timestamp': time.time(),
            'test': True
        }
        emit('audio', test_audio)
    except Exception as e:
        emit('error', {'message': f'TTS 테스트 실패: {str(e)}'})

@socketio.on('clear_order')
def handle_clear_order():
    """주문 정보 초기화"""
    try:
        emit('order_update', {'items': [], 'total': 0, 'status': 'cleared'})
        emit('info', {'message': '주문 정보가 초기화되었습니다'})
    except Exception as e:
        emit('error', {'message': f'주문 초기화 실패: {str(e)}'})

@socketio.on('test_order')
def handle_test_order():
    """주문 정보 테스트"""
    try:
        test_order = {
            'items': [
                {'name': '아메리카노', 'quantity': 2, 'price': 4000},
                {'name': '카페라떼', 'quantity': 1, 'price': 4500},
                {'name': '크로와상', 'quantity': 1, 'price': 3000}
            ],
            'total': 11500,
            'status': 'processing',
            'timestamp': time.time()
        }
        emit('order_update', test_order)
        emit('info', {'message': '테스트 주문 정보가 표시되었습니다'})
    except Exception as e:
        emit('error', {'message': f'주문 테스트 실패: {str(e)}'})

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
    print("🌐 웹 기반 실시간 음성 클라이언트 시작 (간단 버전)")
    print("📱 브라우저에서 http://localhost:5000 접속")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)