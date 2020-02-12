from cloudbot import hook
from cloudbot.bot import bot
from cloudbot.util import http

formats = {
    "taken": "\x034{domain}\x0f{path}",
    "available": "\x033{domain}\x0f{path}",
    "other": "\x031{domain}\x0f{path}"
}


def format_domain(domain):
    if domain["availability"] in formats:
        domainformat = formats[domain["availability"]]
    else:
        domainformat = formats["other"]
    return domainformat.format(**domain)


@hook.command("domain", "domainr")
def domainr(text):
    """<domain> - Uses domain.nr's API to search for a domain, and similar domains."""
    api_key = bot.config.get_api_key("rapidapi")
    if not api_key:
        return "This command requires an API key from rapidapi.com."

    params = {'client_id': api_key, 'domain': text}
    data = http.get_json('https://domainr.p.rapidapi.com/v2/search', params=params)
    if data['query'] == "":
        return "An error occurred: {status} - {message}".format(**data['error'])

    domains = [format_domain(domain) for domain in data["results"]]
    return "Domains: {}".format(", ".join(domains))

