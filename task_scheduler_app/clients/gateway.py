import requests
import json

from task_scheduler_app import settings
from task_scheduler_app.tools.helpers import logger


class Gateway:
    def __init__(self) -> None:
        self.base_url = settings.BASE_URL
        self.signin_url = f'{self.base_url}/api/auth/signin/'
        self.signup_url = f'{self.base_url}/api/auth/signup/'
        self.user_url = f'{self.base_url}/api/users/'
        self.current_user_url = f'{self.base_url}/api/users/me/'
        self.images_url = f'{self.base_url}/api/images/'
        self.current_user_image_url = f'{self.base_url}/api/images/me/'
        self.token = None

    def register(self, data):
        try:
            token = None
            error =None

            headers = {}
            headers['Content-Type'] = 'application/json'

            payload = json.dumps(data)
            r = requests.post(self.gateway_signup_url, verify=False, data=payload, headers= headers)
            if r.status_code == 201:
                res = r.json()
                token = res['access_token']
                self.token = token
            else:
                logger.error("=====> register failed --> failed")
                logger.error(r.status_code)
                logger.error(r.text)
                error = json.loads(r.text)
            return token,error
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return None,None

    def login(self, data):
        try:
            token = None
            error =None

            headers = {}
            headers['Content-Type'] = 'application/json'

            payload = json.dumps(data)
            r = requests.post(self.gateway_signin_url, verify=False, data=payload, headers= headers)
            if r.status_code == 200:
                res = r.json()
                token = res['access_token']
                self.token = token
            else:
                logger.error("=====> login failed --> failed")
                logger.error(r.status_code)
                logger.error(r.text)
                error = json.loads(r.text)
            return token,error
        except Exception as e:
            logger.error(f"Error logging user: {e}")
            return None,None

    def get_user_by_email(self, email, use_admin_token=False, admin_credentials=None):
        try:
            if use_admin_token and admin_credentials:
                logger.info("Using admin token to get user data")
                self.login(admin_credentials) # set the token to the admin token
            if not self.token:
                raise ValueError(f"No token was provided. Failed to get user {email} data")
            
            headers = {}
            headers['Content-Type'] = 'application/json'
            headers['Authorization'] = f'Bearer {self.token}'
            current_user_url = f"{self.gateway_user_url}/?email={email}"

            r = requests.get(current_user_url, headers=headers)
            if r.status_code == 200:
                user = r.json()
                return user
            else:
                logger.error(f"=====> getting user {email} data failed --> failed")
                logger.error(r.status_code)
                logger.error(r.text)
            return None

        except Exception as error:
            logger.info(f"Error getting user {email} daata: {error}")

    def get_current_user(self):
        try:
            headers = {}
            headers['Content-Type'] = 'application/json'
            headers['Authorization'] = f'Bearer {self.token}'
            r = requests.get(self.gateway_current_user_url, verify=False, headers= headers)
            if r.status_code == 200:
                user = r.json()
                return user
            else:
                logger.error("=====> get current user failed --> failed")
                logger.error(r.status_code)
                logger.error(r.text)
            return None
        except Exception as e:
            logger.error(f"Error getting current user: {e}")
            return None
    
    def get_current_user_image(self):
        try:
            headers = {}
            headers['Content-Type'] = 'application/json'
            headers['Authorization'] = f'Bearer {self.token}'
            r = requests.get(self.gateway_current_user_image_url, verify=False, headers= headers)
            if r.status_code == 200:
                user_image = r.json()
                return user_image
            else:
                logger.error("=====> get current user image failed --> failed")
                logger.error(r.status_code)
                logger.error(r.text)
            return None
        except Exception as e:
            logger.error(f"Error getting current user image: {e}")
            return None

    def upload_image(self, image_file, username):
        try:
            data = None
            error =None

            headers = {}
            headers['Authorization'] = f'Bearer {self.token}'

            files = {'file': (image_file._name, image_file, image_file.content_type), 'username': (None, username)}

            r = requests.post(self.gateway_images_url, headers=headers, files=files)

            if r.status_code == 201:
                data = r.json()
            else:
                logger.error("=====> upload user image failed failed --> failed")
                logger.error(r.status_code)
                logger.error(r.text)
                error = json.loads(r.text)
            return data, error

        except Exception as e:
            logger.error(f"Error uploading image: {e}")
            return None,None