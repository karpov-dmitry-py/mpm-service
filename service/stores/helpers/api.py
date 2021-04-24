from ..models import System

# class for managing for own api
class API:

    api_ver = '1'
    headers = [
        'user',
        'token',
    ]

    @staticmethod
    def get_api_ver():
        return f'{API.api_ver}'

    @staticmethod
    def get_api_full_path():
        return f'api/v{API.get_api_ver()}'


    def is_valid_incoming_system_request(self, request):
        pass