import random
import re
import urllib.request
from html.parser import HTMLParser


class InfoMoneyHTMLParser(HTMLParser):
    def __init__(self):
        self.daily_change = None
        self.__grab = None
        super().__init__()

    def handle_data(self, data):
        if self.__grab and data.strip().endswith("%"):
            self.daily_change = data.strip()
            self.__grab = False
        if data == "Variação (Dia)" and self.__grab is None:
            self.__grab = True

    def error(self, message):
        raise RuntimeError(f"failed to parse infomoney's response: {message}")


def get_ibovespa_change():
    payload = urllib.request.urlopen(
        "https://www.infomoney.com.br/cotacoes/ibovespa/"
    ).read()
    parser = InfoMoneyHTMLParser()
    parser.feed(payload.decode("utf-8"))
    return parser.daily_change


class JornalDaCidadeOnlineHTMLParser(HTMLParser):
    def __init__(self):
        self.titles = []
        super().__init__()

    def handle_starttag(self, _tag, attrs):
        titles = [attr[1] for attr in attrs if attr[0] == "title"]
        if len(titles) == 1:
            self.titles.append(titles[0])

    def error(self, message):
        raise RuntimeError(f"failed to parse JCO's response: {message}")


def get_news_from_jornal_cidade_online():
    payload = urllib.request.urlopen(
        "https://www.jornaldacidadeonline.com.br/noticias/direito-e-justica/denuncias"
    ).read()
    parser = JornalDaCidadeOnlineHTMLParser()
    parser.feed(payload.decode("utf-8"))
    return parser.titles[1:]


def sanitize_title(title):
    print(title)
    title_without_pre = re.sub(r"^[A-Z]* *[:-]", "", title.strip())
    return re.sub(r"\(.*\)", "", title_without_pre).strip()


ALIASES = [
    "Bolsa",
    "BOVESPA",
    "IBOV",
    "Ibovespa Futuro",
    "IBOVESPA",
    "Índice Bovespa",
    "Índice da bolsa",
    "Bolsa de São Paulo",
    "Mercado de ações",
    "Mercado",
]

UP_MOVEMENTS = [
    "sobe",
    "acelera",
    "se recupera",
    "decola",
]

DOWN_MOVEMENTS = [
    "desce",
    "desacelera",
    "cai",
    "retrai",
]

LINKS = [
    "após jornal mostrar que",
    "pós notícia em que",
    "depois de reportagem divulgar que",
    "após jornalista denunciar que",
    "com divulgação de evidências de que",
]


def handler(_event, _context):
    ibovespa = get_ibovespa_change()

    alias = random.choice(ALIASES)
    movement = random.choice(UP_MOVEMENTS)
    link = random.choice(LINKS)
    title = sanitize_title(random.choice(get_news_from_jornal_cidade_online()))

    message = f"{alias} {movement} ({ibovespa}) {link} {title}"
    print(message)


if __name__ == "__main__":
    handler(None, None)
