import argparse
from collections import deque
from data import Comment, Story
import pickle


def main():
    parser = argparse.ArgumentParser(description='Generate HTML from a dump of HackerNews')
    parser.add_argument('dump_file', metavar='dump_file', type=str, help='dump filename')

    args = parser.parse_args()
    dump_fname = args.dump_file

    with open(dump_fname, 'rb') as f:
        stories = pickle.load(f)

    print('<html>')
    print('<head>')
    print('<title>Hacker News</title>')
    print('<link rel="stylesheet" type="text/css" href="style.css">')
    print('</head>')
    print('<body>')
    for story in stories:
        print(f'<div class="story" id="story-{story.id}">')
        print(f'<h2>{story.title}</h2>')
        print(f'<h3>{story.by} - {story.score}</h3>')
        print(f'<a href="{story.url}">{story.url}</a>')
        print('<ul>')
        for comment_tree in story.comments:
            last_depth = 1
            for (depth, comment) in comments_dfs(comment_tree):
                delta = depth - last_depth
                if not comment.by:
                    continue
                if depth > last_depth:
                    print('<li>')
                    for i in range(delta):
                        print('<ul>')
                elif depth < last_depth:
                    for i in range(delta):
                        print('</ul>')
                    print('<li>')
                else:
                    print('<li>')
                last_depth = depth
                print(f'<div class="comment" id="comment-{comment.id}">')
                print('<details open="true">')
                print(f'<summary><b>{comment.by}:</b></summary>')
                print(f'<p>{comment.text}</p>')
                print('</details>')
                print('</div>')
                print('</li>')
        print('</ul>')
        print('</div>')

    print('</body>')
    print('</html>')


def comments_dfs(comment_root):
    nodes = deque([(1, comment_root)])

    while nodes:
        (depth, comment) = nodes.pop()
        yield (depth, comment)
        for kid in comment.kids:
            nodes.append((depth + 1, kid))


main()
