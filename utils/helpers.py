import discord

async def send_error(ctx, error_message):
    embed = discord.Embed(title="Error", description=error_message, color=discord.Color.red())
    await ctx.send(embed=embed)

async def send_success(ctx, message):
    embed = discord.Embed(title="Success", description=message, color=discord.Color.green())
    await ctx.send(embed=embed)
