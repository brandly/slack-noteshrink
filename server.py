import os
import json
from glob import glob
from bottle import route, run, template, post, request
import requests
import shutil
import noteshrink

CLIENT_ID = os.environ['CLIENT_ID']
CLIENT_SECRET = os.environ['CLIENT_SECRET']
OAUTH_TOKEN = os.environ['OAUTH_TOKEN']

if not os.path.exists('tmp'):
    os.makedirs('tmp')

def shrink_files(files, basename):
    noteshrink.notescan_main(noteshrink.get_argument_parser().parse_args(['-b', basename] + files))
    for file in glob('*.png'):
        if file.startswith(basename):
            return file

@post('/action')
def index():
    body = json.load(request.body)
    if body['type'] == 'url_verification':
        # Verify with events API
        return body['challenge']
    elif body['type'] == 'event_callback':
        event = body['event']
        if event['type'] == 'file_shared':
            return file_shared(event)
        # TODO: subscribe to file comments so you can
        # comment "shrink" under existing file

# TODO: properly respond so we don't get retried requests
def file_shared(event):
    response = get_file_info(event['file_id'])

    if response['ok']:
        # TODO: only take certain filetypes
        # TODO: look for "whiteboard" or "shrink" in the file name
        file = response['file']

        headers = { 'Authorization': 'Bearer ' + OAUTH_TOKEN }
        r = requests.get(file['url_private'], headers=headers, stream=True)

        if r.status_code == 200:
            path = './tmp/' + file['id'] + file['filetype']
            with open(path, 'wb') as f:
                r.raw.decode_content = True
                shutil.copyfileobj(r.raw, f)
            shrunken_file = shrink_files([path], file['id'])

            print('done', shrunken_file)
            # TODO: upload to slack
            return 'success'
        else:
            print('oh no', r)

def get_file_info(file_id):
    r = requests.post('https://slack.com/api/files.info', data={
        'token': OAUTH_TOKEN,
        'file': file_id
        })
    return r.json()

run(host='localhost', port=4390)
