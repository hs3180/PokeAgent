#!/usr/bin/env python3
"""
Pokemon对战AI演示脚本
"""

import asyncio
import logging
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent))

from agents.rl_agent import RLAgent
from agents.llm_agent import LLMAgent
from agents.base_agent import BaseAgent
from env.battle_manager import BattleManager
from poke_env.player import RandomPlayer

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

async def demo_basic_agents():
    """演示基本Agent功能"""
    print("=" * 60)
    print("演示1: 基本Agent功能")
    print("=" * 60)
    
    # 创建不同类型的Agent
    rl_agent = RLAgent()
    llm_agent = LLMAgent()
    random_agent = RandomPlayer()
    
    print(f"RL Agent: {type(rl_agent).__name__}")
    print(f"LLM Agent: {type(llm_agent).__name__}")
    print(f"Random Agent: {type(random_agent).__name__}")
    
    # 显示Agent信息
    print(f"\nRL Agent信息:")
    print(f"- 状态空间大小: {rl_agent.state_size}")
    print(f"- 动作空间大小: {rl_agent.action_size}")
    print(f"- 学习率: {rl_agent.learning_rate}")
    print(f"- 探索率: {rl_agent.epsilon}")
    
    print(f"\nLLM Agent信息:")
    llm_info = llm_agent.get_model_info()
    for key, value in llm_info.items():
        print(f"- {key}: {value}")

async def demo_battle_manager():
    """演示对战管理器功能"""
    print("\n" + "=" * 60)
    print("演示2: 对战管理器功能")
    print("=" * 60)
    
    # 创建对战管理器
    battle_manager = BattleManager(
        battle_format="gen8randombattle",
        log_battles=False  # 演示时不保存日志
    )
    
    # 创建Agent
    agent1 = RandomPlayer(battle_format="gen8randombattle")
    agent2 = RandomPlayer(battle_format="gen8randombattle")
    
    print(f"创建对战: {agent1.username} vs {agent2.username}")
    
    # 注意：实际对战需要连接到Pokemon Showdown服务器
    # 这里只是演示框架结构
    print("对战管理器已创建，可以用于协调Agent对战")

async def demo_agent_evaluation():
    """演示Agent评估功能"""
    print("\n" + "=" * 60)
    print("演示3: Agent评估功能")
    print("=" * 60)
    
    # 创建评估器
    from scripts.evaluate import AgentEvaluator
    evaluator = AgentEvaluator(
        log_dir="demo_logs",
        battle_format="gen8randombattle"
    )
    
    # 创建Agent
    agents = [
        RandomPlayer(battle_format="gen8randombattle"),
        RandomPlayer(battle_format="gen8randombattle")
    ]
    
    opponents = [RandomPlayer(battle_format="gen8randombattle")]
    
    print("评估器已创建，可以用于比较Agent性能")
    print("支持的功能:")
    print("- 单个Agent评估")
    print("- 多Agent性能比较")
    print("- 基准测试")
    print("- 性能图表生成")

async def demo_training_framework():
    """演示训练框架"""
    print("\n" + "=" * 60)
    print("演示4: 训练框架")
    print("=" * 60)
    
    # 创建训练器
    from scripts.train_rl import RLTrainer
    trainer = RLTrainer(
        model_save_dir="demo_models",
        log_dir="demo_logs",
        battle_format="gen8randombattle"
    )
    
    print("训练器已创建，支持以下功能:")
    print("- 强化学习训练")
    print("- 经验回放")
    print("- 目标网络更新")
    print("- 自动模型保存")
    print("- 训练进度监控")
    print("- 定期评估")

async def demo_llm_framework():
    """演示LLM框架"""
    print("\n" + "=" * 60)
    print("演示5: LLM框架")
    print("=" * 60)
    
    # 创建LLM运行器
    from scripts.run_llm import LLMRunner
    runner = LLMRunner(
        log_dir="demo_llm_logs",
        battle_format="gen8randombattle"
    )
    
    print("LLM运行器已创建，支持以下功能:")
    print("- 多种LLM模型支持")
    print("- 温度控制")
    print("- 响应解析")
    print("- 交互式对战")
    print("- 锦标赛模式")

def demo_configuration():
    """演示配置系统"""
    print("\n" + "=" * 60)
    print("演示6: 配置系统")
    print("=" * 60)
    
    # 加载示例配置
    import json
    config_path = "config/example_config.json"
    
    if Path(config_path).exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        print("示例配置文件内容:")
        print(json.dumps(config, indent=2, ensure_ascii=False))
    else:
        print("配置文件不存在，创建默认配置...")
        
        default_config = {
            "battle_format": "gen8randombattle",
            "agents": {
                "rl_agent": {
                    "learning_rate": 0.001,
                    "epsilon": 0.1
                },
                "llm_agent": {
                    "model_name": "microsoft/DialoGPT-medium",
                    "temperature": 0.7
                }
            }
        }
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)
        
        print("默认配置文件已创建")

async def main():
    """主演示函数"""
    print("Pokemon对战AI框架演示")
    print("=" * 60)
    
    try:
        # 演示各个组件
        await demo_basic_agents()
        await demo_battle_manager()
        await demo_agent_evaluation()
        await demo_training_framework()
        await demo_llm_framework()
        demo_configuration()
        
        print("\n" + "=" * 60)
        print("演示完成！")
        print("=" * 60)
        print("\n使用说明:")
        print("1. 训练RL Agent: python main.py --mode train --agent-type rl")
        print("2. 运行LLM Agent: python main.py --mode run --agent-type llm")
        print("3. 评估Agent: python main.py --mode evaluate --agent-type rl")
        print("4. 运行锦标赛: python main.py --mode tournament")
        print("5. 交互式对战: python main.py --mode interactive")
        
    except Exception as e:
        print(f"演示过程中出现错误: {e}")
        logging.error(f"演示错误: {e}")

if __name__ == "__main__":
    asyncio.run(main())