import math
import time
from dataclasses import dataclass
from email.utils import parsedate
from typing import List, Optional
from urllib.parse import urljoin

import requests
from atproto_client import Client
from atproto_client.models.app.bsky.embed.external import Main as Embed, External
from atproto_client.models.app.bsky.richtext.facet import Link, Main as Facet
from rss_parser import RSSParser

from src.env import Env


@dataclass
class HackerNewsPost:
    title: str
    url: str
    discussion_url: str
    points: int
    timestamp: float
    hotness: float

    def __init__(self, title: str, url: str, discussion_url: str, points: int, timestamp: float):
        self.title = title
        self.url = url
        self.discussion_url = discussion_url
        self.points = points
        self.timestamp = timestamp
        self.hotness = self.__hotness(points, timestamp)

    @staticmethod
    def __hotness(points, post_timestamp):
        hours_since_post = (time.time() - post_timestamp) / 3600
        return math.log(points + 1, 10) - (hours_since_post / 24)


def main():
    n = 10

    bsky = Client()
    bsky.login(Env.bsky_handle, Env.bsky_password)

    latest_bsky_posts = bsky.get_author_feed(actor=Env.bsky_handle, limit=n * 2)['feed']
    already_posted_urls = [post.post.embed.external.uri for post in latest_bsky_posts]

    for hn_post in __get_hacker_news_posts(n):
        if hn_post.url in already_posted_urls:
            continue

        thumb = __get_thumbnail(hn_post.url)
        thumb_blob = bsky.upload_blob(thumb).blob if thumb else None

        discussion = '[Discussion]'
        text = f"{hn_post.title} {discussion}"

        start = len(hn_post.title) + 1
        end = start + len(discussion)

        bsky.send_post(
            text=text,
            facets=[
                Facet(
                    index={
                        "byteStart": start,
                        "byteEnd": end
                    },
                    features=[
                        Link(uri=hn_post.discussion_url)
                    ]
                )
            ],
            embed=Embed(
                external=External(
                    title=hn_post.title,
                    description=hn_post.title,
                    uri=hn_post.url,
                    thumb=thumb_blob
                )
            )
        )


def __get_thumbnail(url: str) -> Optional[bytes]:
    r = requests.get(url, verify=False)
    if r.ok:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(r.text, 'html.parser')
        og_image_tag = soup.find('meta', property='og:image')
        if og_image_tag:
            return requests.get(urljoin(url, og_image_tag['content']), verify=False).content


def __get_hacker_news_posts(n: int) -> List[HackerNewsPost]:
    rss = RSSParser.parse(requests.get('https://hnrss.org/frontpage', params={'count': 30}).text)
    return sorted([
        HackerNewsPost(
            title=item.title.content,
            url=item.links[0].content,
            discussion_url=item.content.comments.content,
            timestamp=time.mktime(parsedate(item.content.pub_date)),
            points=int(item.description.content.lower().split('points:')[-1].split('<')[0].strip())
        )
        for item in rss.channel.items
    ], key=lambda post: post.hotness, reverse=True)[:n]


def lambda_handler(event: Optional[dict] = None, context: Optional[dict] = None) -> None:
    main()


if __name__ == '__main__':
    main()
