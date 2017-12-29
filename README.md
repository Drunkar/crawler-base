# crawler base

## Requirements

- python 3.X
- docker-ce
- docker-compose

## Installation

```
$ pip install -r requirements.txt
```

## Usage

```
$ docker-compose up -d
$ echo '{"username": "YOUR_USERNAME", "password": "YOUR_PASSWORD"}' > auth.json
$ python crawl.py -d
```

## Example
- RedditCrawler: get item links from user's feed of reddit.com
- InstagramCrawler: get feed photos and captions from user's feed of instagram.com. May not work anymore.
