# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the Application
```bash
# Install the package
pip install .

# Or in development mode
pip install -e .

# Run Gen1 OU ladder battles
pokeagent ladder --battles 1

# Challenge a specific opponent
pokeagent challenge --opponent username

# For help
pokeagent --help
```

### Environment Configuration

The application supports authentication and configuration through environment variables. You can set these directly or use a `.env` file.

#### Required Environment Variables
- `POKEAGENT_USERNAME`: Your Pokemon Showdown username
- `POKEAGENT_WEBSOCKET_URL`: Complete WebSocket URL (e.g., `wss://play.pokemonshowdown.com/showdown/websocket`)
- `POKEAGENT_AUTH_URL`: Authentication URL (optional, auto-generated from websocket_url if not provided)

#### Optional Environment Variables
- `POKEAGENT_PASSWORD`: Your Pokemon Showdown password (for registered accounts)
- `POKEAGENT_BATTLE_FORMAT`: Battle format (default: `gen1ou`)
- `POKEAGENT_LOG_LEVEL`: Log level (DEBUG, INFO, WARNING, ERROR)

#### Using .env Files
1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
2. Edit `.env` with your credentials:
   ```
   POKEAGENT_USERNAME=your_username
   POKEAGENT_PASSWORD=your_password
   POKEAGENT_WEBSOCKET_URL=wss://play.pokemonshowdown.com/showdown/websocket
   POKEAGENT_AUTH_URL=https://play.pokemonshowdown.com/action.php?
   ```
3. Run the application - it will automatically load the `.env` file

#### Setting Environment Variables Directly
```bash
export POKEAGENT_USERNAME=your_username
export POKEAGENT_WEBSOCKET_URL=wss://play.pokemonshowdown.com/showdown/websocket
export POKEAGENT_AUTH_URL=https://play.pokemonshowdown.com/action.php?
export POKEAGENT_PASSWORD=your_password
pokeagent ladder --battles 1
```

### Code Quality and Testing
```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov=pokeagent

# Format code
black pokeagent/

# Sort imports
isort pokeagent/

# Lint code
flake8 pokeagent/

# Type checking
mypy pokeagent/

# Run all quality checks
pytest && black pokeagent/ && isort pokeagent/ && flake8 pokeagent/ && mypy pokeagent/
```

## Architecture Overview

### Core Architecture
This is a simplified Pokemon Showdown client specifically designed for Gen1 OU (Generation 1 OverUsed) format battles. The project connects to the official Pokemon Showdown server and uses LLM-based agents for battle decisions.

### Key Components

#### Agent Hierarchy
- `BaseAgent` (`agents/base_agent.py`): Abstract base class extending poke-env's Player
- `LLMAgent` (`agents/llm_agent.py`): Transformers integration for language model decisions
- `ShowdownAgent` (`agents/showdown_agent.py`): Base class for online battles

#### Configuration System
- JSON-based configuration in `config/showdown_config.json`
- Configured for official Pokemon Showdown server: `play.pokemonshowdown.com:443`
- Battle format: `gen1ou`

### Important Implementation Details

#### Transformers Version Compatibility
The codebase uses transformers 2.1.1, which requires:
- Use `AutoModelWithLMHead` instead of `AutoModelForCausalLM`
- Import from `transformers` module

#### Showdown Connection Architecture
Showdown agents use proper configuration objects:
- `AccountConfiguration` for credentials
- `ServerConfiguration` with websocket_url and authentication_url
- Current official server: `play.pokemonshowdown.com:443`

#### Async/Await Pattern
The entire codebase is built on asyncio:
- All battle operations are async
- Use `await` for battle methods
- Main entry points use `asyncio.run()`

#### Agent Decision Making
All agents must implement `choose_move(battle)` method that returns:
- Move orders via `self.create_order(move)`
- Switch orders via `self.create_order(pokemon)`

### File Structure Conventions
- `pokeagent/`: Main package directory
- `pokeagent/agents/`: Agent implementations
- `pokeagent/config/`: JSON configuration files
- `pokeagent/cli.py`: CLI entry point
- `pyproject.toml`: Project configuration and dependencies
- `setup.py`: Installation script

### Common Patterns
- Agents inherit from `BaseAgent` and implement `choose_move()`
- Configuration loaded from JSON files
- Async context managers for resource management
- Comprehensive logging throughout
- Type hints used extensively

### Gen1 OU Specifics
- Optimized for Generation 1 OverUsed format
- Connects to official Pokemon Showdown ladder
- Uses LLM for battle decision making
- Automatic opponent search and battle execution