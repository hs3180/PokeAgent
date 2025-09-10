"""
Showdown Client - Handles communication with Pokemon Showdown servers
"""

import asyncio
import logging
import os
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from dotenv import load_dotenv
from poke_env.battle import Battle
from poke_env.player import Player
from poke_env.ps_client.account_configuration import AccountConfiguration
from poke_env.ps_client.server_configuration import ServerConfiguration

from ..agents.base_agent import BaseAgent


class ShowdownClient:
    """
    Handles all communication with Pokemon Showdown servers
    """

    def __init__(
        self,
        username: str = None,
        password: Optional[str] = None,
        websocket_url: str = None,
        auth_url: str = None,
        battle_format: str = "gen1ou",
        team: Optional[str] = None,
        log_level: int = logging.INFO,
        load_dotenv_file: bool = True,
    ):
        """
        Initialize Showdown client

        Args:
            username: Showdown username
            password: Showdown password (optional)
            websocket_url: WebSocket URL
            auth_url: Authentication URL
            battle_format: Battle format
            team: Team configuration
            log_level: Logging level
            load_dotenv_file: Whether to load .env file
        """
        # Load environment variables
        if load_dotenv_file:
            env_file = Path(__file__).parent.parent.parent / ".env"
            if env_file.exists():
                load_dotenv(env_file)
            else:
                load_dotenv()

        # Get configuration from environment or parameters
        self.username = username or os.environ.get("POKEAGENT_USERNAME")
        self.password = password or os.environ.get("POKEAGENT_PASSWORD")
        self.websocket_url = websocket_url or os.environ.get("POKEAGENT_WEBSOCKET_URL")
        self.auth_url = auth_url or os.environ.get("POKEAGENT_AUTH_URL")
        self.battle_format = battle_format
        self.team = team
        self.log_level = log_level

        # Validate required configuration
        if not self.username:
            raise ValueError(
                "Username is required. Set it as parameter or environment variable POKEAGENT_USERNAME"
            )

        if not self.websocket_url:
            raise ValueError(
                "WebSocket URL is required. Set it as parameter or environment variable POKEAGENT_WEBSOCKET_URL"
            )

        # Generate auth_url if not provided
        if not self.auth_url:
            self.auth_url = self.websocket_url.replace("wss://", "https://").replace(
                "/showdown/websocket", "/action.php?"
            )

        # Create configurations
        self.account_config = AccountConfiguration(self.username, self.password)
        self.server_config = ServerConfiguration(
            websocket_url=self.websocket_url, authentication_url=self.auth_url
        )

        self.agent = None
        self.is_connected = False
        self._battle_stats = {"total_battles": 0, "wins": 0, "losses": 0}

    async def connect(self):
        """Connect to Showdown server"""
        if not self.agent:
            raise RuntimeError(
                "No agent set. Use set_agent() to set an agent before connecting."
            )

        try:
            # The agent will handle connection
            self.is_connected = True
            logging.info(f"Connected to Showdown server: {self.websocket_url}")
        except Exception as e:
            logging.error(f"Failed to connect to Showdown server: {e}")
            self.is_connected = False
            raise

    async def disconnect(self):
        """Disconnect from Showdown server"""
        if self.is_connected:
            self.is_connected = False
            logging.info("Disconnected from Showdown server")

    def set_agent(self, agent: BaseAgent):
        """Set the agent to use for battles"""
        # Initialize the agent with the proper configuration
        agent.initialize_player(
            account_configuration=self.account_config,
            server_configuration=self.server_config,
            battle_format=self.battle_format,
            team=self.team,
        )
        self.agent = agent

    async def challenge_user(self, opponent: str, battle_format: Optional[str] = None):
        """Challenge a specific user"""
        if not self.is_connected:
            raise RuntimeError("Not connected to Showdown server")

        if not self.agent:
            raise RuntimeError("No agent set")

        format_to_use = battle_format or self.battle_format
        await self.agent.challenge_user(opponent, format_to_use)
        logging.info(f"Challenged {opponent} to {format_to_use} battle")

    async def accept_challenge(self, battle_format: Optional[str] = None):
        """Accept a challenge"""
        if not self.is_connected:
            raise RuntimeError("Not connected to Showdown server")

        if not self.agent:
            raise RuntimeError("No agent set")

        format_to_use = battle_format or self.battle_format
        await self.agent.accept_challenge(format_to_use)
        logging.info(f"Accepted {format_to_use} challenge")

    async def ladder(self, battle_format: Optional[str] = None, n_games: int = 1):
        """Join ladder battles"""
        if not self.is_connected:
            raise RuntimeError("Not connected to Showdown server")

        if not self.agent:
            raise RuntimeError("No agent set")

        format_to_use = battle_format or self.battle_format
        try:
            await self.agent.ladder(n_games)
            logging.info(
                f"Started {format_to_use} ladder battles, {n_games} games planned"
            )
        except Exception as e:
            logging.error(f"Failed to join ladder: {e}")
            raise

    async def leave_ladder(self):
        """Leave ladder"""
        if not self.is_connected:
            raise RuntimeError("Not connected to Showdown server")

        if not self.agent:
            raise RuntimeError("No agent set")

        await self.agent.send_message("/cancelsearch")
        logging.info("Left ladder")

    def get_battle_stats(self) -> Dict[str, Any]:
        """Get battle statistics"""
        if not self.agent:
            return self._battle_stats

        stats = self._battle_stats.copy()
        stats["total_battles"] = len(self.agent.battles)
        stats["wins"] = sum(
            1
            for battle in self.agent.battles.values()
            if battle.finished and battle.won
        )
        stats["losses"] = sum(
            1
            for battle in self.agent.battles.values()
            if battle.finished and not battle.won
        )

        return stats

    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect()
