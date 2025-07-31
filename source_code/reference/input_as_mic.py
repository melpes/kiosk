import sys
import torch
import numpy as np
import sounddevice as sd
from scipy.io.wavfile import write
from collections import deque
import urllib.error 

#HOW_LONG_RECORD=10   #음성파일 길이가 너무 길면 STT 가 안되지 않을까?



#변수들
sample_rate = 16000
frame_duration = 0.5    #(초) 한 번에 읽을 오디오 길이. 이경우에는 한 프레임 길이는 sample_rate 16000 * frame_duration 0.5 곱해서 8000이다.
max_silence_duration_start = 5.0     #(초) 무음이 이 시간 이상 지속되면 종료
max_silence_duration_end = 3.0
min_record = 1.0     #(초) 최소 녹음 시간
vad_threshold=0.2    #vad 민감도. 내 마이크는 0.2는 되야 잘 인식하는듯?
file_name='record.wav'

print('안녕하세요 맥도날드 입니다. 주문을 시작하려면 a 키, 종료하려면 x 키를 입력해주세요')

while True:
    enter=input('입력 : ')
    if enter=='a':
        break
    elif enter=='x':
        print('이용해주셔서 감사합니다.')
        sys.exit()
    else:
        print('잘못된 입력입니다')
        
##################VAD 로 음성입력이 감지되는지 판단

# 모델 불러오기
while True:
    try:
        model, utils = torch.hub.load(repo_or_dir='snakers4/silero-vad', model='silero_vad', force_reload=False)   #True 로 하면 코드 실행시킬때마다 모델 다시다운로드한다.
    except urllib.error.HTTPError as e:     #github 가 응답 안할때가 꽤 있다.
        continue
    break
(get_speech_timestamps, _, _, _, _) = utils
print('주문을 말씀해주세요. 말씀을 시작하시면 자동으로 녹음됩니다')

# 녹음 데이터 저장용
recorded_frames = []
silence_buffer_start = deque(maxlen=int(max_silence_duration_start / frame_duration))    #max_silence_duration 이 3초 이고 frame_duration 이 0.5초 라면 3/0.5=6프레임 이상(초과?)이면 녹음종료.  
silence_buffer_end = deque(maxlen=int(max_silence_duration_end / frame_duration))

stream = sd.InputStream(samplerate=sample_rate, channels=1, dtype='float32', blocksize=int(sample_rate * frame_duration))
stream.start()

try:
    while True:
        audio_block, _ = stream.read(int(sample_rate * frame_duration))
        audio_np = audio_block.squeeze()
        audio_tensor = torch.from_numpy(audio_np)

        # 음성 감지. get_speech_timestamps() 는 텐서에서 음성이 있는 구간을 찾아준다
        speech = get_speech_timestamps(audio_tensor, model, sampling_rate=sample_rate, threshold=vad_threshold)

        if speech:
            #print("🗣️ 음성 감지됨")
            if len(silence_buffer_end)!=0:
                recorded_frames+=list(silence_buffer_end)
                silence_buffer_end.clear()
            recorded_frames.append(audio_np)
        else:
            #print("🔇 무음")
            if recorded_frames:
                silence_buffer_end.append(audio_np)
            else:
                silence_buffer_start.append(audio_np)

        # 무음이 오래 지속되면 종료
        if recorded_frames:
            if len(silence_buffer_end)==silence_buffer_end.maxlen:
                print("무음이 지속되어 녹음을 종료합니다.")
                break
        else:
            if len(silence_buffer_start) == silence_buffer_start.maxlen:
                print('입력시간이 초과되었습니다.')
                sys.exit()
                break
finally:
    stream.stop()
    stream.close()
    
#저장
if len(recorded_frames) >= min_record:
    all_audio = np.concatenate(recorded_frames)
    write(f"{file_name}", sample_rate, (all_audio * 32767).astype(np.int16))
    print(f"{file_name} 파일로 저장되었습니다.")
else:
    print('음성이 너무 짧습니다.')






