from os import listdir

from cloudbot import hook
from cloudbot.util import web


@hook.command(permissions=["botcontrol"])
def plpaste(text, message, bot):
    """<command> - pastes the plugin file that contains <command>."""
    if text in bot.plugin_manager.commands:
        file_path = bot.plugin_manager.commands[text].plugin.file_path
        with open(file_path) as f:
            message(web.paste(f.read(), ext='py'))
    elif text + ".py" in listdir('plugins/'):
        with open('plugins/{}.py'.format(text)) as f:
            message(web.paste(f.read(), ext='py'))
    else:
        return "Could not find specified plugin."
