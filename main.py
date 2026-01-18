import asyncio
import os
import logging
from config import DISCORD_TOKEN
import discord
from discord.ext import commands
import static_ffmpeg

# Configura o ffmpeg automaticamente
static_ffmpeg.add_paths()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")

intents = discord.Intents.default()
intents.message_content = True

class CommunityBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=commands.DefaultHelpCommand()
        )

    async def setup_hook(self):
        # Carrega as Cogs (vários arquivos de comandos)
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py"):
                try:
                    await self.load_extension(f"cogs.{filename[:-3]}")
                    logger.info(f"Extensão carregada: {filename}")
                except Exception as e:
                    logger.error(f"Falha ao carregar extensão {filename}: {e}")

    async def on_ready(self):
        logger.info(f'Logado como {self.user} (ID: {self.user.id})')
        logger.info('------')

async def main():
    async with CommunityBot() as bot:
        if not DISCORD_TOKEN:
             logger.error("DISCORD_TOKEN não encontrado nas variáveis de ambiente.")
             return
        await bot.start(DISCORD_TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # Handle Ctrl+C allowing for graceful shutdown
        pass
