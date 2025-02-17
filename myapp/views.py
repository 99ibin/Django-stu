from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.conf import settings
import requests
from .authentication import KakaoAuth, kakao_login_required
from .models import KakaoProfile, UserProfile, NewsPost, Project
from django.contrib.auth.models import User
import json
from functools import wraps
from django.contrib import messages
from django.contrib.auth import login, authenticate
from .forms import SignUpForm

# Create your views here.

def home(request):
    context = {
        'news_posts': NewsPost.objects.all().order_by('-date')[:5],  # NewsPosts를 NewsPost로 수정
        'projects': Project.objects.all(),  # 모든 프로젝트
    }
    return render(request, 'myapp/home.html', context)

def kakao_login(request):
    kakao_auth = KakaoAuth()
    auth_url = kakao_auth.get_auth_url()
    return redirect(auth_url)

def kakao_callback(request):
    code = request.GET.get("code")
    kakao_auth = KakaoAuth()
    
    try:
        # 토큰 받기
        token_json = kakao_auth.get_token(code)
        
        if 'error' in token_json:
            messages.error(request, '로그인 중 오류가 발생했습니다.')
            return redirect('myapp:home')
            
        access_token = token_json.get("access_token")
        refresh_token = token_json.get("refresh_token")
        
        if not access_token:
            messages.error(request, '토큰을 받아오지 못했습니다.')
            return redirect('myapp:home')
        
        # 사용자 정보 받기
        profile_json = kakao_auth.get_user_info(access_token)
        kakao_id = profile_json.get("id")
        
        if not kakao_id:
            messages.error(request, '사용자 정보를 받아오지 못했습니다.')
            return redirect('myapp:home')
        
        # 사용자 생성 또는 가져오기
        user, created = User.objects.get_or_create(
            username=f"kakao_{kakao_id}",
            defaults={
                'first_name': profile_json.get('properties', {}).get('nickname', '')
            }
        )
        
        kakao_profile, _ = KakaoProfile.objects.get_or_create(
            user=user,
            kakao_id=kakao_id
        )
        
        # 세션에 토큰 저장
        request.session['access_token'] = access_token
        request.session['refresh_token'] = refresh_token
        request.session['user_id'] = user.id
        
        messages.success(request, '로그인되었습니다.')
        return redirect('myapp:home')
        
    except Exception as e:
        print(f"Error during login: {str(e)}")  # 로깅 추가
        messages.error(request, '로그인 처리 중 오류가 발생했습니다.')
        return redirect('myapp:home')

def login_required(f):
    @wraps(f)
    def decorated_function(request, *args, **kwargs):
        access_token = request.session.get('access_token')
        if not access_token:
            return JsonResponse({"error": "로그인이 필요합니다"})
        return f(request, *args, **kwargs)
    return decorated_function

@login_required
def send_kakao_message(request):
    access_token = request.session.get('access_token')
    
    # 토큰 값 확인을 위한 디버깅
    print("Access Token:", access_token)  # 콘솔에 토큰 출력
    
    if not access_token:
        return JsonResponse({
            "error": "토큰이 없습니다",
            "session_data": dict(request.session)  # 세션 데이터 확인
        }, status=400)

    template_object = {
        "object_type": "text",
        "text": "테스트 메시지입니다.",
        "link": {
            "web_url": "http://127.0.0.1:8000",
            "mobile_web_url": "http://127.0.0.1:8000"
        }
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/x-www-form-urlencoded"
    }

    data = {
        "template_object": json.dumps(template_object)
    }

    try:
        response = requests.post(
            "https://kapi.kakao.com/v2/api/talk/memo/default/send",
            headers=headers,
            data=data
        )
        
        print("Response Status:", response.status_code)  # 응답 상태 코드 출력
        print("Response Text:", response.text)  # 응답 내용 출력

        if response.status_code != 200:
            return JsonResponse({
                "error": "메시지 전송 실패",
                "status_code": response.status_code,
                "response_text": response.text,
                "token_used": access_token  # 사용된 토큰 값도 함께 반환
            }, status=400)

        return JsonResponse({"message": "메시지가 성공적으로 전송되었습니다."})
        
    except Exception as e:
        return JsonResponse({
            "error": "예외 발생",
            "details": str(e)
        }, status=500)

def kakao_pay(request):
    admin_key = settings.KAKAO_ADMIN_KEY  # settings.py에 추가 필요
    headers = {
        "Authorization": f"KakaoAK {admin_key}",
        "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"
    }
    
    data = {
        "cid": "TC0ONETIME",  # 테스트용 CID
        "partner_order_id": "partner_order_id",
        "partner_user_id": "partner_user_id",
        "item_name": "초코파이",
        "quantity": 1,
        "total_amount": 2200,
        "vat_amount": 200,
        "tax_free_amount": 0,
        "approval_url": "http://localhost:8000/payment/success",
        "fail_url": "http://localhost:8000/payment/fail",
        "cancel_url": "http://localhost:8000/payment/cancel",
    }
    
    response = requests.post('https://kapi.kakao.com/v1/payment/ready', headers=headers, data=data)
    return JsonResponse(response.json())

def get_friends_list(request):
    access_token = request.session.get('access_token')
    if not access_token:
        return JsonResponse({"error": "로그인이 필요합니다"})

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.get(
        "https://kapi.kakao.com/v1/api/talk/friends",
        headers=headers
    )
    
    return JsonResponse(response.json())

def logout(request):
    access_token = request.session.get('access_token')
    if access_token:
        # 카카오 로그아웃
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        requests.post(
            "https://kapi.kakao.com/v1/user/logout",
            headers=headers
        )
    
    # 세션 클리어
    request.session.flush()
    return redirect('myapp:home')

@kakao_login_required
def map_view(request):
    context = {
        'kakao_maps_api_key': settings.KAKAO_MAPS_API_KEY,
    }
    return render(request, 'myapp/map.html', context)

def signup(request):
    if request.method == 'POST':
        try:
            # 받은 데이터 출력
            print("Received POST data:", request.POST)
            print("Username:", request.POST.get('username'))
            print("Email:", request.POST.get('email'))
            print("Password length:", len(request.POST.get('password1', '')))
            
            # 기존 사용자 확인
            if User.objects.filter(username=request.POST.get('username')).exists():
                return JsonResponse({
                    'success': False,
                    'message': '이미 존재하는 사용자명입니다.',
                    'errors': {'username': ['이미 존재하는 사용자명입니다.']}
                })
            
            if User.objects.filter(email=request.POST.get('email')).exists():
                return JsonResponse({
                    'success': False,
                    'message': '이미 등록된 이메일입니다.',
                    'errors': {'email': ['이미 등록된 이메일입니다.']}
                })
            
            # 비밀번호 유효성 검사
            password = request.POST.get('password1')
            if len(password) < 8:
                return JsonResponse({
                    'success': False,
                    'message': '비밀번호는 8자 이상이어야 합니다.',
                    'errors': {'password1': ['비밀번호는 8자 이상이어야 합니다.']}
                })
            
            # 사용자 생성
            user = User.objects.create_user(
                username=request.POST.get('username'),
                email=request.POST.get('email'),
                password=password
            )
            
            # UserProfile 생성
            UserProfile.objects.create(
                user=user,
                phone_number=request.POST.get('phone_number', '')
            )
            
            # 회원가입 후 자동 로그인
            login(request, user)
            
            return JsonResponse({
                'success': True,
                'message': '회원가입이 완료되었습니다!'
            })
            
        except Exception as e:
            print(f"Error type: {type(e)}")
            print(f"Error details: {str(e)}")
            print(f"Error location:", e.__traceback__.tb_lineno)
            return JsonResponse({
                'success': False,
                'message': '회원가입 처리 중 오류가 발생했습니다.',
                'errors': {'__all__': [str(e)]}
            })
    
    return JsonResponse({'success': False, 'message': '잘못된 요청입니다.'})

def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # authenticate() 함수가 데이터베이스에서 사용자 확인
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)  # 로그인 성공
            return JsonResponse({
                'success': True,
                'message': '로그인 성공!'
            })
        else:  # 데이터베이스에서 일치하는 정보를 찾지 못함
            return JsonResponse({
                'success': False,
                'message': '아이디 또는 비밀번호가 올바르지 않습니다.'
            })
    return JsonResponse({'success': False, 'message': '잘못된 요청입니다.'})

# Create (회원가입)
def create_user(request):
    user = User.objects.create_user(
        username='username',
        email='email@example.com',
        password='password'
    )
    # 프로필 생성
    UserProfile.objects.create(
        user=user,
        phone_number='010-1234-5678'
    )
    return user

# Read (사용자 정보 조회)
def get_user_info(request, user_id):
    user = get_object_or_404(User, id=user_id)
    profile = UserProfile.objects.get(user=user)
    return {
        'username': user.username,
        'email': user.email,
        'phone': profile.phone_number
    }

# Update (사용자 정보 수정)
def update_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    profile = UserProfile.objects.get(user=user)
    
    # 사용자 정보 업데이트
    user.email = 'new_email@example.com'
    user.save()
    
    # 프로필 정보 업데이트
    profile.phone_number = '010-9876-5432'
    profile.save()

# Delete (회원 탈퇴)
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.delete()  # 연결된 프로필도 자동으로 삭제됨 (CASCADE)
