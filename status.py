"""
Display Circle Ci Status.

This is a simple script to show status of
circle ci builds on an LED matrix.
"""


import os
import pprint
import sys
import time
from itertools import groupby
from os.path import dirname, join


from circleclient import circleclient

from dotenv import load_dotenv


# load environment variables
dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

# connect to circle and get projects
token = os.environ['CIRCLE_API_TOKEN']
client = circleclient.CircleClient(token)
pp = pprint.PrettyPrinter(indent=4)

# setup drawing variables
POLL_RATE = 30
FONTSIZE = 15

matrix = None
image = None
draw = None
font = None

# variables for rendering
last_test = None
status_text = []                    # a list for strings to display
text_length = 0
status_text_index = 0
status_fill = None                  # colour for notification of status
text_x = None                       # the x position of strings
text_y = 32 - (FONTSIZE / 2)        # y position for drawing text
then = time.time()                  # timer for polling circle ci

try:
    is_PI = os.environ['PI']
except:
    is_PI = False

if is_PI:
    # if running on the pi import all image libraries and fonts
    import Image
    import ImageDraw
    import ImageFont
    from rgbmatrix import Adafruit_RGBmatrix

    image = Image.new('RGB', (64, 32))
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype("DejaVuSans.ttf", FONTSIZE)
    matrix = Adafruit_RGBmatrix(32, 1)


def is_project(project):
    """Return True if is correct Project."""
    is_lm = project['username'] == os.environ['USER_NAME']
    is_right_repo = project['reponame'] == os.environ['REPO_NAME']
    return is_lm and is_right_repo


def get_project():
    """Return circleci project."""
    projects = client.projects.list_projects()
    lm = [x for x in projects if is_project(x)]
    # if milli is not present exit
    if len(lm) is 0:
        print('no projects found')
        sys.exit(0)
    return lm[0]


def digest_build_status(job, status):
    """Convert build info into ..."""
    failed = status['failed']
    stat = status['status']
    owner = status['author_name']
    subject = status['subject']
    job_name = status['workflows']['job_name']
    if failed:
        string = '{0}: {1} {2} [Blame {3}]'.format(
            stat,
            job,
            subject,
            owner,
        )
    else:
        string = '{0}: {1} {2}'.format(
            stat,
            job_name,
            subject
        )
    return {
        'failed': failed,
        'string': string,
    }


def workflow_status(workflow):
    """Determine status of workflow."""
    status = 'pending'
    progress = 0
    # should maybe sort these
    for job in workflow:
        if job['outcome'] == 'failed':
            status = 'failed'
            continue
        elif job['status'] != 'success' and status != 'failed':
            status = job['status']
        elif status != 'failed':
            progress += 1

    if progress == len(workflow) and status != 'failed':
        status = 'success'

    return status, round((progress / len(workflow)) * 100)


def process_recent_builds(project):
    """Return most recent workflow and its status."""
    # statuses = []
    recent = client.build.recent(
        project['username'],
        project['reponame'],
        limit=30,
        branch=project['default_branch']
    )
    jobs = []
    # group jobs
    for k, g in groupby(recent, key=lambda s: s['workflows']['workflow_id']):
        workflow = list(g)
        queued_at = workflow[0]['usage_queued_at']
        subject = workflow[0]['subject']
        user = workflow[0]['author_name']
        (status, progress) = workflow_status(workflow)
        jobs.append({
            'key': k,
            'queued_at': queued_at,
            'status': status,
            'progress': progress,
            'user': user,
            'subject': subject,
            'workflow': workflow
        })

    jobs = sorted(jobs, key=lambda j: j['queued_at'])
    return jobs[-1]


def print_status():
    """Simple logging of status."""
    pp.pprint(status_text)


def positive_value(v):
    """Return 0 if value is negative."""
    if v <= 0:
        return 0
    return v


def text_width(text):
    """Return size of sentence in pixels."""
    if matrix is None:
        return 10  # a dummy value for when not running on the PI
    return draw.textsize(text)[0]


def set_global_status_vars(test):
    """Save workflow info into global vars."""
    global status_fill
    global status_text
    global status_text_index
    global text_x
    global text_length
    status_text_index = 0
    text_x = 0
    status = test['status']
    if status == 'success':
        status_fill = '#00FF00'
        status_text = ['Keep calm and carry on!']
    elif status == 'failed':
        status_fill = '#FF0000'
        status_text = [
            test['user'] + ' broke things',
            'with commit: ',
            test['subject']
        ]
    else:
        status_fill = 'rgb(102, 211, 228)'
        status_text = [
            'Running!',
            test['subject'],
            str(test['progress']) + '%'
        ]
    text_length = text_width(status_text[status_text_index])


def animate_sentence():
    """Animate the movement of text across the screen."""
    global status_text
    global status_text_index
    global text_x
    global text_length
    text_x = text_x + 1
    if (text_x > text_length + 64):
        text_x = 0
        status_text_index = (status_text_index + 1) % len(status_text)
        text_length = text_width(status_text[status_text_index])
        print (status_text[status_text_index])


def render():
    """Render status to screen."""
    if matrix is None:
        return
    draw.rectangle((0, 0), (64, 32), fill='black')
    draw.rectangle((0, 0), (64, 4), fill=status_fill)
    draw.rectangle((0, 32 - 4), (64, 32 - 4), fill=status_fill)
    if status_text:
        text = status_text[status_text_index]
        draw.text((64 - text_x, text_y), text, font=font, fill=status_fill)
    matrix.SetImage(image.im.id, 0, 0)


def loop():
    """Main application loop."""
    global last_test
    global then
    now = time.time()
    if now - then > POLL_RATE * 1000 or last_test is None:
        project = get_project()
        last_test = process_recent_builds(project)
        set_global_status_vars(last_test)
        print_status()
    animate_sentence()
    render()
    then = now
    execution_time = time.time() - then
    time.sleep(positive_value(0.05 - execution_time))

while True:
    loop()
