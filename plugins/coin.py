import random
from cloudbot import hook


@hook.command(autohelp=False)
async def coin(text, action):
    """[amount] - Flips [amount] of coins."""
    try:
        amount = int(text)
    except (ValueError, TypeError):
        amount = 1

    if amount == 1:
        action("flips a coin and gets {}.".format(random.choice(["heads", "tails"])))
    elif amount == 0:
        action("makes a coin flipping motion with his hands.")
    else:
        heads = int(random.normalvariate(.5 * amount, (.75 * amount) ** .5))
        if heads > amount:  # can sometimes happen with random.normalvariate
            heads = amount
        tails = amount - heads
        action(f"flips {amount} coins and gets {heads} heads and {tails} tails.")

