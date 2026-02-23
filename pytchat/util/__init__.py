import datetime
import httpx
import json
import os
import re
from urllib.parse import quote
from .. import config
from ..exceptions import InvalidVideoIdException

PATTERN = re.compile(r"(.*)\(([0-9]+)\)$")

PATTERN_YTURL = re.compile(r"((?<=(v|V)/)|(?<=be/)|(?<=(\?|\&)v=)|(?<=embed/))([\w-]+)")

PATTERN_CHANNEL = re.compile(r"\\\"channelId\\\":\\\"(.{24})\\\"")

PATTERN_M_CHANNEL = re.compile(r"\"channelId\":\"(.{24})\"")

YT_VIDEO_ID_LENGTH = 11

CLIENT_VERSION = "".join(("2.", (datetime.datetime.today() - datetime.timedelta(days=1)).strftime("%Y%m%d"), ".01.00"))

UA = config.headers["user-agent"]

_CHANNEL_PATTERNS = (
    re.compile(r'"channelId":"(UC[a-zA-Z0-9_-]{22})"'),
    re.compile(r'\\"channelId\\":\\"(UC[a-zA-Z0-9_-]{22})\\"'),
)


def extract(url):
    _session = httpx.Client(http2=True)
    html = _session.get(url, headers=config.headers)
    with open(
        str(datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S")) + "test.json", mode="w", encoding="utf-8"
    ) as f:
        json.dump(html.json(), f, ensure_ascii=False)


def save(data, filename, extention) -> str:
    save_filename = filename + "_" + (datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S")) + extention
    with open(save_filename, mode="w", encoding="utf-8") as f:
        f.writelines(data)
    return save_filename


def checkpath(filepath):
    splitter = os.path.splitext(os.path.basename(filepath))
    body = splitter[0]
    extention = splitter[1]
    newpath = filepath
    counter = 1
    while os.path.exists(newpath):
        match = re.search(PATTERN, body)
        if match:
            counter = int(match[2]) + 1
            num_with_bracket = f"({str(counter)})"
            body = f"{match[1]}{num_with_bracket}"
        else:
            body = f"{body}({str(counter)})"
        newpath = os.path.join(os.path.dirname(filepath), body + extention)
    return newpath


def get_param(continuation, replay=False, offsetms: int = 0, dat=""):
    if offsetms < 0:
        offsetms = 0
    ret = {
        "context": {
            "client": {
                "visitorData": dat,
                "userAgent": UA,
                "clientName": "WEB",
                "clientVersion": CLIENT_VERSION,
            },
        },
        "continuation": continuation,
    }
    if replay:
        ret.setdefault("currentPlayerState", {"playerOffsetMs": str(int(offsetms))})
    return ret


def extract_video_id(url_or_id: str) -> str:
    ret = ""
    if "[" in url_or_id:
        url_or_id = url_or_id.replace("[", "").replace("]", "")

    if type(url_or_id) != str:
        raise TypeError(f"{url_or_id}: URL or VideoID must be str, but {type(url_or_id)} is passed.")
    if len(url_or_id) == YT_VIDEO_ID_LENGTH:
        return url_or_id
    match = re.search(PATTERN_YTURL, url_or_id)
    if match is None:
        raise InvalidVideoIdException(f"Invalid video id: {url_or_id}")
    try:
        ret = match.group(4)
    except IndexError:
        raise InvalidVideoIdException(f"Invalid video id: {url_or_id}")

    if ret is None or len(ret) != YT_VIDEO_ID_LENGTH:
        raise InvalidVideoIdException(f"Invalid video id: {url_or_id}")
    return ret


def get_channelid(client, video_id: str) -> str:
    headers = {
        "user-agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
        "accept-language": "en-US,en;q=0.9",
    }

    urls = (
        f"https://www.youtube.com/watch?v={video_id}",
        f"https://www.youtube.com/embed/{video_id}",
        f"https://m.youtube.com/watch?v={video_id}",
    )

    with httpx.Client(http2=True, follow_redirects=True, timeout=20.0, headers=headers) as client:
        for url in urls:
            text = client.get(url).text
            for pattern in _CHANNEL_PATTERNS:
                match = pattern.search(text)
                if match:
                    return match.group(1)

    raise InvalidVideoIdException(f"Cannot find channel id for video id:{video_id}.")


get_channelid_2nd = get_channelid


async def get_channelid_async(client, video_id: str) -> str:
    headers = {
        "user-agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
        "accept-language": "en-US,en;q=0.9",
    }

    urls = (
        f"https://www.youtube.com/watch?v={video_id}",
        f"https://www.youtube.com/embed/{video_id}",
        f"https://m.youtube.com/watch?v={video_id}",
    )

    for url in urls:
        text = (await client.get(url, headers=headers)).text
        for pattern in _CHANNEL_PATTERNS:
            match = pattern.search(text)
            if match:
                return match.group(1)

    raise InvalidVideoIdException(f"Cannot find channel id for video id:{video_id}.")


get_channelid_async_2nd = get_channelid_async
