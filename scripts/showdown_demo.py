#!/usr/bin/env python3
"""
Pokemon Showdown Agent 演示脚本

这个脚本展示了如何将我们的Agent连接到Pokemon Showdown服务器进行在线对战。
"""

import asyncio
import argparse
import logging
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.showdown_rl_agent import ShowdownRLAgent
from agents.showdown_llm_agent import ShowdownLLMAgent
from agents.rl_agent import RLAgent
from agents.llm_agent import LLMAgent

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def parse_args():
    parser = argparse.ArgumentParser(description="Showdown Agent Demo")
    parser.add_argument('--server-url', type=str, required=True, help='Showdown服务器地址')
    parser.add_argument('--server-port', type=int, required=True, help='Showdown服务器端口')
    return parser.parse_args()

args = parse_args()

async def demo_rl_agent_on_showdown():
    """
    演示RL Agent在Showdown上的使用
    """
    print("=== RL Agent Showdown 演示 ===")
    
    # 创建Showdown RL Agent
    username = "RL_Agent_Demo"
    agent = ShowdownRLAgent(
        username=username,
        server_url=args.server_url,
        server_port=args.server_port,
        battle_format="gen8randombattle"
    )
    
    try:
        # 连接到Showdown服务器
        print(f"正在连接到Showdown服务器...")
        await agent.connect()
        
        # 运行几场对战
        print("开始天梯对战...")
        await agent.run_battles(num_battles=3)
        
        # 显示统计信息
        stats = agent.get_training_stats()
        print(f"\n对战统计:")
        print(f"总对战数: {stats.get('total_battles', 0)}")
        print(f"胜利: {stats.get('wins', 0)}")
        print(f"失败: {stats.get('losses', 0)}")
        
    except Exception as e:
        print(f"演示过程中发生错误: {e}")
    finally:
        await agent.disconnect()

async def demo_llm_agent_on_showdown():
    """
    演示LLM Agent在Showdown上的使用
    """
    print("\n=== LLM Agent Showdown 演示 ===")
    
    # 创建Showdown LLM Agent
    username = "LLM_Agent_Demo"
    agent = ShowdownLLMAgent(
        username=username,
        model_name="microsoft/DialoGPT-medium",
        server_url=args.server_url,
        server_port=args.server_port,
        battle_format="gen8randombattle"
    )
    
    try:
        # 连接到Showdown服务器
        print(f"正在连接到Showdown服务器...")
        await agent.connect()
        
        # 运行几场对战
        print("开始天梯对战...")
        await agent.run_showdown_battles(
            num_battles=2,
            temperature=0.7,
            max_length=100
        )
        
        # 显示统计信息
        stats = agent.get_llm_stats()
        print(f"\n对战统计:")
        print(f"总对战数: {stats.get('total_battles', 0)}")
        print(f"胜利: {stats.get('wins', 0)}")
        print(f"失败: {stats.get('losses', 0)}")
        print(f"使用模型: {stats.get('model_name', 'Unknown')}")
        
    except Exception as e:
        print(f"演示过程中发生错误: {e}")
    finally:
        await agent.disconnect()

async def demo_challenge_user():
    """
    演示挑战特定用户
    """
    print("\n=== 挑战用户演示 ===")
    
    # 创建LLM Agent
    username = "Challenge_Demo"
    agent = ShowdownLLMAgent(
        username=username,
        model_name="microsoft/DialoGPT-medium",
        server_url="sim.smogon.com",
        server_port=8000,
        battle_format="gen8randombattle"
    )
    
    try:
        # 连接到Showdown服务器
        print(f"正在连接到Showdown服务器...")
        await agent.connect()
        
        # 挑战特定用户（这里使用一个示例用户名）
        opponent = "TestUser123"  # 请替换为实际的用户名
        print(f"正在挑战用户: {opponent}")
        
        await agent.challenge_specific_user(
            opponent=opponent,
            num_battles=1,
            temperature=0.7
        )
        
    except Exception as e:
        print(f"挑战用户时发生错误: {e}")
    finally:
        await agent.disconnect()

async def demo_with_existing_model():
    """
    演示使用已训练的模型
    """
    print("\n=== 使用已训练模型演示 ===")
    
    # 检查是否存在已训练的模型
    model_path = "models/rl_model.pth"
    if not os.path.exists(model_path):
        print(f"模型文件 {model_path} 不存在，跳过此演示")
        return
    
    # 创建使用已训练模型的Showdown RL Agent
    username = "Trained_RL_Agent"
    agent = ShowdownRLAgent(
        username=username,
        model_path=model_path,
        server_url="sim.smogon.com",
        server_port=8000,
        battle_format="gen8randombattle"
    )
    
    try:
        # 连接到Showdown服务器
        print(f"正在连接到Showdown服务器...")
        await agent.connect()
        
        # 运行几场对战
        print("开始天梯对战...")
        await agent.run_battles(num_battles=2)
        
        # 显示统计信息
        stats = agent.get_training_stats()
        print(f"\n对战统计:")
        print(f"总对战数: {stats.get('total_battles', 0)}")
        print(f"胜利: {stats.get('wins', 0)}")
        print(f"失败: {stats.get('losses', 0)}")
        print(f"模型已加载: {stats.get('model_loaded', False)}")
        
    except Exception as e:
        print(f"演示过程中发生错误: {e}")
    finally:
        await agent.disconnect()

async def interactive_demo():
    """
    交互式演示
    """
    print("\n=== 交互式演示 ===")
    print("请选择要演示的功能:")
    print("1. RL Agent 天梯对战")
    print("2. LLM Agent 天梯对战")
    print("3. 挑战特定用户")
    print("4. 使用已训练模型")
    print("5. 退出")
    
    while True:
        try:
            choice = input("\n请输入选择 (1-5): ").strip()
            
            if choice == "1":
                await demo_rl_agent_on_showdown()
            elif choice == "2":
                await demo_llm_agent_on_showdown()
            elif choice == "3":
                await demo_challenge_user()
            elif choice == "4":
                await demo_with_existing_model()
            elif choice == "5":
                print("退出演示")
                break
            else:
                print("无效选择，请输入 1-5")
                
        except KeyboardInterrupt:
            print("\n用户中断，退出演示")
            break
        except Exception as e:
            print(f"发生错误: {e}")

def main():
    """
    主函数
    """
    parser = argparse.ArgumentParser(description="Pokemon Showdown Agent 演示")
    parser.add_argument(
        "--demo-type",
        choices=["rl", "llm", "challenge", "trained", "interactive"],
        default="interactive",
        help="演示类型"
    )
    parser.add_argument(
        "--username",
        default="DemoAgent",
        help="Showdown用户名"
    )
    parser.add_argument(
        "--password",
        help="Showdown密码（可选）"
    )
    parser.add_argument(
        "--battles",
        type=int,
        default=3,
        help="对战数量"
    )
    parser.add_argument(
        "--model-path",
        help="已训练模型路径"
    )
    
    args = parser.parse_args()
    
    print("Pokemon Showdown Agent 演示")
    print("=" * 50)
    
    if args.demo_type == "interactive":
        asyncio.run(interactive_demo())
    elif args.demo_type == "rl":
        asyncio.run(demo_rl_agent_on_showdown())
    elif args.demo_type == "llm":
        asyncio.run(demo_llm_agent_on_showdown())
    elif args.demo_type == "challenge":
        asyncio.run(demo_challenge_user())
    elif args.demo_type == "trained":
        asyncio.run(demo_with_existing_model())

if __name__ == "__main__":
    main()