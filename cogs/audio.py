import asyncio
import discord
from discord.ext import commands
import yt_dlp

# YouTubeDL format options
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': False,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
    # Bypass "Sign in to confirm you’re not a bot" - STRATEGY 2: TV EMBEDDED
    # This mimics a Smart TV which usually has no login capability, bypassing the check.
    'extractor_args': {
        'youtube': {
            'player_client': ['tv_embedded', 'web_embedded'],
            'player_skip': ['webpage', 'js-interp', 'config']
        }
    }
}

ffmpeg_options = {
    'options': '-vn',
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5' # Ajuda a manter a conexão estável
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False, volume=0.5):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data, volume=volume)

class AudioCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.volume = 0.5 # Default volume 50%
        self.queue = [] # Simple queue: List of (ctx, name, url)

    async def play_next(self, ctx):
        if len(self.queue) > 0:
            ctx, name, url = self.queue.pop(0)
            await self.start_playing(ctx, name, url)
        else:
            # Disconnect if empty? or just stay.
            pass

    async def start_playing(self, ctx, name, url):
        try:
            async with ctx.typing():
                player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True, volume=self.volume)
                
                # Check if still connected
                if not ctx.voice_client:
                     if ctx.author.voice:
                        await ctx.author.voice.channel.connect()
                     else:
                        await ctx.send("Não consegui conectar ao canal de voz.")
                        return

                ctx.voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(ctx), self.bot.loop))
            
            await ctx.send(f"▶️ Tocando agora: **{player.title}**")


        except Exception as e:
            await ctx.send(f"Erro ao tocar áudio: {e}")
            print(f"Play Error: {e}")
            # Try next
            await self.play_next(ctx)

    @commands.command(name="join", help="Entra no canal de voz.")
    async def join(self, ctx):
        if not ctx.author.voice:
            return await ctx.send("Você não está em um canal de voz!")
        
        channel = ctx.author.voice.channel
        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(channel)
        
        await channel.connect()
        await ctx.send(f"🔊 Conectado ao canal **{channel.name}**!")

    @commands.command(name="leave", help="Sai do canal de voz.")
    async def leave(self, ctx):
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.send("Desconectado.")

    @commands.command(name="play", help="Toca um áudio registrado ou URL direta. Uso: !play <nome_ou_url>")
    async def play(self, ctx, query: str):
        if not ctx.author.voice:
            return await ctx.send("Você precisa estar em um canal de voz!")

        url_to_process = query
        title_to_process = query

        # 2. Extrai informações para ver se é Playlist
        # Truque: Se tiver "list=" na URL, forçamos o yt-dlp a olhar a playlist em vez do vídeo único
        # Isso resolve o problema de "watch?v=...&list=..." ser tratado como vídeo único
        if "list=" in url_to_process and "youtube.com" in url_to_process:
            try:
                # Extrai o ID da lista
                import re
                list_id = re.search(r'list=([^&]+)', url_to_process).group(1)
                url_to_process = f"https://www.youtube.com/playlist?list={list_id}"
            except:
                pass # Se falhar, usa a URL original mesmo

        try:
            # Tenta extrair usando a URL processada (que pode ser a playlist forçada)
            # extract_flat=True é CRUCIAL para playlists grandes não travarem o bot (baixa só json leve)
            data = await self.bot.loop.run_in_executor(None, lambda: ytdl.extract_info(url_to_process, download=False, process=False))
        except Exception as e:
            # Se a estratégia da playlist falhar (ex: playlist privada, mix do youtube não suportado, erro de id)
            # Tenta fazer fallback para a URL original (vídeo único)
            if url_to_process != query:
                try:
                    await ctx.send(f"⚠️ Não consegui acessar a playlist (pode ser privada ou Mix). Tentando tocar apenas o vídeo...")
                    data = await self.bot.loop.run_in_executor(None, lambda: ytdl.extract_info(query, download=False, process=False))
                except Exception as e2:
                    await ctx.send(f"Falha no fallback também: {e2}")
                    return
            else:
                await ctx.send(f"Não consegui processar o link/busca: {e}")
                return

        items_to_queue = []
        is_playlist = 'entries' in data

        if is_playlist:
            await ctx.send(f"📜 **Playlist detectada:** {data.get('title', 'Lista')}")
            
            # Se usou extract_flat (process=False), 'entries' é um gerador ou lista de dicts simples
            entries = data.get('entries')
            if not entries: entries = []
            
            count = 0
            for entry in entries:
                v_url = entry.get('url') # No flat extraction, 'url' é o ID ou URL parcial
                if not v_url: continue
                
                # Reconstrói URL completa se necessário
                if "youtube" in url_to_process and len(v_url) == 11: 
                    v_url = f"https://www.youtube.com/watch?v={v_url}"
                
                v_title = entry.get('title') or "Item da Playlist"
                items_to_queue.append((ctx, v_title, v_url))
                count += 1
            
            await ctx.send(f"➕ Adicionando **{count}** músicas à fila...")
        else:
            # Item único
            v_url = data.get('webpage_url') or data.get('url') or url_to_process
            v_title = data.get('title') or title_to_process
            items_to_queue.append((ctx, v_title, v_url))

        # 3. Adiciona à fila
        self.queue.extend(items_to_queue)
        
        # 4. Inicia se estiver parado
        if not ctx.voice_client:
             await ctx.author.voice.channel.connect()

        if not ctx.voice_client.is_playing():
             await self.play_next(ctx)
        else:
             # Se não for playlist (já avisou), avisa o item único
             if not is_playlist:
                 await ctx.send(f"📜 Adicionado à fila: **{items_to_queue[0][1]}**")

    @commands.command(name="stop", help="Para a música e limpa a fila.")
    async def stop(self, ctx):
        self.queue = []
        if ctx.voice_client:
            ctx.voice_client.stop()
        await ctx.send("⏹️ Parado.")

    @commands.command(name="skip", help="Pula para a próxima música.")
    async def skip(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send("⏭️ Pulado.")

    @commands.command(name="pause", help="Pausa a música atual.")
    async def pause(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.send("⏸️ Pausado.")
        else:
            await ctx.send("Não há nada tocando para pausar.")

    @commands.command(name="resume", help="Retoma a música pausada.")
    async def resume(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            await ctx.send("▶️ Retomando.")
        else:
            await ctx.send("A música não está pausada.")

    @commands.command(name="volume", help="Ajusta o volume (0 a 100). Ex: !volume 50")
    async def volume(self, ctx, volume: int):
        if not ctx.author.voice:
            return await ctx.send("Você precisa estar em um canal de voz.")
        
        if 0 <= volume <= 100:
            self.volume = volume / 100 # Converte 50 pra 0.5
            if ctx.voice_client and ctx.voice_client.source:
                ctx.voice_client.source.volume = self.volume
            await ctx.send(f"🔊 Volume definido para **{volume}%**")
        else:
            await ctx.send("Por favor, escolha um valor entre 0 e 100.")


async def setup(bot):
    await bot.add_cog(AudioCog(bot))
