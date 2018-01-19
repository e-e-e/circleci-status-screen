# circleci-status-screen

A script to show circle ci build status on a 32 x 64 LED matrix.

# Installation

Clone this repo.

Requires python3+

```sh
virtualenv -p python3 env
source ./env/bin.activate
pip install pipenv
pipenv install
python status.py
```

# Configure

This script loads environment variables from a .env file.
Create a `.env` file with the following settings.

```
CIRCLE_API_TOKEN=your_circle_api_token
USER_NAME=your_circleci_user
REPO_NAME=the_repository
```
