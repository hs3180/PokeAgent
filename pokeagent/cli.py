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

from .agents.highest_damage_agent import HighestDamageAgent
from .agents.llm_agent import LLMAgent
from .agents.random_agent import RandomMoveAgent
from .client.showdown_client import ShowdownClient

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_agent(agent_type: str, battle_format: str):
    """Create agent based on type"""
    agent_type = agent_type.lower()

    if agent_type == "random":
        return RandomMoveAgent(battle_format=battle_format)
    elif agent_type == "highest_damage":
        return HighestDamageAgent(battle_format=battle_format)
    elif agent_type == "llm":
        return LLMAgent(battle_format=battle_format)
    else:
        logger.warning(f"Unknown agent type: {agent_type}, using random")
        return RandomMoveAgent(battle_format=battle_format)


def load_environment_variables():
    """Load environment variables from .env file"""
    env_file = Path.cwd() / ".env"
    if env_file.exists():
        logger.info(f"Loading environment variables from {env_file}")
        load_dotenv(env_file)
    else:
        load_dotenv()


def validate_environment_variables() -> bool:
    """Validate required environment variables are set"""
    required_vars = ["POKEAGENT_USERNAME", "POKEAGENT_WEBSOCKET_URL"]
    missing_vars = [var for var in required_vars if not os.environ.get(var)]

    if missing_vars:
        logger.error("Missing required environment variables:")
        for var in missing_vars:
            logger.error(f"  - {var}")
        logger.error("\nPlease set these environment variables:")
        logger.error("  export POKEAGENT_USERNAME=your_username")
        logger.error(
            "  export POKEAGENT_WEBSOCKET_URL=wss://play.pokemonshowdown.com/showdown/websocket"
        )
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


async def run_ladder_battles(
    num_battles: int = 1, battle_format: str = "gen1ou", agent_type: str = "random"
) -> None:
    """Run ladder battles"""
    logger.info(f"=== {battle_format.upper()} Ladder Battle ===")
    logger.info(f"Agent type: {agent_type}")

    if not validate_environment_variables():
        return

    # Create agent based on type
    agent = create_agent(agent_type, battle_format)

    # Create client and set agent
    client = ShowdownClient(
        battle_format=battle_format,
        team=get_default_team(),
        username=os.environ.get("POKEAGENT_USERNAME"),
        password=os.environ.get("POKEAGENT_PASSWORD"),
        websocket_url=os.environ.get("POKEAGENT_WEBSOCKET_URL"),
        auth_url=os.environ.get("POKEAGENT_AUTH_URL"),
    )
    client.set_agent(agent)

    try:
        await client.connect()
        logger.info(f"Connected as {client.username}")
        logger.info(f"Battle format: {battle_format}")
        logger.info(f"Starting {num_battles} ladder battles...")

        # Use the proper ladder API
        await client.ladder(battle_format, num_battles)

        # Show final stats
        stats = client.get_battle_stats()
        logger.info("=== Final Stats ===")
        logger.info(f"Battles completed: {stats['total_battles']}")
        logger.info(f"Wins: {stats['wins']}")
        logger.info(f"Losses: {stats['losses']}")

    except Exception as e:
        logger.error(f"Battle error: {e}")
    finally:
        try:
            await client.disconnect()
        except:
            pass
        logger.info("=== Battle ended ===")


async def challenge_opponent(
    opponent_username: str, battle_format: str = "gen1ou", agent_type: str = "random"
) -> None:
    """Challenge a specific opponent"""
    logger.info(f"=== Challenging {opponent_username} ===")
    logger.info(f"Battle format: {battle_format}")
    logger.info(f"Agent type: {agent_type}")

    if not validate_environment_variables():
        return

    # Create agent based on type
    agent = create_agent(agent_type, battle_format)

    # Create client and set agent
    client = ShowdownClient(
        battle_format=battle_format,
        team=get_default_team(),
        username=os.environ.get("POKEAGENT_USERNAME"),
        password=os.environ.get("POKEAGENT_PASSWORD"),
        websocket_url=os.environ.get("POKEAGENT_WEBSOCKET_URL"),
        auth_url=os.environ.get("POKEAGENT_AUTH_URL"),
    )
    client.set_agent(agent)

    try:
        await client.connect()
        logger.info(f"Connected as {client.username}")

        logger.info(f"Challenging {opponent_username}...")
        await client.challenge_user(opponent_username, battle_format)

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

        # Wait for battle to finish
        while not battle.finished:
            await asyncio.sleep(1)

        result = "Victory" if battle.won else "Defeat"
        logger.info(f"Battle finished: {result}")

    except Exception as e:
        logger.error(f"Challenge error: {e}")
    finally:
        await client.disconnect()


def create_parser() -> argparse.ArgumentParser:
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(
        description="PokeAgent - Pokemon Showdown Battle Client",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  pokeagent ladder --battles 5
  pokeagent ladder --battles 3 --agent highest_damage
  pokeagent challenge --opponent username --agent llm
  pokeagent ladder --format gen2ou --battles 3 --agent random
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Ladder command
    ladder_parser = subparsers.add_parser("ladder", help="Run ladder battles")
    ladder_parser.add_argument(
        "--battles",
        "-b",
        type=int,
        default=1,
        help="Number of battles to run (default: 1)",
    )
    ladder_parser.add_argument(
        "--format",
        "-f",
        type=str,
        default="gen1ou",
        help="Battle format (default: gen1ou)",
    )
    ladder_parser.add_argument(
        "--agent",
        "-a",
        type=str,
        default="random",
        choices=["random", "highest_damage", "llm"],
        help="Agent type to use (default: random)",
    )

    # Challenge command
    challenge_parser = subparsers.add_parser(
        "challenge", help="Challenge a specific opponent"
    )
    challenge_parser.add_argument("opponent", type=str, help="Username to challenge")
    challenge_parser.add_argument(
        "--format",
        "-f",
        type=str,
        default="gen1ou",
        help="Battle format (default: gen1ou)",
    )
    challenge_parser.add_argument(
        "--agent",
        "-a",
        type=str,
        default="random",
        choices=["random", "highest_damage", "llm"],
        help="Agent type to use (default: random)",
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

    if args.command == "ladder":
        asyncio.run(run_ladder_battles(args.battles, args.format, args.agent))
    elif args.command == "challenge":
        asyncio.run(challenge_opponent(args.opponent, args.format, args.agent))


if __name__ == "__main__":
    main()
