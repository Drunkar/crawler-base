# crawler base

## Requirements

- python 3.X
- docker-ce
- docker-compose
- vnc client(ex. vinagre)

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

at the host machine: open vnc client and connect to `localhost:5900` with password `secret`.


## Example
- RedditCrawler: get item links from user's feed of reddit.com
- InstagramCrawler: get feed photos and captions from user's feed of instagram.com. May not work anymore.
