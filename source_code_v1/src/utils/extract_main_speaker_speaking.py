#일단 diarization 을 한다. diarization 을 해서 1명이면 주화자만 잘들리는걸수도 있지만
#진짜 화자가 1명일수가 있다. 이때 sepformer에 넣으면 한 음성파일을 그냥 2개로 나눠버릴수가있다

#그래서 diarization 을 해서 화자가 0,1명이 나오면 할게 없다.
#그냥 아무것도 안하고 저장되면 sample.wav, 화자분리 되고 저장되면 e_sample.wav

import torchaudio
try:
    from speechbrain.inference import SepformerSeparation as separator
    from speechbrain.inference import SpeakerRecognition
except ImportError:
    # 이전 버전 호환성
    from speechbrain.pretrained import SepformerSeparation as separator
    from speechbrain.pretrained import SpeakerRecognition
import os
import torch
import sys
from pyannote.audio import Pipeline
from collections import defaultdict

def rms_safe_normalize(waveform, max_target_rms=0.05):
    rms = (waveform ** 2).mean().sqrt()
    peak = waveform.abs().max()

    if rms == 0 or peak == 0:
        raise Exception('오디오파일이 비어있습니다')

    safe_target_rms = min(rms * (1.0 / peak), max_target_rms)
    scaled = waveform * (safe_target_rms / rms)
    return scaled.float()   #float32




def extract_main_speaker(audiodir, savedir='sample.wav', huggingface_token=None):
    """
    음성 파일에서 주요 화자의 음성을 추출하는 함수
    
    Args:
        audiodir (str): 입력 오디오 파일 경로
        savedir (str): 출력 파일 경로 (기본값: 'sample.wav')
        huggingface_token (str): HuggingFace 토큰 (None이면 기본값 사용)
    
    Returns:
        str: 저장된 파일 경로
    """
    
    # 토큰 설정
    if huggingface_token is None:
        huggingface_token = HUGGINGFACE_TOKEN
        
    diarization_speaker_num_is_0or1 = False

    #########diarization

    #음성파일 로드
    waveform_original, sr = torchaudio.load(audiodir)  #waveform_original 은 (1,time) 꼴일거다

    #pyannote diarization 파이프라인       
    pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization@2.1", use_auth_token=huggingface_token)
    pipeline.to(torch.device("cuda"))

    if sr != 16000:     #pyannote 는 16000hz sr 을 써야한다. 그리고 path 입력만 받음
        raise Exception('샘플링레이트가 16000이 아닙니다. Ecapa, pyannote 는 16000 샘플링레이트를 기대합니다')

    #diarization 수행
    diarization = pipeline(audiodir)

    speaker_num=0
    total_energy = defaultdict(float)
    speaker_names=[]

    for segment, _, speaker in diarization.itertracks(yield_label=True):
        #print(f"{speaker}: {segment.start:.2f} → {segment.end:.2f}")
        speaker_names.append(speaker)
        speaker_names=list(set(speaker_names))
        
        start_sample = int(segment.start * sr)
        end_sample = int(segment.end * sr)
        segment_waveform = waveform_original[:, start_sample:end_sample]
        
        energy = torch.norm(segment_waveform)  # L2 norm = 에너지
        total_energy[speaker] += energy.item()
      
    #화자 수가 0명 또는 1명인가
    if not total_energy:   #diarization 에 실패한 경우이다. 즉 이 경우에는 .txt 가 생성되지 않을거다
        print('❌ Diarization 에 실패하였습니다. 화자 수 및 발화구간을 찾을 수 없습니다.')
        speakernum=0
        diarization_speaker_num_is_0or1=True
    elif len(speaker_names) in [0,1]:   #근데 speaker 가 0명이면 diarization 이 안된거 아닌가. 그럼 위 경우에 포함되는건가
        speakernum=len(speaker_names)
        diarization_speaker_num_is_0or1=True

    #################화자 수가 0명 또는 1명이라면 할것이 없다.    
    if diarization_speaker_num_is_0or1==True: 
        torchaudio.save(savedir, waveform_original, sr)
        print('✅ 화자 수가 0명 또는 1명이여서 원본음성파일을 단순 저장합니다.')
        return savedir
            
    #주 화자 찾기(way1 enhanced 방식 말고 그냥 way1 방식)
    main_speaker = max(total_energy, key=total_energy.get)

    #주 화자가 말한 구간들 추출해서 하나로 잇기 (즉 다른 화자의 목소리도 섞여있긴 한거다)
    segments = []    #16000hz
    for segment, _, speaker in diarization.itertracks(yield_label=True):
        if speaker != main_speaker:
            continue
        s, e = int(segment.start * sr), int(segment.end * sr)
        segments.append(waveform_original[:, s:e])
        
    main_speaker_waveform = torch.cat(segments, dim=1).to('cuda')  # (1, total_samples). 

    #ecapa
    recognizer = SpeakerRecognition.from_hparams(source="speechbrain/spkrec-ecapa-voxceleb",run_opts={"device": "cuda"})

    #주 화자가 말한 구간 음성특징 임베딩 (ecapa 도 샘플링레이트 16000hz 를 기대한다)
    main_speaker_embedding = recognizer.encode_batch(main_speaker_waveform).squeeze()    # (192,)
    #print("✅ 주화자 임베딩 벡터 shape:", main_speaker_embedding.shape)

    ###############separation

    #음성분리 모델 로드
    model = separator.from_hparams(
        source="speechbrain/sepformer-wsj02mix",
        run_opts={"device": "cuda"},    #sepformer 는 이런식으로 cuda 로 옮겨야한다. .to('cuda') 로 옮기면 에러난다. 아래에 서브모듈들이 gpu 로 안가서 그럼
    )
    model.eval()

    #필요시 리샘플링
    if sr != 8000:     #sepformer 는 8000hz sr 을 써야한다
        resampler = torchaudio.transforms.Resample(orig_freq=sr, new_freq=8000)
        waveform_8000 = resampler(waveform_original)       #waveform_8000 도 (1,time) 꼴
    else:
        waveform_8000=waveform_original    #이렇게해도 어차피 waveform_8000은 수정하지 않으므로 괜찮을듯
        
    if waveform_8000.shape[0] > 1:
        raise Exception('모노채널 오디오파일인지 확인하세요')

    #음성분리 수행    
    waveform_8000 = waveform_8000.to('cuda')
    estimated_sources = model(waveform_8000)    #(batch, time, num_speakers). 이때 batch 는 1일거다. 왜냐면 오디오 파일을 한개만 넣어서

    if estimated_sources.shape[0]!=1:
        raise Exception('입력 오디오파일이 한개인지 확인하세요')
        
    estimated_sources = estimated_sources.squeeze(0)       # (time, num_speakers)
    num_speakers = estimated_sources.shape[1]    #기본적으로 2명이 나오긴 하는데 아닐때도 가끔 있다고는 한다?

    #separation 된 음성파일들
    sepformer_waveforms=[]    #8000hz

    for i in range(num_speakers):
        waveform = estimated_sources[:, i].unsqueeze(0)   # (time,nums_peakers)->(time,)->(1, time) (mono wav)
        waveform = rms_safe_normalize(waveform, max_target_rms=0.05)
        sepformer_waveforms.append(waveform)
        
        #os.makedirs(f"{savedir}{f.replace('.wav','')}", exist_ok=True)
        #filename=f"{savedir}{f.replace('.wav','')}/speaker{i}.wav"
        #torchaudio.save(filename, waveform.cpu(), 8000)   #sepformer 는 샘플링레이트가 8000이다
        #print(f"✅ Saved: {filename} (shape: {waveform.shape})")

    ###############diarization 결과와 코사인유사도로 비교
    #sepformer_waveforms 는 8000hz 에서 만들어졌으므로 리샘플링 해줘야함
    resampler = torchaudio.transforms.Resample(orig_freq=8000, new_freq=16000).to("cuda")   #텐서 하나만 보고서는 이게 몇 샘플링레이트에서 만들어졌는지는 알수없다. 그니까 잘 기억해두자.  
    sepformer_embeddings=[]
    for w in sepformer_waveforms:
        resampled=resampler(w)
        embedding = recognizer.encode_batch(resampled).squeeze()
        sepformer_embeddings.append(embedding)
        
    #코사인 유사도 계산
    similarities=[]
    for e in sepformer_embeddings:
        similarity=torch.nn.functional.cosine_similarity(main_speaker_embedding, e, dim=0).item()
        similarities.append(similarity)
        
    #라벨 예측 (제일 코사인유사도 높은거 선택)
    predict=similarities.index(max(similarities))

    #16000 샘플레이트로 저장하자. 위에 있던 샘플러써서
    result=resampler(sepformer_waveforms[predict])
    output_path = 'e_' + savedir
    torchaudio.save(output_path, result.cpu(), 16000)
    print('✅ 주 화자의 대화소리를 추출하여 저장합니다.')
    
    return output_path


def main():
    """메인 실행 함수 - 기본 설정으로 실행"""
    audiodir = 'mixed_audio/2person_enhancedmix/wav/S00000332_0.84_S00190179_0.16_mixed_2.3.wav'
    savedir = 'sample.wav'
    
    try:
        result_path = extract_main_speaker(audiodir, savedir)
        print(f"✅ 처리 완료: {result_path}")
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return False
    return True


if __name__ == "__main__":
    main()
