import base64
import hashlib
import hmac
import http.client
import os
import random
import re
import secrets
import time
import urllib.request

from urllib.parse import quote
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
        "".join(["https://www.infomoney.com.br", "/cotacoes/ibovespa/"])
    ).read()
    parser = InfoMoneyHTMLParser()
    parser.feed(payload.decode("UTF8"))
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
        "".join(
            [
                "https://www.jornaldacidadeonline.com.br",
                "/noticias/direito-e-justica/denuncias",
            ]
        )
    ).read()
    parser = JornalDaCidadeOnlineHTMLParser()
    parser.feed(payload.decode("UTF8"))
    return parser.titles[1:]


def sanitize_title(title):
    title_without_pre = re.sub(r"^[A-Z]* *[:-]", "", title.strip())
    return re.sub(r"\(.*\)", "", title_without_pre).strip()


ALIASES = [
    "Bolsa brasileira",
    "Bolsa de ações",
    "Bolsa de São Paulo",
    "Bolsa",
    "BOVESPA",
    "IBOV",
    "Ibovespa Futuro",
    "IBOVESPA",
    "Índice Bovespa",
    "Índice da bolsa",
    "Mercado brasileiro",
    "Mercado de ações",
    "Mercado",
]

UP_MOVEMENTS = [
    "sobe",
    "acelera",
    "se recupera",
    "decola",
    "progride",
    "avança",
]

DOWN_MOVEMENTS = [
    "desce",
    "desacelera",
    "cai",
    "despenca",
    "regride",
    "retrai",
]

LINKS = [
    "após jornal mostrar que",
    "após jornalista denunciar que",
    "depois de evidências de que",
    "depois de reportagem divulgar que",
    "em meio a rumores que",
    "em meio a relatos que",
    "em seguida do vazamento que",
    "em seguida de relato de que",
    "pós notícia mostrar que",
    "pouco depois de noticiado que",
]


def generate_headline():
    ibovespa = get_ibovespa_change()

    alias = random.choice(ALIASES)
    if ibovespa.startswith("+"):
        movement = random.choice(UP_MOVEMENTS)
    if ibovespa.startswith("-"):
        movement = random.choice(DOWN_MOVEMENTS)
    link = random.choice(LINKS)
    title = sanitize_title(random.choice(get_news_from_jornal_cidade_online()))

    message = f"{alias} {movement} ({ibovespa}) {link} {title}"
    return message


def encode(string):
    return quote(string, safe="")


class TwitterClient:
    http_protocol = "https"
    http_host = "api.twitter.com"
    http_resource = "/1.1/statuses/update.json"
    base_url = f"{http_protocol}://{http_host}{http_resource}"
    oauth_timestamp = str(int(time.time()))
    oauth_nonce = secrets.token_hex(32)
    oauth_signature_method = "HMAC-SHA1"
    oauth_version = "1.0"

    def __init__(
        self, consumer_key, consumer_secret, access_token, access_token_secret,
    ):
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.access_token = access_token
        self.access_token_secret = access_token_secret

    def oauth_sign(self, message):
        signature_parameters = {
            "status": message,
            "oauth_consumer_key": self.consumer_key,
            "oauth_nonce": self.oauth_nonce,
            "oauth_signature_method": self.oauth_signature_method,
            "oauth_timestamp": self.oauth_timestamp,
            "oauth_token": self.access_token,
            "oauth_version": self.oauth_version,
        }
        param_string = "&".join(
            [
                f"{p}={encode(signature_parameters[p])}"
                for p in sorted(signature_parameters.keys())
            ]
        )

        signature_base_string = "&".join(
            ["POST", encode(self.base_url), encode(param_string)]
        ).encode("UTF8")
        signing_key = "&".join(
            [encode(self.consumer_secret), encode(self.access_token_secret)]
        ).encode("UTF8")
        oauth_signature = hmac.new(
            signing_key, signature_base_string, hashlib.sha1
        ).digest()
        return base64.b64encode(oauth_signature).decode("UTF8")

    def tweet(self, message):
        authorization_params = {
            "oauth_consumer_key": self.consumer_key,
            "oauth_nonce": self.oauth_nonce,
            "oauth_signature": self.oauth_sign(message),
            "oauth_signature_method": self.oauth_signature_method,
            "oauth_timestamp": self.oauth_timestamp,
            "oauth_token": self.access_token,
            "oauth_version": self.oauth_version,
        }
        oauth_header = ", ".join(
            [
                f'{p}="{encode(authorization_params[p])}"'
                for p in sorted(authorization_params.keys())
            ]
        )
        client = http.client.HTTPSConnection("api.twitter.com")
        client.request(
            "POST",
            "/1.1/statuses/update.json",
            body=f"status={encode(message)}",
            headers={
                "Authorization": f"OAuth {oauth_header}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )
        response = client.getresponse()
        print(response.status, response.reason)
        data = response.read()
        print(data)
        client.close()


def handler(_event, _context):
    consumer_key = os.environ["CONSUMER_KEY"]
    consumer_secret = os.environ["CONSUMER_SECRET"]
    access_token = os.environ["ACCESS_TOKEN"]
    access_token_secret = os.environ["ACCESS_TOKEN_SECRET"]

    headline = generate_headline()
    TwitterClient(
        consumer_key, consumer_secret, access_token, access_token_secret
    ).tweet(headline)


if __name__ == "__main__":
    handler(None, None)
