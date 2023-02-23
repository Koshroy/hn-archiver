import argparse
from data import Comment, Story
from fetch import fetch
from generate import generate
import os
import logging
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile


def main():
    parser = argparse.ArgumentParser(description='Fetch all HackerNews posts')
    parser.add_argument(
        '--dump-file', metavar='dump_file', type=str,
        help='Existing dump filename',
        required=False,
    )
    parser.add_argument(
        '--outgoing', metavar='outgoing', type=str,
        help='Directory to place generated archive in for outgoing sends',
        required=False,
    )
    

    loglevel = os.environ.get('LOG_LEVEL') or 'info'
    logging.basicConfig(level=getattr(logging, loglevel.upper()))
    args = parser.parse_args()
    dump_fname = args.dump_file
    outgoing_dir = args.outgoing

    dest_node = os.environ['NNCP_SENDER'] if not outgoing_dir else ''
    base_nncp_dir = os.environ.get('NNCP_DIR')
    style_dir = os.environ['STYLE_DIR']
    nncp_dir = base_nncp_dir + '/' if base_nncp_dir else ''

    logging.info(f'Starting with log level {loglevel}')

    if outgoing_dir:
        num_stories = None
    else:
        try:
            num_stories = int(sys.stdin.readline().strip())
        except ValueError:
            num_stories = None

    if num_stories:
        logging.info(f'Packaging and sending {num_stories} stories')
    else:
        logging.info(f'Packaging and sending all stories')

    with tempfile.TemporaryDirectory() as tmpdirname:
        logging.info(f'tmpdirname: {tmpdirname}')
        tmp_path = Path(tmpdirname)
        out_dir = tmp_path / 'hackernews'
        out_dir.mkdir()
        
        dump_path = Path(dump_fname) if dump_fname else tmp_path / 'fetch.pickle'        
        if not dump_fname:
            logging.info('Fetching new stories')
            fetch(str(dump_path))

        logging.info('Generating output')
        generate(str(dump_path), str(out_dir), Path(style_dir) / 'style.css', num_stories)

        tarpath = tmp_path / 'hackernews.tar.xz'
        logging.info('Creating tarfile')
        with tarfile.open(tarpath, 'x:xz') as tar:
            tar.add(str(out_dir), 'hackernews')

        if outgoing_dir:
            # Move the generated tarfile into the outgoing dir
            logging.info(f'Copying tarfile to outgoing dir {outgoing_dir}')
            shutil.copy(tarpath, Path(outgoing_dir) / tarpath.name)
        else:
            # Instead, send it through nncp-file
            logging.info('Sending tarfile through NNCP')
            proc = subprocess.run([
                f"{nncp_dir}/nncp-file",
                "-cfg",
                "/tmp/nncp/bob.hjson",
                str(tarpath),
                f'{dest_node}:'
            ])
            if proc.returncode != 0:
                logging.error("Error: Could not run nncp-file")
                sys.exit(proc.returncode)


if __name__ == '__main__':
    main()
