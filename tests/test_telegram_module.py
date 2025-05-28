#!/usr/bin/env python3
"""
测试Telegram模块 (Test Telegram Module)
"""

import os
import tempfile
from unittest.mock import Mock, mock_open, patch

import pytest
import requests

from src.telegram import TelegramBot


class TestTelegramBotInitialization:
    """测试TelegramBot初始化 (Test TelegramBot Initialization)"""

    def test_init_with_explicit_params(self):
        """测试使用显式参数初始化"""
        token = "test_token_123"
        chat_id = "test_chat_456"

        bot = TelegramBot(token=token, chat_id=chat_id)

        assert bot.token == token
        assert bot.chat_id == chat_id

    def test_init_with_env_vars(self):
        """测试使用环境变量初始化"""
        with patch.dict("os.environ", {"TG_TOKEN": "env_token_123", "TG_CHAT": "env_chat_456"}):
            bot = TelegramBot()

            assert bot.token == "env_token_123"
            assert bot.chat_id == "env_chat_456"

    def test_init_partial_env_vars(self):
        """测试部分环境变量存在的情况"""
        with patch.dict("os.environ", {"TG_TOKEN": "token_only"}, clear=True):
            bot = TelegramBot()

            assert bot.token == "token_only"
            assert bot.chat_id is None

    def test_init_no_env_vars(self):
        """测试没有环境变量的情况"""
        with patch.dict("os.environ", {}, clear=True):
            with patch("builtins.print") as mock_print:
                bot = TelegramBot()

                assert bot.token is None
                assert bot.chat_id is None
                mock_print.assert_called_once_with("警告: 缺少TG_TOKEN或TG_CHAT环境变量，Telegram通知将不可用")

    def test_init_mixed_params_and_env(self):
        """测试混合参数和环境变量"""
        with patch.dict("os.environ", {"TG_TOKEN": "env_token", "TG_CHAT": "env_chat"}):
            bot = TelegramBot(token="explicit_token")

            # 显式参数应该覆盖环境变量
            assert bot.token == "explicit_token"
            assert bot.chat_id == "env_chat"  # 从环境变量获取


class TestTelegramBotSendMessage:
    """测试TelegramBot发送消息功能 (Test TelegramBot Send Message)"""

    @pytest.fixture
    def bot_with_credentials(self):
        """创建有认证信息的bot"""
        return TelegramBot(token="test_token", chat_id="test_chat")

    @pytest.fixture
    def bot_without_token(self):
        """创建没有token的bot"""
        return TelegramBot(token=None, chat_id="test_chat")

    @patch("requests.post")
    def test_send_message_success(self, mock_post, bot_with_credentials):
        """测试成功发送消息"""
        # 设置成功响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        result = bot_with_credentials.send_message("test_chat", "Hello World")

        assert result is True
        mock_post.assert_called_once()

        # 验证请求参数
        call_args = mock_post.call_args
        assert "https://api.telegram.org/bot" in call_args[0][0]  # URL在位置参数中
        assert call_args[1]["json"]["chat_id"] == "test_chat"
        assert call_args[1]["json"]["text"] == "Hello World"
        assert call_args[1]["json"]["parse_mode"] == "HTML"

    @patch("requests.post")
    def test_send_message_with_custom_parse_mode(self, mock_post, bot_with_credentials):
        """测试使用自定义解析模式发送消息"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        result = bot_with_credentials.send_message("test_chat", "**Bold**", parse_mode="Markdown")

        assert result is True
        call_args = mock_post.call_args
        assert call_args[1]["json"]["parse_mode"] == "Markdown"

    @patch("requests.post")
    def test_send_message_without_parse_mode(self, mock_post, bot_with_credentials):
        """测试不使用解析模式发送消息"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        result = bot_with_credentials.send_message("test_chat", "Plain text", parse_mode=None)

        assert result is True
        call_args = mock_post.call_args
        assert "parse_mode" not in call_args[1]["json"]

    def test_send_message_without_token(self, bot_without_token):
        """测试没有token时发送消息"""
        result = bot_without_token.send_message("test_chat", "Hello")

        assert result is False

    @patch("requests.post")
    def test_send_message_api_error(self, mock_post, bot_with_credentials):
        """测试API错误响应"""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_post.return_value = mock_response

        with patch("builtins.print") as mock_print:
            result = bot_with_credentials.send_message("test_chat", "Hello")

            assert result is False
            mock_print.assert_called_once_with("发送Telegram消息失败: 400 - Bad Request")

    @patch("requests.post")
    def test_send_message_network_error(self, mock_post, bot_with_credentials):
        """测试网络错误"""
        mock_post.side_effect = requests.ConnectionError("Network error")

        with patch("builtins.print") as mock_print:
            result = bot_with_credentials.send_message("test_chat", "Hello")

            assert result is False
            mock_print.assert_called_once_with("发送Telegram消息出错: Network error")

    @patch("requests.post")
    def test_send_message_generic_exception(self, mock_post, bot_with_credentials):
        """测试一般异常"""
        mock_post.side_effect = Exception("Generic error")

        with patch("builtins.print") as mock_print:
            result = bot_with_credentials.send_message("test_chat", "Hello")

            assert result is False
            mock_print.assert_called_once_with("发送Telegram消息出错: Generic error")


class TestTelegramBotSendCompatible:
    """测试TelegramBot向后兼容发送功能 (Test TelegramBot Send Compatible)"""

    @pytest.fixture
    def bot_with_chat_id(self):
        """创建有chat_id的bot"""
        return TelegramBot(token="test_token", chat_id="test_chat")

    @pytest.fixture
    def bot_without_chat_id(self):
        """创建没有chat_id的bot"""
        return TelegramBot(token="test_token", chat_id=None)

    @patch.object(TelegramBot, "send_message")
    def test_send_with_chat_id(self, mock_send_message, bot_with_chat_id):
        """测试有chat_id时的send方法"""
        mock_send_message.return_value = True

        result = bot_with_chat_id.send("Hello World")

        assert result is True
        mock_send_message.assert_called_once_with("test_chat", "Hello World")

    def test_send_without_chat_id(self, bot_without_chat_id):
        """测试没有chat_id时的send方法"""
        result = bot_without_chat_id.send("Hello World")

        assert result is False


class TestTelegramBotSendPhoto:
    """测试TelegramBot发送图片功能 (Test TelegramBot Send Photo)"""

    @pytest.fixture
    def bot_with_credentials(self):
        """创建有认证信息的bot"""
        return TelegramBot(token="test_token", chat_id="test_chat")

    @pytest.fixture
    def bot_without_token(self):
        """创建没有token的bot"""
        return TelegramBot(token=None, chat_id="test_chat")

    @pytest.fixture
    def temp_image_file(self):
        """创建临时图片文件"""
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            f.write(b"fake image data")
            yield f.name
        os.unlink(f.name)

    @patch("requests.post")
    @patch("builtins.open", new_callable=mock_open, read_data=b"fake image data")
    def test_send_photo_success(self, mock_file, mock_post, bot_with_credentials):
        """测试成功发送图片"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        result = bot_with_credentials.send_photo("test_chat", "/path/to/image.jpg", "Test caption")

        assert result is True
        mock_post.assert_called_once()

        # 验证请求参数
        call_args = mock_post.call_args
        assert "https://api.telegram.org/bot" in call_args[0][0]
        assert call_args[1]["data"]["chat_id"] == "test_chat"
        assert call_args[1]["data"]["caption"] == "Test caption"
        assert "files" in call_args[1]

    @patch("requests.post")
    @patch("builtins.open", new_callable=mock_open, read_data=b"fake image data")
    def test_send_photo_without_caption(self, mock_file, mock_post, bot_with_credentials):
        """测试发送图片不带说明文字"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        result = bot_with_credentials.send_photo("test_chat", "/path/to/image.jpg")

        assert result is True
        call_args = mock_post.call_args
        assert "caption" not in call_args[1]["data"] or call_args[1]["data"]["caption"] == ""

    def test_send_photo_without_token(self, bot_without_token):
        """测试没有token时发送图片"""
        result = bot_without_token.send_photo("test_chat", "/path/to/image.jpg")

        assert result is False

    @patch("requests.post")
    @patch("builtins.open", new_callable=mock_open, read_data=b"fake image data")
    def test_send_photo_api_error(self, mock_file, mock_post, bot_with_credentials):
        """测试发送图片API错误"""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_post.return_value = mock_response

        with patch("builtins.print") as mock_print:
            result = bot_with_credentials.send_photo("test_chat", "/path/to/image.jpg")

            assert result is False
            mock_print.assert_called_once_with("发送Telegram图片失败: 400 - Bad Request")

    @patch("builtins.open", side_effect=FileNotFoundError("File not found"))
    def test_send_photo_file_error(self, mock_file, bot_with_credentials):
        """测试文件不存在错误"""
        with patch("builtins.print") as mock_print:
            result = bot_with_credentials.send_photo("test_chat", "/nonexistent/image.jpg")

            assert result is False
            mock_print.assert_called_once_with("发送Telegram图片出错: File not found")

    @patch("requests.post")
    @patch("builtins.open", new_callable=mock_open, read_data=b"fake image data")
    def test_send_photo_network_error(self, mock_file, mock_post, bot_with_credentials):
        """测试发送图片网络错误"""
        mock_post.side_effect = requests.ConnectionError("Network error")

        with patch("builtins.print") as mock_print:
            result = bot_with_credentials.send_photo("test_chat", "/path/to/image.jpg")

            assert result is False
            mock_print.assert_called_once_with("发送Telegram图片出错: Network error")


class TestTelegramBotIntegration:
    """测试TelegramBot集成 (Test TelegramBot Integration)"""

    @patch("requests.post")
    def test_full_workflow(self, mock_post):
        """测试完整工作流程"""
        # 设置成功响应
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        # 创建bot并发送消息
        bot = TelegramBot(token="test_token", chat_id="test_chat")

        # 测试不同类型的消息发送
        text_result = bot.send_message("test_chat", "Hello")
        compatible_result = bot.send("World")

        assert text_result is True
        assert compatible_result is True
        assert mock_post.call_count == 2

    @patch("requests.post")
    def test_error_recovery(self, mock_post):
        """测试错误恢复机制"""
        # 设置一个失败的响应，以防万一有请求发出
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_post.return_value = mock_response

        # 创建没有认证信息的bot
        bot = TelegramBot(token=None, chat_id=None)

        # 所有操作都应该优雅失败
        assert bot.send_message("chat", "text") is False  # 没有token
        assert bot.send("text") is False  # 没有chat_id
        assert bot.send_photo("chat", "/path") is False  # 没有token

    def test_multiple_bots(self):
        """测试多个bot实例"""
        bot1 = TelegramBot(token="token1", chat_id="chat1")
        bot2 = TelegramBot(token="token2", chat_id="chat2")

        # 验证实例独立性
        assert bot1.token != bot2.token
        assert bot1.chat_id != bot2.chat_id

    @patch.dict("os.environ", {"TG_TOKEN": "env_token", "TG_CHAT": "env_chat"})
    def test_environment_fallback(self):
        """测试环境变量回退机制"""
        # 第一个bot使用显式参数
        bot1 = TelegramBot(token="explicit_token", chat_id="explicit_chat")

        # 第二个bot使用环境变量
        bot2 = TelegramBot()

        assert bot1.token == "explicit_token"
        assert bot1.chat_id == "explicit_chat"
        assert bot2.token == "env_token"
        assert bot2.chat_id == "env_chat"

    def test_url_construction(self):
        """测试URL构建逻辑"""
        bot = TelegramBot(token="test_token_123", chat_id="test_chat")

        with patch("requests.post") as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response

            bot.send_message("chat", "text")

            # 验证URL格式正确
            call_args = mock_post.call_args
            expected_url = "https://api.telegram.org/bottest_token_123/sendMessage"
            assert call_args[0][0] == expected_url

    def test_payload_structure(self):
        """测试请求负载结构"""
        bot = TelegramBot(token="test_token", chat_id="test_chat")

        with patch("requests.post") as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response

            bot.send_message("chat123", "Hello 世界", parse_mode="Markdown")

            # 验证负载结构
            call_args = mock_post.call_args
            payload = call_args[1]["json"]

            assert payload["chat_id"] == "chat123"
            assert payload["text"] == "Hello 世界"
            assert payload["parse_mode"] == "Markdown"
