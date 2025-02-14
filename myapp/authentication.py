from django.conf import settings
import requests
from django.shortcuts import redirect
from functools import wraps
from django.contrib import messages

class KakaoAuth:
    def __init__(self):
        self.client_id = settings.KAKAO_REST_API_KEY
        self.redirect_uri = settings.KAKAO_REDIRECT_URI

    def get_auth_url(self):
        scope = "talk_message,profile_nickname,profile_image"  # 필요한 모든 권한을 명시
        return f"https://kauth.kakao.com/oauth/authorize?client_id={self.client_id}&redirect_uri={self.redirect_uri}&response_type=code&scope={scope}"

    def get_token(self, code):
        try:
            token_request = requests.post(
                "https://kauth.kakao.com/oauth/token",
                data={
                    "grant_type": "authorization_code",
                    "client_id": self.client_id,
                    "redirect_uri": self.redirect_uri,
                    "code": code,
                    "scope": "talk_message,profile_nickname,profile_image"  # scope 추가
                }
            )
            token_request.raise_for_status()
            return token_request.json()
        except requests.exceptions.RequestException as e:
            print(f"Token request error: {str(e)}")
            return {"error": str(e)}

    def get_user_info(self, access_token):
        try:
            profile_request = requests.get(
                "https://kapi.kakao.com/v2/user/me",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            profile_request.raise_for_status()  # HTTP 오류 체크
            return profile_request.json()
        except requests.exceptions.RequestException as e:
            print(f"Profile request error: {str(e)}")  # 로깅 추가
            return {"error": str(e)}

def kakao_login_required(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        if 'access_token' not in request.session:
            messages.warning(request, '이 기능을 사용하려면 로그인이 필요합니다.')
            return redirect('myapp:kakao_login')
        return function(request, *args, **kwargs)
    return wrap