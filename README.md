# Pokemon对战AI

基于poke-env构建的Pokemon对战AI项目，支持强化学习(RL)和大语言模型(LLM)两种方法。

## 项目结构

```
├── agents/                 # Agent实现
│   ├── base_agent.py      # 基础Agent类
│   ├── rl_agent.py        # 强化学习Agent
│   ├── llm_agent.py       # 大语言模型Agent
│   └── __init__.py
├── env/                   # 环境相关
│   ├── poke_env_wrapper.py # poke-env包装器
│   ├── battle_manager.py   # 对战管理器
│   └── __init__.py
├── scripts/               # 脚本文件
│   ├── train_rl.py        # RL训练脚本
│   ├── run_llm.py         # LLM运行脚本
│   └── evaluate.py        # 评估脚本
├── config/                # 配置文件
│   └── example_config.json
├── tests/                 # 测试文件
├── main.py               # 主程序入口
├── requirements.txt      # 依赖列表
└── README.md            # 项目文档
```

## 功能特性

- **多种Agent类型**: 支持强化学习、大语言模型和随机Agent
- **完整的训练流程**: 包含经验回放、目标网络更新等RL标准组件
- **灵活的对战系统**: 支持单场对战、锦标赛和自我对弈训练
- **详细的评估系统**: 提供胜率、平均回合数等多维度评估
- **可视化支持**: 生成性能对比图表
- **配置化管理**: 支持JSON配置文件

## 安装

1. 克隆项目
```bash
git clone <repository-url>
cd pokemon-battle-ai
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 验证安装
```bash
python -c "import poke_env; print('poke-env安装成功')"
```

## 快速开始

### 1. 训练RL Agent

```bash
# 使用默认参数训练
python main.py --mode train --agent-type rl --episodes 1000

# 使用配置文件训练
python main.py --mode train --config config/example_config.json --episodes 500
```

### 2. 运行LLM Agent

```bash
# 运行LLM Agent对战
python main.py --mode run --agent-type llm --battles 10

# 交互式对战
python main.py --mode interactive --agent-type llm
```

### 3. 评估Agent性能

```bash
# 评估单个Agent
python main.py --mode evaluate --agent-type rl --battles 50

# 比较多个Agent
python scripts/evaluate.py --mode compare --agent-type rl --battles 30 --generate-plots
```

### 4. 运行锦标赛

```bash
# 运行锦标赛
python main.py --mode tournament --agent-type rl --rounds 3
```

## 详细使用说明

### RL Agent训练

RL Agent使用深度Q网络(DQN)算法，包含以下特性：

- **经验回放**: 存储和重放历史经验
- **目标网络**: 稳定训练过程
- **ε-贪婪策略**: 平衡探索和利用
- **自动保存**: 定期保存模型检查点

```bash
# 训练参数说明
python scripts/train_rl.py \
    --episodes 1000 \           # 训练回合数
    --epsilon-start 1.0 \       # 初始探索率
    --epsilon-end 0.01 \        # 最终探索率
    --epsilon-decay 0.995 \     # 探索率衰减
    --learning-rate 0.001 \     # 学习率
    --battle-format gen8randombattle
```

### LLM Agent使用

LLM Agent支持多种大语言模型，通过自然语言理解对战状态并做出决策：

```bash
# LLM参数说明
python scripts/run_llm.py \
    --battles 10 \              # 对战数量
    --model microsoft/DialoGPT-medium \  # 模型名称
    --temperature 0.7 \         # 生成温度
    --max-length 100 \          # 最大生成长度
    --interactive               # 交互式模式
```

### 评估系统

评估系统提供多维度的性能分析：

- **胜率统计**: 计算对各类对手的胜率
- **回合分析**: 分析平均回合数和效率
- **性能对比**: 多Agent性能比较
- **可视化**: 生成性能图表

```bash
# 评估模式
python scripts/evaluate.py \
    --mode evaluate \           # 评估模式: evaluate/compare/benchmark
    --agent-type rl \          # Agent类型
    --battles 50 \             # 对战数量
    --generate-plots           # 生成图表
```

## 配置文件

项目支持JSON配置文件来管理参数：

```json
{
  "battle_format": "gen8randombattle",
  "agents": {
    "rl_agent": {
      "learning_rate": 0.001,
      "epsilon": 0.1,
      "state_size": 100,
      "action_size": 50
    },
    "llm_agent": {
      "model_name": "microsoft/DialoGPT-medium",
      "temperature": 0.7,
      "max_length": 100
    }
  },
  "training": {
    "episodes": 1000,
    "episodes_per_eval": 50,
    "epsilon_start": 1.0,
    "epsilon_end": 0.01
  }
}
```

## API文档

### BaseAgent

基础Agent类，提供通用功能：

```python
from agents.base_agent import BaseAgent

class CustomAgent(BaseAgent):
    def choose_move(self, battle):
        # 实现自定义决策逻辑
        return self.choose_random_move(battle)
```

### BattleManager

对战管理器，协调Agent对战：

```python
from env.battle_manager import BattleManager

manager = BattleManager()
result = await manager.run_battle(agent1, agent2)
```

### RLAgent

强化学习Agent：

```python
from agents.rl_agent import RLAgent

agent = RLAgent(learning_rate=0.001, epsilon=0.1)
agent.save_model("model.pth")
agent.load_model("model.pth")
```

### LLMAgent

大语言模型Agent：

```python
from agents.llm_agent import LLMAgent

agent = LLMAgent(model_name="microsoft/DialoGPT-medium")
agent.set_temperature(0.7)
```

## 开发指南

### 添加新的Agent类型

1. 继承BaseAgent类
2. 实现choose_move方法
3. 在main.py中添加支持

### 扩展评估指标

1. 在AgentEvaluator中添加新的统计方法
2. 更新评估报告生成逻辑
3. 添加相应的可视化

### 自定义对战格式

1. 修改battle_format参数
2. 调整状态表示方法
3. 更新动作空间定义

## 故障排除

### 常见问题

1. **poke-env连接问题**
   - 检查网络连接
   - 确认服务器状态

2. **模型加载失败**
   - 检查模型路径
   - 确认模型格式

3. **内存不足**
   - 减少batch_size
   - 降低memory_size

### 日志分析

项目生成详细的日志文件：

- `logs/`: 训练和运行日志
- `battle_logs/`: 对战记录
- `evaluation_logs/`: 评估结果
- `models/`: 保存的模型

## 贡献指南

1. Fork项目
2. 创建功能分支
3. 提交更改
4. 创建Pull Request

## 许可证

本项目采用MIT许可证。

## 致谢

- [poke-env](https://github.com/hsahovic/poke-env): Pokemon对战环境
- [PyTorch](https://pytorch.org/): 深度学习框架
- [Transformers](https://huggingface.co/transformers/): 大语言模型库
