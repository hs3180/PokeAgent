#!/usr/bin/env python3
"""
简化的Gen1 OU天梯对战客户端
连接天梯进行一场Gen1OU比赛
"""

import asyncio
import logging
import sys
import os
import time
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from agents.showdown_agent import ShowdownAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_single_gen1ou_battle():
    """
    连接天梯进行一场Gen1OU比赛
    """
    logger.info("=== Gen1 OU 天梯对战 ===")
    
    # 创建Showdown Agent
    agent = ShowdownAgent(
        username=f"Gen1OU_{int(time.time())}",  # 时间戳用户名避免冲突
        password=None,
        server_url="play.pokemonshowdown.com",
        server_port=443,
        battle_format="gen1ou"
    )
    
    try:
        # 连接服务器
        logger.info("连接到Showdown服务器...")
        await agent.connect()
        logger.info(f"已连接，用户名: {agent.username}")
        logger.info("对战格式: Gen1 OU")
        
        # 加入天梯
        logger.info("加入Gen1 OU天梯...")
        await agent.join_ladder("gen1ou")
        
        # 等待对战开始
        logger.info("等待对手...")
        start_time = time.time()
        while not agent.client.battles and (time.time() - start_time) < 120:
            await asyncio.sleep(1)
        
        if not agent.client.battles:
            logger.error("120秒内未找到对手")
            return
        
        # 进行对战
        logger.info("对战开始！")
        battle_id = list(agent.client.battles.keys())[0]
        battle = agent.client.battles[battle_id]
        
        await battle.wait_until_finished()
        
        # 显示结果
        result = "胜利" if battle.won else "失败"
        logger.info(f"对战结束: {result}")
        
        # 获取统计信息
        stats = agent.get_battle_stats()
        logger.info(f"统计 - 胜: {stats['wins']}, 负: {stats['losses']}")
        
    except Exception as e:
        logger.error(f"对战出错: {e}")
    finally:
        # 离开天梯并断开连接
        try:
            await agent.leave_ladder()
        except:
            pass
        try:
            await agent.disconnect()
        except:
            pass
        logger.info("=== 对战结束 ===")

if __name__ == "__main__":
    # 运行单场Gen1OU天梯对战
    asyncio.run(run_single_gen1ou_battle())