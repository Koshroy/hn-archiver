import argparse
from collections import deque
from data import Comment, Story
from datetime import datetime
import pickle


def main():
    parser = argparse.ArgumentParser(description='Generate HTML from a dump of HackerNews')
    parser.add_argument('--dump-file', metavar='dump_file', type=str, help='dump filename')
    parser.add_argument('--output-dir', metavar='output_dir', type=str, help='output directory')
    parser.add_argument(
        '--num-posts', metavar='num_posts', type=int,
        help='# of posts to render',
        required=False,
    )

    args = parser.parse_args()
    dump_fname = args.dump_file
    output_dir = args.output_dir
    num_posts = args.num_posts

    with open(dump_fname, 'rb') as f:
        stories = pickle.load(f)

    chosen_stories = stories[0:num_posts] if num_posts else stories
    print_top_page(f'{output_dir}/top.html', chosen_stories)
    for story in chosen_stories:
        print_comment_tree(f'{output_dir}/story-{story.id}.html', story)


def print_top_page(fname, stories):
    with open(fname, 'w') as f:
        print('<html>', file=f)
        print('<head>', file=f)
        print('<meta charset="utf-8"/>', file=f)
        print('<title>Hacker News Archived Top Page</title>', file=f)
        print('<link rel="stylesheet" type="text/css" href="../style.css">', file=f)
        print('</head>', file=f)
        print('<body>', file=f)
        print('<h1>Hacker News Top Stories</h1>', file=f)
        print(f'<h2>Last generated at: {datetime.now()}</h2>', file=f)
        print('<hr>', file=f)
        print('<ul>', file=f)
        for story in stories:
            story_dt = datetime.utcfromtimestamp(story.time)
            print(f'<li><div class="story" id="story-{story.id}">', file=f)
            print(f'<h2><a href="story-{story.id}.html">{story.title} - [{story.score}]</a></h2>', file=f)
            print(f'<h3>By: {story.by} at {story_dt} - {story.num_comments} comments</h3>', file=f)
            print('</div></li>', file=f)
        print('</ul>', file=f)
        print('</body></html>', file=f)


def print_comment_tree(fname, story):
    story_dt = datetime.utcfromtimestamp(story.time)
    
    with open(fname, 'w') as f:
        print('<html>', file=f)
        print('<head>', file=f)
        print(f'<title>{story.title}</title>', file=f)
        print('<meta charset="utf-8"/>', file=f)
        print('<link rel="stylesheet" type="text/css" href="../style.css">', file=f)
        print('</head>', file=f)
        print('<body>', file=f)
        print('<header>', file=f)
        print(f'<div class="story-header" id="story-{story.id}">', file=f)
        print(f'<h1>{story.title}</h1>', file=f)
        print(f'<h3>By: {story.by}</h3>', file=f)
        print(f'<h3>Score: {story.score}</h3>', file=f)
        print(f'<h3>Posted at: {story_dt}</h3>', file=f)
        print(f'<a href="{story.url}">{story.url}</a>', file=f)
        print('</header>', file=f)
        print('<hr>', file=f)
        print('<ul>', file=f)

        for comment_tree in story.comments:
            last_depth = 0
            for (depth, comment) in comments_dfs(comment_tree):
                delta = abs(depth - last_depth)
                if not comment.by:
                    continue
                if depth > last_depth:
                    print('<li>', file=f)
                    for i in range(delta):
                        print('<ul><li>', file=f)
                elif depth < last_depth:
                    for i in range(delta):
                        print('</ul></li>', file=f)
                    print('<li>', file=f)
                else:
                    print('<li>', file=f)
                last_depth = depth
                skull = ' ☠' if comment.dead else ''
                comment_dt = datetime.utcfromtimestamp(comment.time)
                print(f'<div class="comment" id="comment-{comment.id}">', file=f)
                print('<details open="true">', file=f)
                print(f'<summary><b>{comment.by}{skull}</b> <u>{comment_dt}</u></summary>', file=f)
                print(f'<p>{comment.text}</p>', file=f)
                print('</details>', file=f)
                print('</div>', file=f)
                print('</li>', file=f)
        print('</ul>', file=f)

        print('</body>', file=f)
        print('</html>', file=f)
    

def comments_dfs(comment_root):
    nodes = deque([(0, comment_root)])

    while nodes:
        (depth, comment) = nodes.popleft()
        yield (depth, comment)
        for kid in comment.kids:
            nodes.append((depth + 1, kid))


main()
