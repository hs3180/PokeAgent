#!/usr/bin/env python3
"""
Simplified Gen1 OU ladder battle client
Connects to ladder for a single Gen1OU battle
"""

import asyncio
import logging
import sys
import time
import os
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from agents.showdown_agent import ShowdownAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_single_gen1ou_battle():
    """
    Connect to ladder for a single Gen1OU battle
    """
    logger.info("=== Gen1 OU Ladder Battle ===")
    
    # Load .env file if it exists
    env_file = Path(__file__).parent / '.env'
    if env_file.exists():
        logger.info(f"Loading environment variables from {env_file}")
        load_dotenv(env_file)
    else:
        # Try to load from current directory
        load_dotenv()
    
    # Check for required environment variables
    missing_vars = []
    if not os.environ.get('POKEAGENT_USERNAME'):
        missing_vars.append('POKEAGENT_USERNAME')
    if not os.environ.get('POKEAGENT_SERVER_URL'):
        missing_vars.append('POKEAGENT_SERVER_URL')
    if not os.environ.get('POKEAGENT_SERVER_PORT'):
        missing_vars.append('POKEAGENT_SERVER_PORT')
    
    if missing_vars:
        logger.error("Missing required environment variables:")
        for var in missing_vars:
            logger.error(f"  - {var}")
        logger.error("\nPlease set these environment variables:")
        logger.error("  export POKEAGENT_USERNAME=your_username")
        logger.error("  export POKEAGENT_SERVER_URL=play.pokemonshowdown.com")
        logger.error("  export POKEAGENT_SERVER_PORT=443")
        logger.error("  export POKEAGENT_PASSWORD=your_password  # Optional")
        return
    
    # Create Showdown Agent using environment variables
    agent = ShowdownAgent(
        battle_format="gen1ou"
    )
    
    try:
        # Connect to server
        logger.info("Connecting to Showdown server...")
        await agent.connect()
        logger.info(f"Connected, username: {agent.username}")
        logger.info("Battle format: Gen1 OU")
        
        # Join ladder
        logger.info("Joining Gen1 OU ladder...")
        await agent.join_ladder("gen1ou")
        
        # Wait for battle to start
        logger.info("Waiting for opponent...")
        start_time = time.time()
        while not agent.battles and (time.time() - start_time) < 120:
            await asyncio.sleep(1)
        
        if not agent.battles:
            logger.error("No opponent found within 120 seconds")
            return
        
        # Conduct battle
        logger.info("Battle started!")
        battle_id = list(agent.battles.keys())[0]
        battle = agent.battles[battle_id]
        
        await battle.wait_until_finished()
        
        # Show result
        result = "Victory" if battle.won else "Defeat"
        logger.info(f"Battle finished: {result}")
        
        # Get statistics
        stats = agent.get_battle_stats()
        logger.info(f"Stats - Wins: {stats['wins']}, Losses: {stats['losses']}")
        
    except Exception as e:
        logger.error(f"Battle error: {e}")
    finally:
        # Leave ladder and disconnect
        try:
            await agent.leave_ladder()
        except:
            pass
        try:
            await agent.disconnect()
        except:
            pass
        logger.info("=== Battle ended ===")

if __name__ == "__main__":
    # Run single Gen1OU ladder battle
    asyncio.run(run_single_gen1ou_battle())