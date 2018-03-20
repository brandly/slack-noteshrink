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

@route('/ping')
def ping():
    return 'pong'

@post('/action')
def index():
    body = json.load(request.body)
    if body['type'] == 'url_verification':
        # Verify with events API
        return body['challenge']
    elif body['type'] == 'event_callback':
        event = body['event']
        if event['type'] == 'file_shared':
            return handle_file_id(event['file_id'])
        elif event['type'] == 'file_comment_added':
            return handle_file_id(event['file_id'], event['comment']['comment'])

# TODO: properly respond so we don't get retried requests
# API wants a 200 within 3 seconds
def handle_file_id(file_id, cmd=''):
    response = get_file_info(file_id)

    if response['ok']:
        file = response['file']

        if file['filetype'] not in ['jpg', 'jpeg', 'png']:
            return 'not an image'

        title = file['title'].lower() + cmd.lower()
        if 'whiteboard' not in title and 'shrink' not in title:
            return 'no shrink needed'

        return handle_img_file(file)


handled_files = []
def handle_img_file(file):
    if file['id'] in handled_files:
        # this is a hack because i'm unsure how to respond quickly before
        # shrinking and uploading the image.
        return 'already taken care of'

    handled_files.append(file['id'])
    print('handling', file['name'])

    headers = { 'Authorization': 'Bearer ' + OAUTH_TOKEN }
    r = requests.get(file['url_private'], headers=headers, stream=True)

    if r.status_code != 200:
        print('oh no', r)
        return

    path = './tmp/' + file['id'] + file['filetype']
    with open(path, 'wb') as f:
        r.raw.decode_content = True
        shutil.copyfileobj(r.raw, f)

    shrunken_file = shrink_files([path], file['id'])
    channels = file['channels'] + [file['user']]

    print('uploading', shrunken_file, 'to', channels)
    r = upload_file(shrunken_file, channels)

    if r['ok']:
        print('shrunk', shrunken_file)
        return 'success'
    else:
        print('failed', r)


def upload_file(filename, channels):
    return requests.post(
        'https://slack.com/api/files.upload',
        files={
            'file': open(filename, 'rb'),
        },
        data={
            'token': OAUTH_TOKEN,
            'title': 'shrunk-' + filename,
            'channels': ','.join(channels)
        }
    ).json()

def get_file_info(file_id):
    r = requests.post('https://slack.com/api/files.info', data={
        'token': OAUTH_TOKEN,
        'file': file_id
        })
    return r.json()


run(host='0.0.0.0', port=int(os.getenv('PORT', 4390)))
