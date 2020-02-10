import random
from cloudbot import hook
from cloudbot.util import colors

responses = ["$(dark_green, bold)It is certain",
             "$(dark_green, bold)It is decidedly so",
             "$(dark_green, bold)Signs point to yes",
             "$(dark_green, bold)Without a doubt",
             "$(dark_green, bold)You may rely on it",
             #"Reply hazy, try again",
             #"Ask again later",
             #"Better not tell you now",
             #"Cannot predict now",
             #"Concentrate and ask again",
             "$(dark_red, bold)Don't count on it",
             "$(dark_red, bold)My reply is no",
             "$(dark_red, bold)My sources say no",
             "$(dark_red, bold)Outlook not so good",
             "$(dark_red, bold)Very doubtful"]


@hook.command("8ball")
async def eightball(message):
    """<question> - asks the all knowing magic electronic eight ball <question>"""
    message(colors.parse(random.choice(responses)))

