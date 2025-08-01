from openai import OpenAI
import sys

MY_API_KEY='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'
client = OpenAI(api_key=MY_API_KEY)
MODEL='gpt-4o'
DOMAIN='맥도날드에서 주문시 할법한 대화'
INTENT=['주문','변경','취소']
MENU=['햄버거','더블치즈버거','트리플치즈버거','치즈버거','베이컨 토마토 디럭스',
      '슈비버거','슈슈버거','불고기버거','더블불고기버거','맥치킨','맥치킨 모짜렐라',
      '1955버거','맥크리스피 클래식 버거','맥크리스피 디럭스 버거','빅맥','토마토 치즈 비프 버거',
      '쿼터파운더 치즈','맥스파이시 상하이 버거','더블 쿼터파운더 치즈','더블 맥스파이시 상하이 버거',
      '햄버거 세트','더블치즈버거 세트','트리플치즈버거 세트','치즈버거 세트',
      '베이컨 토마토 디럭스 세트','슈비버거 세트','슈슈버거 세트','불고기버거 세트',
      '더블불고기버거 세트','맥치킨 세트','맥치킨 모짜렐라 세트','1955버거 세트',
      '맥크리스피 클래식 버거 세트','맥크리스피 디럭스 버거 세트','빅맥 세트',
      '토마토 치즈 비프 버거 세트','쿼터파운더 치즈 세트','맥스파이시 상하이 버거 세트',
      '더블 쿼터파운더 치즈 세트','더블 맥스파이시 상하이 버거 세트',
      '햄버거 라지세트','더블치즈버거 라지세트','트리플치즈버거 라지세트','치즈버거 라지세트',
      '베이컨 토마토 디럭스 라지세트','슈비버거 라지세트','슈슈버거 라지세트','불고기버거 라지세트',
      '더블불고기버거 라지세트','맥치킨 라지세트','맥치킨 모짜렐라 라지세트','1955버거 라지세트',
      '맥크리스피 클래식 버거 라지세트','맥크리스피 디럭스 버거 라지세트','빅맥 라지세트',
      '토마토 치즈 비프 버거 라지세트','쿼터파운더 치즈 라지세트','맥스파이시 상하이 버거 라지세트',
      '더블 쿼터파운더 치즈 라지세트','더블 맥스파이시 상하이 버거 라지세트',]



def generate_data(message_to_send):
    completion = client.chat.completions.create(
        model=MODEL,  
        messages=message_to_send
    )
    result = completion.choices[0].message.content
    return result

def ask_to_gpt(system_msg, user_msg):
    messages = [
        {"role": "system", "content": system_msg},
        {"role": "user", "content": user_msg},
    ]
    return generate_data(messages)
            
        

########음성인식 파트

#입력된 음성을 텍스트로 전환
#pass

#텍스트를 표준어 텍스트로 전환
#pass



########자연어 대화 파트

#1. 입력이 도메인에 속하는가?
system_msg='''
너는 맥도날드에서 주문을 받는 AI 직원이야. 입력되는 텍스트가 맥도날드에서 주문시 할법한 대화인지 판단해줘.
반드시 답변은 다른 말은 하지말고 딱 '예', '아니오' 로 해줘. 

예를 들어서,
입력:자동차 휠이 까져서 도색을하려고 하는데요
답변: 아니오

입력: 순대국이랑 공기밥 하나 주문해줘
답변: 아니오

입력: 안녕하세요 맥도날드에 오랜만에 왔네
답변: 예

입력: 내가 차를 타고 가면서 햄버거를 먹다가 흘렸는데
답변: 아니오

입력: 한식이랑 불고기버거, 감자튀김, 맥플러리의 공통점을 알려줘
답변: 아니오

입력: 감자탕이랑 불고기버거 주문해주세요
답변: 아니오

입력: 불고기버거 세트 하나 줘. 콜라는 제로콜라로
답변: 예'''

user_msg=input('system: 안녕하세요 맥도날드입니다. 주문을 도와드리겠습니다\ncustomer: ')
response1=ask_to_gpt(system_msg, user_msg)
if '아니오' in response1:
    print('맥도날드에서 제공하는 서비스가 아닙니다.')
    sys.exit()

past_conversation='''<과거 대화내역>
gpt: 안녕하세요 맥도날드입니다. 주문을 도와드리겠습니다'''

present_conversation='''<현재 입력>
customer: '''

first_conversation=True
while True:
    #2. gpt와 대화
    #입력 자체에서 모든 요청을 각각 파악해서 query compression 을 할려고 했다.
    #ex)입력: 어우 너무 덥다 1955버거랑 맥너겟 하나 주세요. 아 1955버거는 불고기버거로 바꿔주세요.
    #ex)답변: 1955버거 단품 1개 주문, 맥너겟 1개 주문, 1955버거 단품 불고기버거 단품으로 변경
    
    #근데 이건 일일히 코드로 파악하는거보다 gpt가 그냥 대화하면서 파악하는게 더 정확할거같다.
    #따라서 대화 후 최종 결제 단계에서 gpt의 답변에서 요청을 파악하는 방식으로 해보자.
    
    system_msg='''
    너는 맥도날드에서 주문을 받는 AI 직원이야. 아래의 지시사항들을 따르면서 손님과 대화하면 되.
    0. 너가 평소에 하던대로 지금까지의 대화와 현재 입력된 대화 정보를 바탕으로 멀티턴 대화를 한다.
    1. 단, 손님에게 과하게 친절할필요나 공감은 필요없어. 사무적인 말투로 대화하면 되.
    2. 손님의 말중에 인사, 주문, 변경, 취소, 결제, 현재 주문리스트 문의, 항의 이 7가지 의도 외의 부분에는 '주문, 변경, 취소, 결제 외의 부분은 직원에게 문의해주세요' 라고 해.
    3. 손님의 말중에 항의 의도인 부분에는 '불편을 드려서 죄송합니다' 라고 하고 그냥 넘어가.
    4. 손님의 말중에 인사 의도인 부분에는 '안녕하세요 맥도날드를 이용해주셔서 감사합니다' 라고 해.
    5. 결제는 카드만 가능해. 손님이 결제수단을 궁금해하면 '키오스크에서는 카드결제만 가능합니다' 라고 안내해줘.
    6. 이모티콘은 출력하지 마. 나중에 TTS 할때 방해될수가있어
    
    예를 들어서
    손님: 불고기버거 세트 주세요. 아 근데 주문이 왤케 느려요 빨리좀 해주세요.
    답변: 불고기버거 세트 1개가 주문리스트에 추가되었습니다. 불편을 드려서 죄송합니다.
    
    손님: 지금 대량주문 되나요? 좀 많이 시키려고 하는데요
    답변: 주문, 변경, 취소, 결제 외의 부분은 직원에게 문의해주세요.
    
    손님: 에 그 애들 유치원에 햄버거를 좀 주문하려고 하는데요 불고기버거 그 뭐냐 50개만 줘봐요
    답변: 불고기버거 단품 50개가 주문리스트에 추가되었습니다.
    
    손님: 맥치킨 하나 주세요. 아 그리고 여기 화장실이 어디에요?
    답변: 맥치킨 단품 1개가 주문리스트에 추가되었습니다. 주문, 변경, 취소, 결제 외의 부분은 직원에게 문의해주세요.
    
    손님: 1955버거랑 맥너겟 주세요
    답변: 1955버거 단품 1개, 맥너겟 1개가 주문리스트에 추가되었습니다. 
    
    손님: 빅맥 세트 2개 주세요. 아 근데 왜이렇게 사람이 많아요, 1955버거도 하나 주세요 아 너는 뭐먹는다고? 저기 불고기버거 세트도 하나 주세요
    답변: 빅맥 세트 2개, 1955버거 단품 1개, 불고기버거 세트 1개가 주문리스트에 추가되었습니다. 불편을 드려서 죄송합니다.
    
    손님: 빅맥 라지세트 2개 줘 아 하나는 음료는 제로콜라로
    답변: 빅맥라지세트 1개, 빅맥라지세트 1개(음료는 제로콜라) 가 주문리스트에 추가되었습니다.
    
    손님: 지금까지 주문리스트에 있는거 말해주세요
    답변: (현재입력과 과거대화내역을 참고하여 출력하면 됨)
    
    손님: 내가 지금까지 뭐시켰더라
    답변: (현재입력과 과거대화내역을 참고하여 출력하면 됨)
    
    손님: 어우 너무 덥다 1955버거랑 맥너겟 하나 주세요. 아 1955버거는 불고기버거로 바꿔주세요.
    답변: 불고기버거 1개랑 맥너겟 1개가 주문리스트에 추가되었습니다.
    
    손님: 빅맥 주문했던거 50개로 바꿔주세요.
    답변: 주문리스트의 빅맥 단품 주문수량이 50개로 바뀌었습니다.
    
    손님: 맥플러리는 빼줘.
    답변: 주문리스트에서 맥플러리 취소되었습니다.
    
    손님: 맥너겟은 2개만 빼주세요
    답변: 주문리스트에서 맥너겟 2개가 취소되었습니다.
    
    손님: 아 저기 다음에 시킬게요 지금 얼른 가봐야되서
    답변: 주문리스트가 전부 취소되었습니다.
    
    손님: 결제
    답변: 결제를 도와드리겠습니다. 카드를 아래의 카드 투입구에 삽입해주세요.
    
    손님: 안녕하세요 맥도날드에 오랜만에 왔네 슈슈버거 하나 주세요
    답변: 안녕하세요 맥도날드를 이용해주셔서 감사합니다. 슈슈버거 단품 1개가 주문리스트에 추가되었습니다.
    
    손님: 내가 주문했던거 환불해줘
    답변: 주문, 변경, 취소, 결제 외의 부분은 직원에게 문의해주세요.'''
    
    if first_conversation==True:
        #print(f'\n--------------------------------\n{past_conversation}\n{present_conversation}{user_msg}\n--------------------------------\n')
        response=ask_to_gpt(system_msg, past_conversation+'\n'+present_conversation+user_msg)
        print(f'system: {response}')
        past_conversation+=(f'\ncustomer: {user_msg}\ngpt: {response}')
        first_conversation=False
    else:
        user_msg=input('customer: ')
        #print(f'\n--------------------------------\n{past_conversation}\n{present_conversation}{user_msg}\n--------------------------------\n')
        response=ask_to_gpt(system_msg, past_conversation+'\n'+present_conversation+user_msg)
        print(f'system: {response}')
        past_conversation+=(f'\ncustomer: {user_msg}\ngpt: {response}')
    
    
    
    
    


''' old prompt
system_msg=
너는 맥도날드에서 주문을 받는 직원이야. 입력되는 텍스트의 요청들을 파악해서 출력해줘.
이때 아래의 사항들을 반드시 지켜야되.
1. 요청 속의 의도는 주문, 변경, 취소, 결제, 기타 5가지야. 반드시 의도는 이 5개중 골라야되.
2. 의도가 주문인 경우는 요청은 '주문메뉴 주문개수 의도' 형태로 출력해줘.
3. 의도가 변경인 경우는 요청은 '바꾸기전 메뉴 바꾼후 메뉴 의도' 형태로 출력해줘.
4. 의도가 취소인 경우는 요청은 '취소할메뉴 취소개수 의도' 형태로 출력해줘.
5. 의도가 결제, 기타인 경우는 요청은 '의도' 형태로 출력해줘.
6. 개수는 1개, 2개, 3개 ... 처럼 숫자+개 형태로 출력해줘.
7. 의도가 주문인 경우는 요청에 개수정보가 없다면 1개 주문이야.
8. 의도가 변경인 경우는 요청에 개수정보가 없다면 
2. 각 요청들은 , 로 구분해서 출력해줘.
3. 이때 '답변:' 이라는 글자는 빼고 출력해줘.
4. 출력되는 요청의 순서는 입력되는 텍스트 내의 순서에따라 출력해줘.

예를 들어서,
입력: 불고기버거 주문해줘.
답변: 불고기버거 단품 1개 주문

입력: 1955버거랑 맥너겟 하나 주세요.
답변: 1955버거 단품 1개 주문, 맥너겟 1개 주문

입력: 1955버거 세트 하나 주세요. 아 그리고 제가 저혈당이 있어서 제로콜라로 주시면 안되요.
답변: 1955버거 세트 1개 주문

입력: 불고기버거 세트 주세요. 아 근데 주문이 왤케 느려요 빨리좀 해주세요.
답변: 불고기버거 세트 1개 주문, 기타

입력: 불고기버거 세트 하나 주세요. 아 근데 왜이렇게 사람이 많아요, 1955버거도 주세요.
답변: 불고기버거 세트 1개 주문, 기타, 1955버거 단품 1개 주문

입력: 빅맥 세트 2개 주세요. 아 근데 왜이렇게 사람이 많아요, 1955버거도 하나 주세요 아 너는 뭐먹는다고? 저기 불고기버거 세트도 하나 주세요   
답변: 빅맥 세트 2개 주문, 기타, 1955버거 단품 1개 주문, 불고기버거 세트 1개 주문

입력: 어우 너무 덥다 1955버거랑 맥너겟 하나 주세요. 아 1955버거는 불고기버거로 바꿔주세요.
답변: 1955버거 단품 1개 주문, 맥너겟 1개 주문, 1955버거 단품 불고기버거 단품으로 변경

입력: 아 슈슈버거는 맥치킨 버거로 바꿔
답변: 슈슈버거 단품 맥치킨 버거 단품으로 변경

입력: 맥플러리는 빼줘
답변: 맥플러리 취소

입력: 어제 주문한거를 먹었는데 맛이없었어. 환불해줘
답변: 기타

입력: 불고기 세트를 라지로 바꾸면 얼마야
답변: 기타

입력: 지금 주문을 좀 많이하려고 하는데 대량주문 되요?
답변: 기타

입력: 결제
답변: 결제

입력: 지금까지 주문한거 결제해줘
답변: 결제'''

''' old func
def query_compression(querys):
    #compressed 의 각 원소는 [주문할 항목, 개수] 이다.
    #주문, 변경, 취소, 결제 외의 의도가 들어오면 ['something', None] 을 추가한다.
    
    querys=querys.split(',')
    compressed=[]
    
    for q in querys:
        if '주문' in q:
            menu=None
            for m in MENU:
                if m in q:
                    menu=m    #q 내에 주문품목이 여러가지일수도 있다. 그러나 따로 처리하지 않는다. 의도한 메뉴랑 같은지 확인하라는 메세지를 출력할것이므로
                    break
            if menu==None:
                return [['cannot understand',None]]   #혹시 메뉴에 없는걸 주문했다면
            
            splitq=q.split()
            quantity=None
            for sq in splitq:
                if '개' in sq:
                    quantity=sq.replace('개','')
                    if quantity.find('.')!=-1 or quantity.find('-'):   #사용자가 혹시 소수개 혹은 음수개를 입력했는가
                        return [['cannot understand',None]]
                    quantity=int(quantity)
                    break
                else:
                    quantity=1
                    
            if quantity==None:
                quantity=1   #혹시 개수가 입력이 안됬으면 1개로
            compressed.append([menu,quantity])
        elif '변경' in q: pass'''






























