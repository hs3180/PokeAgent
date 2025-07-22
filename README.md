# 宝可梦对战AI平台（支持RL/LLM/Showdown）

本项目是一个基于 [poke-env](https://github.com/hsahovic/poke-env) 的宝可梦（Pokemon）对战AI平台，支持强化学习（RL）、大语言模型（LLM）和 Showdown 在线对战三大智能体体系，适用于AI算法研究、对比实验、自动化对战和平台接入。

---

## 目录结构

```
├── agents/                  # 智能体实现（RL/LLM/Showdown）
│   ├── base_agent.py        # 基础智能体类
│   ├── rl_agent.py          # 强化学习智能体
│   ├── llm_agent.py         # 大语言模型智能体
│   ├── showdown_agent.py    # Showdown通用智能体
│   ├── showdown_llm_agent.py# Showdown LLM智能体
│   ├── showdown_rl_agent.py # Showdown RL智能体
│   └── __init__.py
├── env/                     # 环境与对战管理
│   ├── poke_env_wrapper.py  # poke-env环境封装
│   ├── battle_manager.py    # 本地对战管理器
│   ├── showdown_manager.py  # Showdown对战管理器
│   └── __init__.py
├── scripts/                 # 训练、评测与Showdown脚本
│   ├── train_rl.py          # RL训练脚本
│   ├── run_llm.py           # LLM对战脚本
│   ├── evaluate.py          # 智能体评测与对比
│   ├── run_showdown.py      # Showdown对战脚本
│   ├── showdown_demo.py     # Showdown演示脚本
│   └── __pycache__/
├── config/                  # 配置文件
│   ├── example_config.json  # 本地训练/对战配置示例
│   └── showdown_config.json # Showdown平台配置示例
├── tests/                   # 单元测试
│   ├── test_agents.py
│   └── test_showdown_agent.py
├── docs/                    # 文档
│   └── SHOWDOWN_GUIDE.md    # Showdown平台接入指南
├── main.py                  # 项目主入口，支持多模式
├── demo.py                  # 主要功能演示脚本
├── requirements.txt         # 依赖列表
└── README.md                # 项目说明文档
```

---

## 功能亮点

- **多智能体体系**：支持强化学习（DQN）、大语言模型（Huggingface Transformers）、随机智能体、Showdown专用智能体。
- **本地与在线对战**：既可本地模拟对战，也可接入 Pokemon Showdown 平台进行真实在线对战。
- **完整训练与评测流程**：内置经验回放、目标网络、自动保存、性能评测与可视化。
- **灵活配置**：支持 JSON 配置文件，参数可灵活调整。
- **丰富脚本与演示**：一键训练、对战、评测、Showdown演示、功能演示脚本齐全。
- **完善测试与文档**：自带单元测试与详细平台接入文档。

---

## 安装与环境要求

- Python >= 3.8
- 推荐使用虚拟环境

```bash
git clone <repository-url>
cd <项目根目录>
pip install -r requirements.txt
```

---

## 快速上手

### 1. 训练强化学习智能体

```bash
# 使用主入口训练
python main.py --mode train --agent-type rl --episodes 1000

# 使用专用脚本训练（参数更丰富）
python scripts/train_rl.py --episodes 1000 --epsilon-start 1.0 --epsilon-end 0.01 --learning-rate 0.001
```

### 2. 运行大语言模型智能体对战

```bash
# 本地 LLM 智能体对战
python main.py --mode run --agent-type llm --battles 10

# 使用脚本自定义模型
python scripts/run_llm.py --battles 10 --model microsoft/DialoGPT-medium --temperature 0.7
```

### 3. 智能体性能评测与对比

```bash
# 单智能体评测
python main.py --mode evaluate --agent-type rl --battles 50

# 多智能体对比与可视化
python scripts/evaluate.py --mode compare --agent-type rl --battles 30 --generate-plots
```

### 4. Showdown 平台在线对战

详见 [docs/SHOWDOWN_GUIDE.md](docs/SHOWDOWN_GUIDE.md)

```bash
# 运行Showdown对战（需配置Showdown账号）
python scripts/run_showdown.py --agent-type llm --battles 5 --config config/showdown_config.json

# Showdown演示脚本
python scripts/showdown_demo.py
```

### 5. 功能演示与测试

```bash
# 主要功能演示（本地）
python demo.py

# 运行单元测试
pytest tests/
```

---

## 配置文件说明

- `config/example_config.json`：本地训练/对战参数示例
- `config/showdown_config.json`：Showdown平台参数示例

主要参数包括：
- `battle_format`：对战格式（如 gen8randombattle）
- `agents`：各类智能体参数（如学习率、模型名、温度等）
- `training`：训练相关参数（回合数、epsilon等）
- `logging`：日志与保存路径

---

## 主要API与扩展说明

### 1. 自定义智能体

继承 `agents/base_agent.py` 的 `BaseAgent`，实现 `choose_move` 方法即可：

```python
from agents.base_agent import BaseAgent

class MyAgent(BaseAgent):
    def choose_move(self, battle):
        # 实现自定义决策逻辑
        return self.choose_random_move(battle)
```

### 2. 强化学习智能体（RLAgent）

```python
from agents.rl_agent import RLAgent
agent = RLAgent(learning_rate=0.001, epsilon=0.1)
agent.save_model("model.pth")
agent.load_model("model.pth")
```

### 3. 大语言模型智能体（LLMAgent）

```python
from agents.llm_agent import LLMAgent
agent = LLMAgent(model_name="microsoft/DialoGPT-medium", temperature=0.7)
agent.set_temperature(0.5)
```

### 4. Showdown 智能体与管理器

```python
from agents.showdown_llm_agent import ShowdownLLMAgent
agent = ShowdownLLMAgent(username="mybot", model_name="microsoft/DialoGPT-medium")

from env.showdown_manager import ShowdownManager
async with ShowdownManager("config/showdown_config.json") as manager:
    await manager.run_showdown_battles(agent, num_battles=5)
```

### 5. 对战管理与评测

```python
from env.battle_manager import BattleManager
manager = BattleManager(battle_format="gen8randombattle")
result = await manager.run_battle(agent1, agent2)

from scripts.evaluate import AgentEvaluator
evaluator = AgentEvaluator()
await evaluator.evaluate_agent(agent, [opponent], num_battles=20)
```

---

## 依赖列表（requirements.txt）

- poke-env
- torch
- transformers
- stable-baselines3
- numpy
- pytest
- gym>=0.26.0
- matplotlib
- pandas
- asyncio

---

## 日志与模型存储

- `logs/`：训练与运行日志
- `battle_logs/`：对战记录
- `evaluation_logs/`：评测结果
- `models/`：模型保存目录

---

## 文档与扩展

- [docs/SHOWDOWN_GUIDE.md](docs/SHOWDOWN_GUIDE.md)：Showdown平台接入与账号配置指南
- 代码注释与类型提示齐全，便于二次开发

---

## 常见问题与故障排查

1. **poke-env 连接失败**：请检查网络与 Showdown 服务器状态。
2. **模型加载失败**：确认模型路径与格式正确。
3. **内存不足**：可适当降低 batch_size 或 memory_size。
4. **Showdown 账号问题**：详见文档配置说明。

---

## 贡献与开发

1. Fork 本项目，创建功能分支
2. 提交更改并补充测试
3. 创建 Pull Request

---

## 许可证

本项目采用 MIT 许可证，欢迎学术与商业用途。

---

## 致谢

- [poke-env](https://github.com/hsahovic/poke-env)：宝可梦对战环境
- [PyTorch](https://pytorch.org/)：深度学习框架
- [Transformers](https://huggingface.co/transformers/)：大语言模型库
