#!/usr/bin/env python3

import aiohttp
import asyncio
from collections import deque
from itertools import zip_longest
from dataclasses import asdict, dataclass
import ujson

@dataclass
class Comment:
    by: str
    id: int
    time: int
    text: str
    kids: list
    deleted: bool
    dead: bool

@dataclass
class Story:
    by: str
    id: int
    score: int
    time: int
    title: str
    url: str
    comments: list[Comment]


async def main():
    async with aiohttp.ClientSession() as session:
        story_ids = list(set(await fetch_top_story_ids(session)))
        # story_ids = story_ids[0:3] if len(story_ids) >= 3 else story_ids
        coroutines = [fetch_item(story_id, session) for story_id in story_ids]
        top = await asyncio.gather(*coroutines)
        for raw_story in top:
            kid_ids = raw_story.get('kids', [])
            comment_tree = await parse_comment_tree(kid_ids, session)
            story = parse_raw_story(raw_story, comment_tree)
            print(ujson.dumps(asdict(story)))


async def parse_comment_tree(top_ids, session):
    ids = deque(top_ids)
    comment_dict = {}

    while ids:
        tasks = [fetch_item(id, session) for id in ids]
        raw_comments = await asyncio.gather(*tasks)
        new_comments = dict(
            ((comment_id, raw_comment)
            for comment_id, raw_comment in zip_longest(ids, raw_comments)),
        )
        comment_dict.update(new_comments)
        ids.clear()
        for raw_comment in raw_comments:
            # Why do we need this?
            if not raw_comment:
                continue

            for kid_id in raw_comment.get('kids', []):
                ids.append(kid_id)

    raw_comments = [comment_dict[id] for id in top_ids if id in comment_dict]
    top_comments = [parse_raw_comment(raw) for raw in raw_comments if raw]
    current_level = deque(top_comments)
    while current_level:
        comment = current_level.pop()
        raw_kids = [comment_dict[id] for id in comment.kids if id in comment_dict]
        kids = [parse_raw_comment(raw) for raw in raw_kids if raw]
        comment.kids = kids
        for kid in kids:
            current_level.append(kid)

    return top_comments

def parse_raw_story(raw_story, comments):
    return Story(
        by=raw_story['by'],
        id=raw_story['id'],
        score=raw_story['score'],
        time=raw_story['time'],
        title=raw_story['title'],
        url=raw_story.get('url', ''),
        comments=comments,
    )

def parse_raw_comment(raw_comment):
    return Comment(
        by=raw_comment.get('by', ''),
        id=raw_comment['id'],
        kids=raw_comment.get('kids', []),
        text=raw_comment.get('text', ''),
        time=raw_comment['time'],
        deleted=raw_comment.get('deleted', False),
        dead=raw_comment.get('dead', False),
    )

async def fetch_top_story_ids(session):
    url = 'https://hacker-news.firebaseio.com/v0/topstories.json'
    async with session.get(url) as response:
        return await response.json()


async def fetch_item(item_id, session):
    url = f'https://hacker-news.firebaseio.com/v0/item/{item_id}.json'
    async with session.get(url) as response:
        return await response.json()


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
