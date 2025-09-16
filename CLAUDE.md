# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick Start

### Environment Setup
```bash
# Create and activate virtual environment
source metamon_venv/bin/activate

# Install dependencies
pip install -e .
```

### Running the Application
```bash
# Run ladder battles
pokeagent ladder --battles 1

# Challenge specific opponent
pokeagent challenge --opponent username

# Get help
pokeagent --help
```

## Configuration

### Environment Variables

Required:
- `POKEAGENT_USERNAME`: Pokemon Showdown username
- `POKEAGENT_WEBSOCKET_URL`: WebSocket URL (e.g., `wss://play.pokemonshowdown.com/showdown/websocket`)
- `POKEAGENT_AUTH_URL`: Authentication URL (auto-generated if not provided)

Optional:
- `POKEAGENT_PASSWORD`: Password for registered accounts
- `POKEAGENT_BATTLE_FORMAT`: Battle format (default: `gen1ou`)
- `POKEAGENT_LOG_LEVEL`: Log level (DEBUG, INFO, WARNING, ERROR)

### Using .env Files
1. Copy example: `cp .env.example .env`
2. Edit with your credentials
3. Run application - automatically loads `.env`

## Development

### Code Quality
```bash
source metamon_venv/bin/activate

# Run tests
pytest --cov=pokeagent

# Format and lint code
ruff check pokeagent/
ruff format pokeagent/

# Type checking
pyright pokeagent/

# Run all checks
pytest && ruff check pokeagent/ && ruff format pokeagent/ && pyright pokeagent/
```

## Architecture

### Core Components

#### Agent System
- `BaseAgent`: Abstract base class
- `LLMAgent`: Uses transformers models
- `RandomMoveAgent`: Random move selection
- `HighestDamageAgent`: Damage optimization
- `MetamonPretrainAgent`: Pretrained models from HuggingFace

#### Client Architecture
- `ShowdownClient`: Server connection management
- Separates agent logic from network communication
- Handles authentication and battle statistics

### Key Implementation Details

#### Transformers Compatibility
- Uses transformers 2.1.1
- Use `AutoModelWithLMHead` instead of `AutoModelForCausalLM`
- Handle model loading failures gracefully

#### Connection Management
- `AccountConfiguration` for credentials
- `ServerConfiguration` with websocket_url and authentication_url
- Support for registered and guest accounts

#### Async Pattern
- Built on asyncio throughout
- All battle operations are async
- Proper connection lifecycle management

#### Agent Interface
All agents implement `choose_move(battle)` returning:
- Move orders via `self.create_order(move)`
- Switch orders via `self.create_order(pokemon)`

### File Structure
- `pokeagent/`: Main package
- `pokeagent/agents/`: Agent implementations
- `pokeagent/client/`: Network layer
- `pokeagent/config/`: Configuration files
- `pokeagent/cli.py`: CLI entry point
- `pyproject.toml`: Project configuration

### Common Patterns
- Agents inherit from `BaseAgent`
- Client handles connections, agents handle logic
- Configuration from JSON and environment variables
- Comprehensive logging and type hints
- Async context managers for resources