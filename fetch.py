#!/usr/bin/env python3

import aiohttp
import asyncio
from collections import deque
from data import Comment, Story
from itertools import zip_longest
from dataclasses import asdict
import pickle
import ujson


async def main():
    stories = []
    async with aiohttp.ClientSession() as session:
        story_ids = await fetch_top_story_ids(session)
        coroutines = [fetch_item(story_id, session) for story_id in story_ids]
        top = await asyncio.gather(*coroutines)
        for raw_story in top:
            kid_ids = raw_story.get('kids', [])
            comment_tree = await parse_comment_tree(kid_ids, session)
            story = parse_raw_story(raw_story, comment_tree)
            stories.append(story)

    try:
        with open('stories.pickle', 'wb') as f:
            pickle.dump(stories, f)
    except Exception as e:
        print(f'Problem dumping pickle of stories: {e}')
        print('Dumping stories to JSON')
        with open('stories.json', 'w') as f:
            print(ujson.dumps(), file=f)


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
