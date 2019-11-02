import ctypes
import sys
import os
import time
import requests
import praw
from PIL import Image

import argparse

IMAGE_FILE_NAME = "BackgroundImage"
MIN_SUBMISSION_SCORE = 10

def get_absolute_path(path):
    return os.path.abspath(path)

def download_image(url, filename):
    with open(filename, 'wb') as handle:
        response = requests.get(url, stream=True)

        if not response.ok:
            return False

        for block in response.iter_content(1024):
            if not block:
                break

            handle.write(block)
    return True

def equals_epsilon(val, other, ep):
    return val >= other - ep and val <= other + ep

def get_reddit_image(submissions):
    filenames = []
    for submission in submissions:
        if submission.score > MIN_SUBMISSION_SCORE:
            extension = None
            if submission.url.find(".png") >= 0:
                extension = ".png"
            elif submission.url.find(".jpg") >= 0:
                extension = ".jpg"
            if extension:
                filename = IMAGE_FILE_NAME + extension
                if download_image(submission.url, filename):
                    if filename not in filenames:
                        filenames.append(filename)
                    im = Image.open(filename)
                    width, height = im.size
                    if width >= 1920 and equals_epsilon(float(width) / float(height), 16.0 / 9.0, 0.2):
                        return filename, filenames
    return None

def parse_cfg(file):
    with open(file, "r") as f:
        data = f.read()
        data.replace('\r', '')
        lines = data.split('\n')
        result = {}
        for line in lines:
            index = line.find('=')
            if (index >= 0):
                key = line[:index]
                value = line[index + 1:]
                result[key] = value
        return result

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('subreddit', type=str, help="subreddit to find images in")
    parser.add_argument('-k', action="store_true", help="keep resulting image file")
    parser.add_argument('-s', default=MIN_SUBMISSION_SCORE, help="minimum submission score")
    parser.add_argument('--mode', '--m', '-m', default="new", help="where to get images from (new, top, hot)")
    parser.add_argument('--config', '--c', '-c', default="Reddit.cfg", help="where to find reddit api config")

    args = parser.parse_args()

    config = parse_cfg(args.config)

    reddit = praw.Reddit(
        client_id=config['client_id'],
        user_agent=config['user_agent'],
        client_secret=config['client_secret']
    )

    sr = args.subreddit
    subreddit = reddit.subreddit(sr)
    
    submissions = []
    if args.mode == "new":
        submissions = subreddit.new(limit=None)
    elif args.mode == "top":
        submissions = subreddit.top(limit=None)
    elif args.mode == "hot":
        submissions = subreddit.hot(limit=None)
    
    filename, filenames = get_reddit_image(submissions)
    if (filename):
        SPI_SETDESKWALLPAPER = 20 
        ctypes.windll.user32.SystemParametersInfoW(SPI_SETDESKWALLPAPER, 0, get_absolute_path(filename), 0)   
    time.sleep(2)
    for f in filenames:
        if (args.k and f == filename):
            continue
        os.remove(f)

if __name__ == "__main__":
    main()
