#!/usr/bin/env python3
"""
环境变量加载脚本 - 配置Telegram通知和API密钥
"""
import os
import sys
import argparse
import configparser

def setup_parser():
    """设置命令行参数"""
    parser = argparse.ArgumentParser(description='加载环境变量')
    
    parser.add_argument('--tg_token', type=str, help='Telegram Bot Token')
    parser.add_argument('--tg_chat', type=str, help='Telegram Chat ID')
    parser.add_argument('--save', action='store_true', help='保存到.env文件')
    
    return parser

def load_env():
    """从.env文件加载环境变量"""
    env_file = '.env'
    if not os.path.exists(env_file):
        return {}
        
    env_vars = {}
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            key, value = line.split('=', 1)
            env_vars[key.strip()] = value.strip().strip('"\'')
            
    return env_vars

def save_env(env_vars):
    """保存环境变量到.env文件"""
    env_file = '.env'
    
    # 读取现有环境变量
    existing_vars = load_env()
    # 更新环境变量
    existing_vars.update(env_vars)
    
    # 写入文件
    with open(env_file, 'w') as f:
        for key, value in existing_vars.items():
            f.write(f"{key}={value}\n")
            
    print(f"环境变量已保存到 {env_file}")

def main():
    """主函数"""
    parser = setup_parser()
    args = parser.parse_args()
    
    # 尝试从.env文件加载
    env_vars = load_env()
    
    # 设置环境变量
    tg_token = args.tg_token or env_vars.get('TG_TOKEN')
    tg_chat = args.tg_chat or env_vars.get('TG_CHAT')
    
    if tg_token:
        os.environ['TG_TOKEN'] = tg_token
        print(f"已设置 TG_TOKEN 环境变量")
    
    if tg_chat:
        os.environ['TG_CHAT'] = tg_chat
        print(f"已设置 TG_CHAT 环境变量")
    
    # 保存环境变量
    if args.save and (tg_token or tg_chat):
        save_vars = {}
        if tg_token:
            save_vars['TG_TOKEN'] = tg_token
        if tg_chat:
            save_vars['TG_CHAT'] = tg_chat
            
        save_env(save_vars)
    
    # 显示说明
    if not (tg_token and tg_chat):
        print("\n请设置Telegram通知所需的环境变量:")
        print("方法1: 命令行参数")
        print("  python load_env.py --tg_token=YOUR_TOKEN --tg_chat=YOUR_CHAT_ID --save")
        print("方法2: 创建.env文件，添加以下内容:")
        print("  TG_TOKEN=YOUR_TOKEN")
        print("  TG_CHAT=YOUR_CHAT_ID")
        print("方法3: 在执行前设置环境变量:")
        print("  export TG_TOKEN=YOUR_TOKEN")
        print("  export TG_CHAT=YOUR_CHAT_ID")
    
    print("\n当前配置状态:")
    print(f"TG_TOKEN: {'已配置' if tg_token else '未配置'}")
    print(f"TG_CHAT: {'已配置' if tg_chat else '未配置'}")
    
if __name__ == "__main__":
    main() 