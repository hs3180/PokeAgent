"""
Command Line Interface for PokeAgent
"""

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

from .agents.showdown_agent import ShowdownAgent

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_environment_variables():
    """Load environment variables from .env file"""
    env_file = Path.cwd() / '.env'
    if env_file.exists():
        logger.info(f"Loading environment variables from {env_file}")
        load_dotenv(env_file)
    else:
        load_dotenv()


def validate_environment_variables() -> bool:
    """Validate required environment variables are set"""
    required_vars = ['POKEAGENT_USERNAME', 'POKEAGENT_SERVER_URL']
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        logger.error("Missing required environment variables:")
        for var in missing_vars:
            logger.error(f"  - {var}")
        logger.error("\nPlease set these environment variables:")
        logger.error("  export POKEAGENT_USERNAME=your_username")
        logger.error("  export POKEAGENT_SERVER_URL=play.pokemonshowdown.com")
        logger.error("  export POKEAGENT_PASSWORD=your_password  # Optional")
        return False
    
    return True


def get_default_team() -> str:
    """Get the default Gen1 OU team"""
    return """
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


async def run_ladder_battles(num_battles: int = 1, battle_format: str = "gen1ou") -> None:
    """Run ladder battles"""
    logger.info(f"=== {battle_format.upper()} Ladder Battle ===")
    
    if not validate_environment_variables():
        return
    
    agent = ShowdownAgent(
        battle_format=battle_format,
        team=get_default_team(),
        username=os.environ.get('POKEAGENT_USERNAME'),
        password=os.environ.get('POKEAGENT_PASSWORD'),
        server_url=os.environ.get('POKEAGENT_SERVER_URL'),
        server_port=int(os.environ.get('POKEAGENT_SERVER_PORT', 443))
    )
    
    try:
        await agent.connect()
        logger.info(f"Connected as {agent.username}")
        logger.info(f"Battle format: {battle_format}")
        
        battles_completed = 0
        while battles_completed < num_battles:
            logger.info(f"Joining {battle_format} ladder for battle {battles_completed + 1}...")
            await agent.join_ladder(battle_format)
            
            # Wait for opponent
            start_time = asyncio.get_event_loop().time()
            while not agent.battles and (asyncio.get_event_loop().time() - start_time) < 120:
                await asyncio.sleep(1)
            
            if not agent.battles:
                logger.error("No opponent found within 120 seconds")
                break
            
            # Conduct battle
            battle_id = list(agent.battles.keys())[0]
            battle = agent.battles[battle_id]
            
            logger.info(f"Battle {battles_completed + 1} started!")
            await battle.wait_until_finished()
            
            result = "Victory" if battle.won else "Defeat"
            logger.info(f"Battle {battles_completed + 1} finished: {result}")
            
            battles_completed += 1
            
            if battles_completed < num_battles:
                await asyncio.sleep(3)
        
        # Show final stats
        stats = agent.get_battle_stats()
        logger.info("=== Final Stats ===")
        logger.info(f"Battles completed: {battles_completed}")
        logger.info(f"Wins: {stats['wins']}")
        logger.info(f"Losses: {stats['losses']}")
        
    except Exception as e:
        logger.error(f"Battle error: {e}")
    finally:
        try:
            await agent.leave_ladder()
        except:
            pass
        try:
            await agent.disconnect()
        except:
            pass
        logger.info("=== Battle ended ===")


async def challenge_opponent(opponent_username: str, battle_format: str = "gen1ou") -> None:
    """Challenge a specific opponent"""
    logger.info(f"=== Challenging {opponent_username} ===")
    logger.info(f"Battle format: {battle_format}")
    
    if not validate_environment_variables():
        return
    
    agent = ShowdownAgent(
        battle_format=battle_format,
        team=get_default_team(),
        username=os.environ.get('POKEAGENT_USERNAME'),
        password=os.environ.get('POKEAGENT_PASSWORD'),
        server_url=os.environ.get('POKEAGENT_SERVER_URL'),
        server_port=int(os.environ.get('POKEAGENT_SERVER_PORT', 443))
    )
    
    try:
        await agent.connect()
        logger.info(f"Connected as {agent.username}")
        
        logger.info(f"Challenging {opponent_username}...")
        await agent.challenge_user(opponent_username, battle_format)
        
        # Wait for battle to start
        start_time = asyncio.get_event_loop().time()
        while not agent.battles and (asyncio.get_event_loop().time() - start_time) < 30:
            await asyncio.sleep(1)
        
        if not agent.battles:
            logger.error(f"Failed to start battle with {opponent_username}")
            return
        
        # Conduct battle
        battle_id = list(agent.battles.keys())[0]
        battle = agent.battles[battle_id]
        
        logger.info("Battle started!")
        await battle.wait_until_finished()
        
        result = "Victory" if battle.won else "Defeat"
        logger.info(f"Battle finished: {result}")
        
    except Exception as e:
        logger.error(f"Challenge error: {e}")
    finally:
        await agent.disconnect()


def create_parser() -> argparse.ArgumentParser:
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(
        description='PokeAgent - Pokemon Showdown Battle Client',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  pokeagent ladder --battles 5
  pokeagent challenge --opponent username
  pokeagent ladder --format gen2ou --battles 3
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Ladder command
    ladder_parser = subparsers.add_parser('ladder', help='Run ladder battles')
    ladder_parser.add_argument(
        '--battles', '-b', type=int, default=1,
        help='Number of battles to run (default: 1)'
    )
    ladder_parser.add_argument(
        '--format', '-f', type=str, default='gen1ou',
        help='Battle format (default: gen1ou)'
    )
    
    # Challenge command
    challenge_parser = subparsers.add_parser('challenge', help='Challenge a specific opponent')
    challenge_parser.add_argument(
        'opponent', type=str,
        help='Username to challenge'
    )
    challenge_parser.add_argument(
        '--format', '-f', type=str, default='gen1ou',
        help='Battle format (default: gen1ou)'
    )
    
    return parser


def main() -> None:
    """Main entry point"""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    load_environment_variables()
    
    if args.command == 'ladder':
        asyncio.run(run_ladder_battles(args.battles, args.format))
    elif args.command == 'challenge':
        asyncio.run(challenge_opponent(args.opponent, args.format))


if __name__ == "__main__":
    main()