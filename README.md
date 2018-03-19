# slack-noteshrink
> A slackbot that shrinks your notes

you'll need a few environment variables. these values are given to you upon [creating a new slack app](https://api.slack.com/apps?new_app=1).

```
CLIENT_ID=
CLIENT_SECRET=
OAUTH_TOKEN=
```

```
$ pip install -r requirements.txt
$ pip install git+git://github.com/mzucker/noteshrink.git@master
$ python server.py
```

this bot needs `files:read` and `files:write:user` permissions and to be subscribed to `file_comment_added` and `file_shared` events.

slack has [some solid tutorials](https://api.slack.com/tutorials)

props to [noteshrink](https://github.com/mzucker/noteshrink)
