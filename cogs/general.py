from discord.ext import commands
import discord

class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ping", help="Responde com Pong e a latência.")
    async def ping(self, ctx):
        # Calcula a latência em milissegundos
        latency = round(self.bot.latency * 1000)
        await ctx.send(f"Pong! 🏓 ({latency}ms)")

    @commands.command(name="info", help="Mostra informações sobre o usuário.")
    async def info(self, ctx, member: discord.Member = None):
        # Se nenhum membro for especificado, usa o autor do comando
        member = member or ctx.author
        
        # Cria um embed com as informações
        embed = discord.Embed(title="Informações do Usuário", description=f"Aqui estão as informações de {member.mention}", color=discord.Color.blue())
        embed.add_field(name="ID", value=member.id, inline=True)
        embed.add_field(name="Entrou em", value=member.joined_at.strftime("%d/%m/%Y"), inline=True)
        await ctx.send(embed=embed)

    @commands.command(name="comandos", help="Lista todos os comandos disponíveis.")
    async def comandos(self, ctx):
        embed = discord.Embed(title="Todos Comandos - CHATUBA BOT", color=discord.Color.green())
        
        embed.add_field(name="🎵 Música e Controle", value="""
`!play <link ou nome>`: Toca música (YouTube ou salvo).
`!volume <0-100>`: 🔊 Ajusta o volume global (Ex: !volume 50).
`!pause`: ⏸️ Pausa a música.
`!resume`: ▶️ Despausa.
`!skip`: ⏭️ Pula para a próxima.
`!stop`: ⏹️ Para e limpa a fila.
`!join` / `!leave`: Entra ou sai do canal de voz.
""", inline=False)









        embed.add_field(name="ℹ️ Outros", value="""
`!ping`: Teste de velocidade.
""", inline=False)

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(General(bot))
