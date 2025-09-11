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
This is a Pokemon Showdown client designed for automated battles using AI agents. The project connects to the official Pokemon Showdown server and supports multiple agent types for battle decision-making.

### Key Components

#### Agent System
- `BaseAgent` (`agents/base_agent.py`): Abstract base class providing common functionality
- `LLMAgent` (`agents/llm_agent.py`): Uses transformers models for battle decisions
- `RandomMoveAgent` (`agents/random_agent.py`): Makes random move choices
- `HighestDamageAgent` (`agents/highest_damage_agent.py`): Calculates optimal damage output

#### Client Architecture
- `ShowdownClient` (`client/showdown_client.py`): Manages server connections and battle coordination
- Separates agent logic from network communication
- Handles authentication, connection management, and battle statistics

#### Configuration System
- JSON configuration in `config/showdown_config.json`
- Environment variable support via `.env` files
- Default team configuration for Gen1 OU format

### Important Implementation Details

#### Transformers Version Compatibility
The codebase uses transformers 2.1.1, which requires:
- Use `AutoModelWithLMHead` instead of `AutoModelForCausalLM`
- Import from `transformers` module
- Handle model loading failures gracefully

#### Connection Management
Showdown connections use proper configuration objects:
- `AccountConfiguration` for credentials
- `ServerConfiguration` with websocket_url and authentication_url
- Automatic auth_url generation from websocket_url
- Support for both registered and guest accounts

#### Async/Await Pattern
The entire codebase is built on asyncio:
- All battle operations are async
- Use `await` for battle methods
- Main entry points use `asyncio.run()`
- Proper connection lifecycle management

#### Agent Decision Making
All agents must implement `choose_move(battle)` method that returns:
- Move orders via `self.create_order(move)`
- Switch orders via `self.create_order(pokemon)`
- Must handle battle state analysis and action selection

### File Structure Conventions
- `pokeagent/`: Main package directory
- `pokeagent/agents/`: Agent implementations
- `pokeagent/client/`: Network communication layer
- `pokeagent/config/`: JSON configuration files
- `pokeagent/cli.py`: CLI entry point with argument parsing
- `pyproject.toml`: Project configuration and dependencies

### Common Patterns
- Agents inherit from `BaseAgent` and implement `choose_move()`
- Client handles connection management, agents handle battle logic
- Configuration loaded from both JSON and environment variables
- Async context managers for resource management
- Comprehensive logging throughout
- Type hints used extensively

### Agent Types and Usage

#### Random Agent
- Simple random move selection
- Useful for testing and baseline comparison
- Fallback when other agents fail

#### Highest Damage Agent
- Calculates expected damage for each move
- Considers type effectiveness, STAB, priority
- Implements switch logic based on HP and type advantages

#### LLM Agent
- Uses transformer models for decision making
- Supports configurable model parameters
- Includes system prompts for battle context
- Falls back to random strategy if model fails

### Battle Flow
1. CLI parses arguments and creates appropriate agent
2. ShowdownClient handles server connection
3. Agent receives battle state and makes decisions
4. Client coordinates battle execution and statistics
5. Proper cleanup and disconnection on completion