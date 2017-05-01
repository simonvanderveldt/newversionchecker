#!/usr/bin/env python3
import datetime
import os
import toml
import dateutil.parser
from git import Repo
from git.exc import GitCommandError
import requests
import sys
import tempfile

github_api_token = os.environ.get("GITHUB_API_TOKEN")
if not github_api_token:
    sys.exit("GitHub API token not set. Please set the GITHUB_API_TOKEN environment variable, exiting")

try:
    with open("newversionchecker.toml") as conffile:
        config = toml.loads(conffile.read())
except IOError:
    sys.exit("confnewversioncheckerig.toml file not found, exiting")

if not 'github_repo' in config:
    sys.exit('Please add "github_repo" to config.toml')
if not 'check_interval' in config:
    sys.exit('Please add "check_interval" in hours to config.toml')
elif not 'projects' in config:
    sys.exit('Please add a "[projects]" dictionary to config.toml')
elif len(config['projects']) < 1 :
    sys.exit('Please add projects to the "[projects]" dictionary using the format: <project name> = "<project git url>"')


def get_latest_git_tag(repo_url):
    with tempfile.TemporaryDirectory() as tmpdir:
        repo = Repo.clone_from(repo_url, os.path.normpath(tmpdir), depth=50)
        try:
            latest_tag_name = repo.git.describe('--abbrev=0', '--tags')
        except GitCommandError as error:
            if "No names found" in error.stderr:
                return None
            else:
                sys.exit(error)

        # Get date and time from latest tag
        latest_tag_date = dateutil.parser.parse(repo.git.log('-1', '--format=%aI', latest_tag_name)).replace(tzinfo=datetime.timezone.utc)
        print("Latest tag: " + str(latest_tag_name) + ", created on: " + str(latest_tag_date))
        return {"name": latest_tag_name, "date": latest_tag_date}


def get_github_issues():
    try:
        response = requests.get("https://api.github.com/repos/" + config['github_repo'] + "/issues?labels=version+bump&access_token=" + github_api_token, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as error:
        sys.exit(error)

    return response.json()


def create_github_issue(issue):
    try:
        response = requests.post("https://api.github.com/repos/" + config['github_repo'] + "/issues?access_token=" + github_api_token, json=issue, timeout=10)
        response.raise_for_status()
        print("Issue created: " + response.json()['url'])
    except requests.exceptions.RequestException as error:
        sys.exit(error)


for project_name, project_repo_url in config['projects'].items():
    print("Checking latest version for " + project_name)
    check_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=config['check_interval'])
    latest_tag = get_latest_git_tag(project_repo_url)

    if not latest_tag:
        print('Project has no tags, skipping')
        continue

    if latest_tag["date"] > check_date:
        print('Latest tag is newer than ' + str(config['check_interval']) + " hours, checking if there's already an issue for this version bump")
    else:
        print('Latest tag is older than ' + str(config['check_interval']) + ' hours, skipping')
        continue

    new_issue = {
        'title': "New version " + latest_tag["name"] + " of " + project_name + " available",
        'body': "A new version " + latest_tag["name"] + " of " + project_name + " is available since " + str(latest_tag["date"]) + ". For more details see " + project_repo_url + "/releases",
        "labels": [
            "version bump"
        ]
    }

    # Check if there's already an issue for this version bump
    project_issues = get_github_issues()
    existing_issues = [existing_issue for existing_issue in project_issues if existing_issue['title'] == new_issue['title']]
    if not existing_issues:
        print("No existing version bump issue found, creating one")
        create_github_issue(new_issue)
    else:
        print("Issue for this version bump has already been created, see: " + ",".join(existing_issue['html_url'] for existing_issue in existing_issues))
