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


def is_milli(project):
    is_lm = project['username'] == os.environ['USER_NAME']
    is_right_repo = project['reponame'] == os.environ['REPO_NAME']
    return is_lm and is_right_repo


def get_milli():
    projects = client.projects.list_projects()
    lm = [x for x in projects if is_milli(x)]
    # if milli is not present exit
    if len(lm) is 0:
        print('no projects found')
        sys.exit(0)
    return lm[0]


def digest_build_status(job, status):
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


def loop():
    project = get_milli()
    last_test = process_recent_builds(project)
    status = last_test['status']
    if status == 'success':
        print('Keep calm and carry on!')
        for x in last_test['workflow']:
            print(x['status'], x['workflows']['job_name'])
    elif status == 'failed':
        print('Things are not ok!')
        print(last_test['user'] + ' broke the build with commit: ' + last_test['subject'])
    else:
        print('running ' + last_test['subject'] + ':' + str(last_test['progress']) + '%')
    time.sleep(30)
    loop()

loop()
