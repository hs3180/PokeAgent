# Installation Guide

## Quick Start

### Option 1: Using pip (recommended)
```bash
# Install the package
pip install .

# Or in development mode
pip install -e .

# Run the application
pokeagent ladder --battles 1
```

### Option 2: Using conda
```bash
# Activate your conda environment
conda activate pokeagent

# Install dependencies
pip install poke-env torch "transformers==2.1.1" numpy python-dotenv

# Run the application
python -m pokeagent ladder --battles 1
```

### Option 3: Direct from source
```bash
# Set up environment variables
export POKEAGENT_USERNAME=your_username
export POKEAGENT_SERVER_URL=play.pokemonshowdown.com
export POKEAGENT_PASSWORD=your_password  # Optional

# Run directly
python -m pokeagent ladder --battles 1
```

## Configuration

1. Copy `.env.example` to `.env`
2. Edit `.env` with your credentials
3. The application will automatically load the `.env` file

## Usage Examples

```bash
# Run ladder battles
pokeagent ladder --battles 5

# Challenge specific opponent
pokeagent challenge --opponent username

# Different battle format
pokeagent ladder --format gen2ou --battles 3

# Get help
pokeagent --help
```