#!/usr/bin/env python3
"""
Simplified Gen1 OU battle client
Supports ladder battles and challenging specific opponents
"""

import asyncio
import logging
import sys
import time
import os
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from agents.showdown_agent import ShowdownAgent
from agents.llm_agent import LLMAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_single_gen1ou_battle(num_battles=1):
    """
    Connect to ladder for multiple Gen1OU battles
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
    
    # Gen1 OU Team - User's competitive team
    gen1ou_team = """
Starmie
Ability: Illuminate
Bashful Nature
- Recover
- Psychic
- Thunderbolt
- Blizzard

Chansey
Ability: Natural Cure
- Soft-Boiled
- Thunder Wave
- Ice Beam
- Seismic Toss

Rhydon
Ability: Lightning Rod
- Rock Slide
- Earthquake
- Substitute
- Body Slam

Snorlax
Ability: Immunity
- Body Slam
- Surf
- Hyper Beam
- Self-Destruct

Tauros
Ability: Intimidate
- Body Slam
- Hyper Beam
- Blizzard
- Earthquake

Exeggutor
Ability: Chlorophyll
- Sleep Powder
- Stun Spore
- Explosion
- Psychic
"""
    
    # Create Showdown Agent using environment variables with team
    agent = ShowdownAgent(
        battle_format="gen1ou",
        team=gen1ou_team
    )
    
    try:
        # Connect to server
        logger.info("Connecting to Showdown server...")
        await agent.connect()
        logger.info(f"Connected, username: {agent.username}")
        logger.info("Battle format: Gen1 OU")
        
        # Join ladder for multiple battles
        logger.info(f"Joining Gen1 OU ladder for {num_battles} battles...")
        battles_completed = 0
        
        while battles_completed < num_battles:
            # Join ladder and wait for opponent
            await agent.join_ladder("gen1ou")
            
            logger.info("Waiting for opponent...")
            start_time = time.time()
            while not agent.battles and (time.time() - start_time) < 120:
                await asyncio.sleep(1)
            
            if not agent.battles:
                logger.error("No opponent found within 120 seconds")
                break
            
            # Conduct battle
            logger.info(f"Battle {battles_completed + 1} started!")
            battle_id = list(agent.battles.keys())[0]
            battle = agent.battles[battle_id]
            
            await battle.wait_until_finished()
            
            # Show result
            result = "Victory" if battle.won else "Defeat"
            logger.info(f"Battle {battles_completed + 1} finished: {result}")
            
            battles_completed += 1
            
            # Short break between battles
            if battles_completed < num_battles:
                logger.info("Taking a short break before next battle...")
                await asyncio.sleep(3)
        
        # Get final statistics
        stats = agent.get_battle_stats()
        logger.info(f"=== Final Stats ===")
        logger.info(f"Battles completed: {battles_completed}")
        logger.info(f"Wins: {stats['wins']}")
        logger.info(f"Losses: {stats['losses']}")
        
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


async def challenge_opponent(opponent_username, battle_format="gen1ou"):
    """
    Challenge a specific opponent
    """
    logger.info(f"=== Challenging {opponent_username} ===")
    logger.info(f"Battle format: {battle_format}")
    
    # Gen1 OU Team - User's competitive team
    gen1ou_team = """
Starmie
Ability: Illuminate
Bashful Nature
- Recover
- Psychic
- Thunderbolt
- Blizzard

Chansey
Ability: Natural Cure
- Soft-Boiled
- Thunder Wave
- Ice Beam
- Seismic Toss

Rhydon
Ability: Lightning Rod
- Rock Slide
- Earthquake
- Substitute
- Body Slam

Snorlax
Ability: Immunity
- Body Slam
- Surf
- Hyper Beam
- Self-Destruct

Tauros
Ability: Intimidate
- Body Slam
- Hyper Beam
- Blizzard
- Earthquake

Exeggutor
Ability: Chlorophyll
- Sleep Powder
- Stun Spore
- Explosion
- Psychic
"""
    
    agent = ShowdownAgent(battle_format=battle_format, team=gen1ou_team)
    
    try:
        # Connect to server
        logger.info("Connecting to Showdown server...")
        await agent.connect()
        logger.info(f"Connected as {agent.username}")
        
        # Challenge the opponent
        logger.info(f"Challenging {opponent_username}...")
        await agent.challenge_user(opponent_username, battle_format)
        
        # Wait for battle to start
        start_time = time.time()
        while not agent.battles and (time.time() - start_time) < 30:
            await asyncio.sleep(1)
        
        if not agent.battles:
            logger.error(f"Failed to start battle with {opponent_username}")
            return
        
        # Conduct battle
        logger.info("Battle started!")
        battle_id = list(agent.battles.keys())[0]
        battle = agent.battles[battle_id]
        
        await battle.wait_until_finished()
        
        # Show result
        result = "Victory" if battle.won else "Defeat"
        logger.info(f"Battle finished: {result}")
        
    except Exception as e:
        logger.error(f"Challenge error: {e}")
    finally:
        await agent.disconnect()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Pokemon Showdown Battle Client')
    parser.add_argument('--mode', choices=['ladder', 'challenge'], 
                       default='ladder', help='Battle mode')
    parser.add_argument('--opponent', type=str, 
                       help='Username to challenge (required for challenge mode)')
    parser.add_argument('--format', type=str, default='gen1ou',
                       help='Battle format (default: gen1ou)')
    parser.add_argument('--battles', type=int, default=1,
                       help='Number of battles to run (default: 1)')
    
    args = parser.parse_args()
    
    if args.mode == 'ladder':
        asyncio.run(run_single_gen1ou_battle(args.battles))
    elif args.mode == 'challenge':
        if not args.opponent:
            logger.error("Opponent username is required for challenge mode")
            logger.error("Usage: python simple_gen1ou_client.py --mode challenge --opponent <username>")
            sys.exit(1)
        asyncio.run(challenge_opponent(args.opponent, args.format))