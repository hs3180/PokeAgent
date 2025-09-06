# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the Application
```bash
# Run Gen1 OU battle client
python simple_gen1ou_client.py

# Installation
pip install -r requirements.txt
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
- `agents/`: Agent implementations
- `config/`: JSON configuration files
- `simple_gen1ou_client.py`: Main client application

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