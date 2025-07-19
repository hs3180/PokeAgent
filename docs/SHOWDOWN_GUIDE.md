# Pokemon Showdown Agent 使用指南

本指南介绍如何将我们的Agent接入到Pokemon Showdown服务器进行在线对战。

## 概述

我们提供了三种类型的Showdown Agent：

1. **ShowdownAgent**: 基础Showdown Agent类
2. **ShowdownRLAgent**: 基于强化学习的Showdown Agent
3. **ShowdownLLMAgent**: 基于大语言模型的Showdown Agent

## 快速开始

### 1. 基本使用

```python
import asyncio
from agents.showdown_llm_agent import ShowdownLLMAgent

async def main():
    # 创建LLM Agent
    agent = ShowdownLLMAgent(
        username="MyAgent",
        model_name="microsoft/DialoGPT-medium"
    )
    
    # 连接到Showdown服务器
    await agent.connect()
    
    # 运行对战
    await agent.run_showdown_battles(num_battles=5)
    
    # 断开连接
    await agent.disconnect()

asyncio.run(main())
```

### 2. 使用Showdown管理器

```python
import asyncio
from env.showdown_manager import ShowdownManager

async def main():
    async with ShowdownManager() as manager:
        # 创建LLM Agent
        agent = manager.create_llm_agent(username="MyAgent")
        
        # 运行对战
        await manager.run_llm_battles(
            agent=agent,
            num_battles=10,
            temperature=0.7
        )

asyncio.run(main())
```

## 详细使用说明

### ShowdownRLAgent

RL Agent可以在Showdown上进行在线训练：

```python
from agents.showdown_rl_agent import ShowdownRLAgent

# 创建RL Agent
agent = ShowdownRLAgent(
    username="RL_Trainer",
    model_path="models/pretrained_model.pth"  # 可选：加载预训练模型
)

# 在线训练
await agent.train_on_showdown(
    num_battles=100,
    save_interval=10,
    model_save_path="models/showdown_trained.pth"
)
```

### ShowdownLLMAgent

LLM Agent支持多种参数配置：

```python
from agents.showdown_llm_agent import ShowdownLLMAgent

# 创建LLM Agent
agent = ShowdownLLMAgent(
    username="LLM_Player",
    model_name="microsoft/DialoGPT-medium"
)

# 设置参数
agent.set_temperature(0.8)
agent.set_max_length(150)

# 运行对战
await agent.run_showdown_battles(
    num_battles=10,
    temperature=0.7,
    max_length=100
)

# 挑战特定用户
await agent.challenge_specific_user(
    opponent="SomePlayer",
    num_battles=3,
    temperature=0.6
)
```

### 配置文件

创建配置文件 `config/showdown_config.json`：

```json
{
  "showdown": {
    "server": {
      "url": "sim.smogon.com",
      "port": 8000,
      "secure": false
    },
    "credentials": {
      "username": "YourAgentName",
      "password": null
    },
    "battle_format": "gen8randombattle",
    "log_level": "INFO"
  },
  "rl_agent": {
    "model_path": "models/showdown_rl_model.pth",
    "save_interval": 10,
    "training": {
      "num_battles": 100,
      "epsilon_start": 1.0,
      "epsilon_end": 0.01,
      "epsilon_decay": 0.995,
      "learning_rate": 0.001
    }
  },
  "llm_agent": {
    "model_name": "microsoft/DialoGPT-medium",
    "temperature": 0.7,
    "max_length": 100,
    "top_p": 0.9,
    "do_sample": true
  },
  "battle_settings": {
    "default_battles": 5,
    "challenge_cooldown": 5,
    "ladder_wait_time": 2,
    "max_concurrent_battles": 1
  }
}
```

## 命令行使用

### 基本命令

```bash
# 运行RL Agent
python scripts/run_showdown.py --agent-type rl --battles 10

# 运行LLM Agent
python scripts/run_showdown.py --agent-type llm --battles 5

# 挑战特定用户
python scripts/run_showdown.py --challenge username --battles 3

# 使用自定义用户名
python scripts/run_showdown.py --agent-type llm --username MyAgent --battles 10
```

### 演示脚本

```bash
# 交互式演示
python scripts/showdown_demo.py

# 特定演示
python scripts/showdown_demo.py --demo-type rl
python scripts/showdown_demo.py --demo-type llm
```

## 高级功能

### 1. 异步上下文管理器

```python
async with ShowdownLLMAgent(username="MyAgent") as agent:
    await agent.run_showdown_battles(num_battles=5)
    # 自动断开连接
```

### 2. 统计信息

```python
# 获取对战统计
stats = agent.get_battle_stats()
print(f"总对战: {stats['total_battles']}")
print(f"胜利: {stats['wins']}")
print(f"失败: {stats['losses']}")

# 获取LLM统计
llm_stats = agent.get_llm_stats()
print(f"使用模型: {llm_stats['model_name']}")
print(f"温度: {llm_stats['temperature']}")
```

### 3. 错误处理

```python
try:
    await agent.connect()
    await agent.run_battles(num_battles=5)
except Exception as e:
    logging.error(f"连接或对战失败: {e}")
finally:
    await agent.disconnect()
```

## 注意事项

### 1. 服务器限制

- 遵守Showdown服务器的使用条款
- 避免过于频繁的请求
- 使用合理的用户名

### 2. 网络连接

- 确保网络连接稳定
- 处理连接中断的情况
- 实现重连机制

### 3. 资源管理

- 及时断开连接
- 监控内存使用
- 定期保存模型

### 4. 对战格式

支持的对战格式：
- `gen8randombattle`: 第八代随机对战
- `gen7randombattle`: 第七代随机对战
- `gen6randombattle`: 第六代随机对战
- 其他格式请参考Showdown文档

## 故障排除

### 常见问题

1. **连接失败**
   - 检查网络连接
   - 验证服务器地址和端口
   - 确认用户名可用

2. **对战无法开始**
   - 检查对战格式是否正确
   - 确认服务器状态
   - 等待更长时间

3. **Agent决策失败**
   - 检查模型文件是否存在
   - 验证模型格式
   - 查看错误日志

### 调试模式

启用详细日志：

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# 或者在配置文件中设置
{
  "showdown": {
    "log_level": "DEBUG"
  }
}
```

## 扩展开发

### 自定义Agent

```python
from agents.showdown_agent import ShowdownAgent

class CustomShowdownAgent(ShowdownAgent):
    def choose_move(self, battle):
        # 实现自定义决策逻辑
        return self.choose_random_move(battle)
```

### 添加新功能

1. 继承相应的Agent类
2. 重写需要的方法
3. 添加新的功能
4. 更新文档

## 相关链接

- [poke-env文档](https://poke-env.readthedocs.io/)
- [Pokemon Showdown](https://pokemonshowdown.com/)
- [项目主页](README.md)