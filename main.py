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


# Health Check Server for Back4App/PaaS
from aiohttp import web

async def health_check(request):
    return web.Response(text="I'm alive!")

async def start_health_server():
    app = web.Application()
    app.router.add_get('/', health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    logger.info("Health check server running on port 8080")
    print(r"""
   ______  __  __   ___   _____  __  __  ____    ___ 
  / ____/ / / / /  /   | /_  __/ / / / / / __ )  /   |
 / /     / /_/ /  / /| |  / /   / / / / / __  | / /| |
/ /___  / __  /  / ___ | / /   / /_/ / / /_/ / / ___ |
\____/ /_/ /_/  /_/  |_|/_/    \____/ /_____/ /_/  |_|
                                                      
   >>> BOT INICIADO COM SUCESSO! <<<
   >>> Servidor de Health Check: Porta 8080 <<<
    """)

async def main():
    # Start health check server
    await start_health_server()

    async with CommunityBot() as bot:
        if not DISCORD_TOKEN:
             logger.error("DISCORD_TOKEN não encontrado nas variáveis de ambiente.")
             return
        await bot.start(DISCORD_TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
