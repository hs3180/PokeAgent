#!/usr/bin/env python3
"""
运行Pokemon Showdown Agent的简单脚本

使用方法:
    python scripts/run_showdown.py --agent-type rl --battles 10
    python scripts/run_showdown.py --agent-type llm --battles 5
    python scripts/run_showdown.py --challenge username --battles 3
"""

import asyncio
import argparse
import logging
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from env.showdown_manager import ShowdownManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def main():
    """
    主函数
    """
    parser = argparse.ArgumentParser(description="运行Pokemon Showdown Agent")
    parser.add_argument(
        "--agent-type",
        choices=["rl", "llm"],
        help="Agent类型"
    )
    parser.add_argument(
        "--battles",
        type=int,
        default=5,
        help="对战数量"
    )
    parser.add_argument(
        "--challenge",
        help="挑战特定用户"
    )
    parser.add_argument(
        "--username",
        help="Showdown用户名"
    )
    parser.add_argument(
        "--config",
        default="config/showdown_config.json",
        help="配置文件路径"
    )
    parser.add_argument(
        "--model-path",
        help="RL模型路径"
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.7,
        help="LLM生成温度"
    )
    
    args = parser.parse_args()
    
    print("Pokemon Showdown Agent 启动")
    print("=" * 50)
    
    # 创建Showdown管理器
    async with ShowdownManager(args.config) as manager:
        try:
            if args.challenge:
                # 挑战特定用户
                print(f"挑战用户: {args.challenge}")
                agent = manager.create_llm_agent(username=args.username)
                await manager.challenge_user(
                    opponent=args.challenge,
                    agent=agent,
                    num_battles=args.battles,
                    temperature=args.temperature
                )
                
            elif args.agent_type == "rl":
                # 运行RL Agent
                print("运行RL Agent")
                agent = manager.create_rl_agent(
                    username=args.username,
                    model_path=args.model_path
                )
                await manager.run_rl_training(
                    agent=agent,
                    num_battles=args.battles
                )
                
            elif args.agent_type == "llm":
                # 运行LLM Agent
                print("运行LLM Agent")
                agent = manager.create_llm_agent(username=args.username)
                await manager.run_llm_battles(
                    agent=agent,
                    num_battles=args.battles,
                    temperature=args.temperature
                )
                
            else:
                print("请指定Agent类型 (--agent-type rl/llm) 或挑战用户 (--challenge username)")
                return
            
            # 显示统计信息
            if args.username:
                stats = manager.get_agent_stats(args.username)
                print(f"\n最终统计:")
                for key, value in stats.items():
                    print(f"  {key}: {value}")
                    
        except KeyboardInterrupt:
            print("\n用户中断，正在退出...")
        except Exception as e:
            print(f"运行过程中发生错误: {e}")
            logging.error(f"运行错误: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())