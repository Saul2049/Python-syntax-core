#!/usr/bin/env python3
# telegram.py - Telegram通知机器人模块

import os
from typing import Optional

import requests


class TelegramBot:
    """
    Telegram机器人类，用于发送通知消息
    """

    def __init__(self, token: Optional[str] = None, chat_id: Optional[str] = None):
        """
        初始化Telegram机器人

        参数:
            token: Telegram Bot API令牌，如果为None则从环境变量TG_TOKEN读取
            chat_id: 聊天ID，如果为None则从环境变量TG_CHAT读取
        """
        self.token = token or os.getenv("TG_TOKEN")
        self.chat_id = chat_id or os.getenv("TG_CHAT")

        if not self.token or not self.chat_id:
            print("警告: 缺少TG_TOKEN或TG_CHAT环境变量，Telegram通知将不可用")

    def send(self, text: str) -> bool:
        """
        发送消息（向后兼容）

        参数:
            text: 要发送的消息文本

        返回:
            是否发送成功
        """
        return self.send_message(self.chat_id, text) if self.chat_id else False

    def send_message(self, chat_id: str, text: str, parse_mode: str = "HTML") -> bool:
        """
        发送文本消息

        参数:
            chat_id: 聊天ID
            text: 要发送的消息文本
            parse_mode: 解析模式 (HTML, Markdown, None)

        返回:
            是否发送成功
        """
        if not self.token:
            return False

        try:
            url = f"https://api.telegram.org/bot{self.token}/sendMessage"
            payload = {"chat_id": chat_id, "text": text}
            if parse_mode:
                payload["parse_mode"] = parse_mode

            response = requests.post(url, json=payload)

            if response.status_code == 200:
                return True
            else:
                print(f"发送Telegram消息失败: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            print(f"发送Telegram消息出错: {str(e)}")
            return False

    def send_photo(self, chat_id: str, photo_path: str, caption: str = "") -> bool:
        """
        发送图片消息

        参数:
            chat_id: 聊天ID
            photo_path: 图片文件路径
            caption: 图片说明文字

        返回:
            是否发送成功
        """
        if not self.token:
            return False

        try:
            url = f"https://api.telegram.org/bot{self.token}/sendPhoto"

            with open(photo_path, "rb") as photo_file:
                files = {"photo": photo_file}
                data = {"chat_id": chat_id}
                if caption:
                    data["caption"] = caption

                response = requests.post(url, files=files, data=data)

            if response.status_code == 200:
                return True
            else:
                print(f"发送Telegram图片失败: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            print(f"发送Telegram图片出错: {str(e)}")
            return False


if __name__ == "__main__":
    # 简单测试
    bot = TelegramBot()
    if bot.token and bot.chat_id:
        print("发送测试消息...")
        success = bot.send("这是一条测试消息 - This is a test message")
        print(f"结果: {'成功' if success else '失败'}")
    else:
        print("缺少TG_TOKEN或TG_CHAT环境变量，无法测试")
