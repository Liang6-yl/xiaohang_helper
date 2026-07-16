import unittest
from unittest.mock import patch, MagicMock
from src.api import call_doubao_api


class TestDoubaoAPI(unittest.TestCase):

    def test_empty_api_key(self):
        with patch('src.api.DOUBAO_API_KEY', ''):
            with patch('src.api.DOUBAO_MODEL', 'test_model'):
                result = call_doubao_api([{"role": "user", "content": "test"}])
                self.assertIn("未配置 API 密钥", result)

    def test_empty_model(self):
        with patch('src.api.DOUBAO_API_KEY', 'test_key'):
            with patch('src.api.DOUBAO_MODEL', ''):
                result = call_doubao_api([{"role": "user", "content": "test"}])
                self.assertIn("未配置 API 模型", result)

    def test_api_connection_error(self):
        with patch('src.api.DOUBAO_API_KEY', 'test_key'):
            with patch('src.api.DOUBAO_MODEL', 'test_model'):
                with patch('requests.post') as mock_post:
                    from requests.exceptions import ConnectionError
                    mock_post.side_effect = ConnectionError("Connection refused")
                    result = call_doubao_api([{"role": "user", "content": "test"}])
                    self.assertIn("API调用失败", result)

    def test_api_timeout(self):
        with patch('src.api.DOUBAO_API_KEY', 'test_key'):
            with patch('src.api.DOUBAO_MODEL', 'test_model'):
                with patch('requests.post') as mock_post:
                    from requests.exceptions import Timeout
                    mock_post.side_effect = Timeout("Request timed out")
                    result = call_doubao_api([{"role": "user", "content": "test"}])
                    self.assertIn("API调用失败", result)

    def test_api_http_error_400(self):
        with patch('src.api.DOUBAO_API_KEY', 'test_key'):
            with patch('src.api.DOUBAO_MODEL', 'test_model'):
                with patch('requests.post') as mock_post:
                    from requests.exceptions import HTTPError
                    mock_response = MagicMock()
                    mock_response.raise_for_status.side_effect = HTTPError("400 Bad Request")
                    mock_post.return_value = mock_response
                    result = call_doubao_api([{"role": "user", "content": "test"}])
                    self.assertIn("API调用失败", result)

    def test_api_http_error_401(self):
        with patch('src.api.DOUBAO_API_KEY', 'test_key'):
            with patch('src.api.DOUBAO_MODEL', 'test_model'):
                with patch('requests.post') as mock_post:
                    from requests.exceptions import HTTPError
                    mock_response = MagicMock()
                    mock_response.raise_for_status.side_effect = HTTPError("401 Unauthorized")
                    mock_post.return_value = mock_response
                    result = call_doubao_api([{"role": "user", "content": "test"}])
                    self.assertIn("API调用失败", result)

    def test_api_http_error_403(self):
        with patch('src.api.DOUBAO_API_KEY', 'test_key'):
            with patch('src.api.DOUBAO_MODEL', 'test_model'):
                with patch('requests.post') as mock_post:
                    from requests.exceptions import HTTPError
                    mock_response = MagicMock()
                    mock_response.raise_for_status.side_effect = HTTPError("403 Forbidden")
                    mock_post.return_value = mock_response
                    result = call_doubao_api([{"role": "user", "content": "test"}])
                    self.assertIn("API调用失败", result)

    def test_api_http_error_500(self):
        with patch('src.api.DOUBAO_API_KEY', 'test_key'):
            with patch('src.api.DOUBAO_MODEL', 'test_model'):
                with patch('requests.post') as mock_post:
                    from requests.exceptions import HTTPError
                    mock_response = MagicMock()
                    mock_response.raise_for_status.side_effect = HTTPError("500 Internal Server Error")
                    mock_post.return_value = mock_response
                    result = call_doubao_api([{"role": "user", "content": "test"}])
                    self.assertIn("API调用失败", result)

    def test_api_http_error_503(self):
        with patch('src.api.DOUBAO_API_KEY', 'test_key'):
            with patch('src.api.DOUBAO_MODEL', 'test_model'):
                with patch('requests.post') as mock_post:
                    from requests.exceptions import HTTPError
                    mock_response = MagicMock()
                    mock_response.raise_for_status.side_effect = HTTPError("503 Service Unavailable")
                    mock_post.return_value = mock_response
                    result = call_doubao_api([{"role": "user", "content": "test"}])
                    self.assertIn("API调用失败", result)

    def test_invalid_json_response(self):
        with patch('src.api.DOUBAO_API_KEY', 'test_key'):
            with patch('src.api.DOUBAO_MODEL', 'test_model'):
                with patch('requests.post') as mock_post:
                    mock_response = MagicMock()
                    mock_response.raise_for_status.return_value = None
                    mock_response.json.side_effect = ValueError("Invalid JSON")
                    mock_post.return_value = mock_response
                    result = call_doubao_api([{"role": "user", "content": "test"}])
                    self.assertIn("API响应解析失败", result)

    def test_missing_choices_key(self):
        with patch('src.api.DOUBAO_API_KEY', 'test_key'):
            with patch('src.api.DOUBAO_MODEL', 'test_model'):
                with patch('requests.post') as mock_post:
                    mock_response = MagicMock()
                    mock_response.raise_for_status.return_value = None
                    mock_response.json.return_value = {"error": "something went wrong"}
                    mock_post.return_value = mock_response
                    result = call_doubao_api([{"role": "user", "content": "test"}])
                    self.assertIn("API响应解析失败", result)

    def test_empty_choices_array(self):
        with patch('src.api.DOUBAO_API_KEY', 'test_key'):
            with patch('src.api.DOUBAO_MODEL', 'test_model'):
                with patch('requests.post') as mock_post:
                    mock_response = MagicMock()
                    mock_response.raise_for_status.return_value = None
                    mock_response.json.return_value = {"choices": []}
                    mock_post.return_value = mock_response
                    result = call_doubao_api([{"role": "user", "content": "test"}])
                    self.assertIn("API响应解析失败", result)

    def test_missing_message_content(self):
        with patch('src.api.DOUBAO_API_KEY', 'test_key'):
            with patch('src.api.DOUBAO_MODEL', 'test_model'):
                with patch('requests.post') as mock_post:
                    mock_response = MagicMock()
                    mock_response.raise_for_status.return_value = None
                    mock_response.json.return_value = {"choices": [{"message": {}}]}
                    mock_post.return_value = mock_response
                    result = call_doubao_api([{"role": "user", "content": "test"}])
                    self.assertIn("API响应解析失败", result)

    def test_valid_api_response(self):
        with patch('src.api.DOUBAO_API_KEY', 'test_key'):
            with patch('src.api.DOUBAO_MODEL', 'test_model'):
                with patch('requests.post') as mock_post:
                    mock_response = MagicMock()
                    mock_response.raise_for_status.return_value = None
                    mock_response.json.return_value = {
                        "choices": [{"message": {"content": "这是测试响应"}}]
                    }
                    mock_post.return_value = mock_response
                    result = call_doubao_api([{"role": "user", "content": "test"}])
                    self.assertEqual(result, "这是测试响应")


if __name__ == '__main__':
    unittest.main()
