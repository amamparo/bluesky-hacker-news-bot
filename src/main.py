from dataclasses import dataclass
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


def main():
    n = 10

    bsky = Client()
    bsky.login(Env.bsky_handle, Env.bsky_password)

    latest_bsky_posts = bsky.get_author_feed(actor="hacker-news.bsky.social", limit=n * 2)['feed']
    for hn_post in __get_hacker_news_posts(n):
        if any(hn_post.url == post.post.embed.external.uri for post in latest_bsky_posts):
            continue

        thumb_blob = None
        thumb = __get_thumbnail(hn_post.url)
        if thumb:
            img_data = requests.get(thumb).content
            thumb_blob = bsky.upload_blob(img_data).blob

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

def lambda_handler(event: Optional[dict] = None, context: Optional[dict] = None) -> None:
    main()


def __get_thumbnail(url: str):
    r = requests.get(url)
    if r.ok:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(r.text, 'html.parser')
        og_image_tag = soup.find('meta', property='og:image')
        if og_image_tag:
            return urljoin(url, og_image_tag['content'])


def __get_hacker_news_posts(n: int) -> List[HackerNewsPost]:
    rss = RSSParser.parse(requests.get('https://news.ycombinator.com/rss').text)
    posts = [
        HackerNewsPost(
            title=item.title.content,
            url=item.links[0].content,
            discussion_url=item.content.comments.content
        )
        for item in rss.channel.items[:n]
    ]
    return list(reversed(posts))


if __name__ == '__main__':
    main()
