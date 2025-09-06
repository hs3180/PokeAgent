# Gen1 OU Pokemon Showdown Agent

本项目是一个简化的 Pokemon Showdown 客户端，专门用于 Gen1 OU (Generation 1 OverUsed) 格式的在线对战。项目基于 [poke-env](https://github.com/hsahovic/poke-env) 构建，支持连接到官方 Pokemon Showdown 服务器进行自动对战。

---

## 目录结构

```
├── agents/                  # 智能体实现
│   ├── base_agent.py        # 基础智能体类
│   ├── llm_agent.py         # 大语言模型智能体
│   ├── showdown_agent.py    # Showdown 连接与对战
│   └── __init__.py
├── config/                  # 配置文件
│   └── showdown_config.json # Showdown 服务器配置
├── simple_gen1ou_client.py  # Gen1 OU 对战客户端
├── requirements.txt         # 依赖列表
└── README.md                # 项目说明文档
```

---

## 功能特点

- **专门针对 Gen1 OU**：优化用于第一代宝可梦 OU 格式对战
- **Showdown 在线对战**：连接到官方 Pokemon Showdown 服务器
- **LLM 智能体**：使用大语言模型进行对战决策
- **简化配置**：最小化配置，专注于核心功能
- **自动对战**：自动搜索对手并进行对战

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

### 运行 Gen1 OU 对战

```bash
# 运行单场 Gen1 OU 对战
python simple_gen1ou_client.py
```

### 配置文件

编辑 `config/showdown_config.json` 来自定义设置：

```json
{
  "showdown": {
    "server": {
      "url": "play.pokemonshowdown.com",
      "port": 443,
      "secure": true
    },
    "credentials": {
      "username": "Gen1OU_Player",
      "password": null
    },
    "battle_format": "gen1ou",
    "log_level": "INFO"
  },
  "llm_agent": {
    "model_name": "microsoft/DialoGPT-medium",
    "temperature": 0.7,
    "max_length": 100
  }
}
```

---

## 使用说明

### 工作流程

1. **连接服务器**：自动连接到 Pokemon Showdown 官方服务器
2. **搜索对战**：加入 Gen1 OU 天梯并搜索对手
3. **自动对战**：使用 LLM 智能体进行对战决策
4. **显示结果**：输出对战结果和统计信息

### LLM 智能体

项目使用 Hugging Face Transformers 中的大语言模型进行对战决策：

- 默认模型：`microsoft/DialoGPT-medium`
- 可调节参数：温度、生成长度
- 支持自定义模型替换

### 服务器配置

- **官方服务器**：`play.pokemonshowdown.com:443`
- **对战格式**：`gen1ou` (第一代 OU)
- **认证方式**：用户名 + 密码（可选）

---

## 注意事项

### 兼容性说明

- 使用 Transformers 2.1.1 版本，需要 `AutoModelWithLMHead` 而非 `AutoModelForCausalLM`
- Python 3.8+ 兼容
- 仅支持 Pokemon Showdown 官方服务器

### 使用限制

- 请遵守 Pokemon Showdown 的服务条款
- 避免过于频繁的请求
- 使用合理的用户名

### 故障排除

1. **连接失败**：检查网络连接和服务器状态
2. **模型加载失败**：确认模型路径和网络连接
3. **对战无法开始**：等待更长时间或检查服务器状态

---

## 依赖列表（requirements.txt）

- poke-env
- torch
- transformers
- numpy

---

## 致谢

- [poke-env](https://github.com/hsahovic/poke-env)：宝可梦对战环境
- [PyTorch](https://pytorch.org/)：深度学习框架
- [Transformers](https://huggingface.co/transformers/)：大语言模型库
