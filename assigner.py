import argparse
import collections
import getpass
import gitlab
import json
import logging
import os
import shutil
import sys
import yaml

from urllib.parse import urlparse
from git import Repo, Remote


def exit_with_error(msg):
    logging.error(msg)
    sys.exit(1)

def get_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("hwrepo", help="URL to repository where assignment exists")
    parser.add_argument("roster", help="File name for class roster")
    return parser.parse_args()

def parse_repo_url(url):
    parsed_url = urlparse(url)
    ParsedRepoUrl = collections.namedtuple(
        "ParsedRepoUrl",
        ["full", "host_name", "group_name", "assignment_name"])
    path_entries = parsed_url.path.split('/')
    if len(path_entries) < 3:
        exit_with_error(
            "The provided URL is invalid. \n" +
            "Required format: [hostname]/[group]/[repo].git")
    # Get host name
    if parsed_url.netloc:
        host_name = parsed_url.netloc
    else:
        url = "https://" + url
        host_name = path_entries[0]
    if not host_name:
        exit_with_error("Host part was not found in the provided URL")
    # Get group name
    group_name = path_entries[1]
    if not group_name:
        exit_with_error("Group part was not found in the provided URL")
    # Get assignment name
    assignment = path_entries[2]
    if not assignment:
        exit_with_error("Assignment part was not found in provided URL")
    if not assignment.endswith('.git'):
        exit_with_error("Assignment must end with .git identifier")
    assignment_name = assignment[:-4]
    logging.info("Host: " + host_name)
    logging.info("Group: " + group_name)
    logging.info("Assignment: " + assignment_name)
    return ParsedRepoUrl(url, host_name, group_name, assignment_name)

def get_config(file_name):
    if not os.path.isfile(CONFIG_FILE_NAME):
        logging.info("Creating new config file")
        with open(CONFIG_FILE_NAME, 'w') as f:
            f.write("private_token: \n")
    with open(CONFIG_FILE_NAME, 'r') as f:
        config = yaml.load(f)
    logging.info("Config loaded")
    return config

def connect_to_gitlab(host, private_token=""):
    try:
        if private_token:
            logging.info("Private key found")
            glab = gitlab.Gitlab(repo_url.host_name, token=private_token)
        else:
            logging.info("No private key found, add it to speed up authentication")
            glab = gitlab.Gitlab(repo_url.host_name)
            userName = input('> GitLab User Name: ')
            userPw = getpass.getpass('> GitLab Password: ')
            glab.login(userName, userPw)
        logging.info("Authentication succcessful")
    except:
        exit_with_error("GitLab authentication failed - check your credentials")
    return glab

def get_roster(file_name):
    try:
        with open(file_name, encoding="utf-8") as dataFile:
            roster = json.loads(dataFile.read())
    except Exception as e:
        exit_with_error(e)
    if "sections" not in roster or not roster["sections"]:
        exit_with_error("No sections defined in roster file")
    studentCount = 0
    for sec in roster["sections"]:
        studentCount += len(sec["students"])
    logging.info(
        "Roster loaded: {} (section(s): {}, student(s): {})".format(
            file_name, str(len(roster["sections"])), str(studentCount)))
    if not studentCount:
        logging.info("Exiting because no students were found in roster file")
        sys.exit(1)
    return roster

def create_assignment_repo(repo_url, section, student, gitlab_api):
    project_name = repo_url.assignment_name + "-"
    project_name += section["name"] + "-"
    project_name += student["username"]
    # Get group ID
    group = gitlab_api.getgroups(repo_url.group_name)
    group_id = group["id"]
    gitlab_api.createproject(
        project_name,
        namespace_id=group_id,
        visibility_level=0)
    project = gitlab_api.getproject(
        repo_url.group_name + "/" + project_name)
    # Get student GitLab id
    matching_users = gitlab_api.getusers(student["username"])
    if len(matching_users) != 1:
        logging.warning(
            "Student {} {} with username '{}' not found on GitLab"
            .format(
                student["firstname"],
                student["lastname"],
                student["username"]))
        return false
    user = matching_users[0]
    gitlab_api.addprojectmember(project["id"], user["id"], 30)
    # Add url to remote list for use later
    ssh_url = "git@{}:{}/{}.git".format(
        repo_url.host_name, repo_url.group_name, project_name)
    return (student["username"], ssh_url.lower())

def create_assignment_repos(roster, repo_url, gitlab_api):
    all_remotes = []
    for section in roster["sections"]:
        logging.info("Creating repos for students in section " +
                     section["name"])
        repos_made = 0
        for student in section["students"]:
            result = create_assignment_repo(
                repo_url, section, student, gitlab_api)
            if result:
                all_remotes.append(result)
                repos_made += 1
        logging.info("Done, " + str(repos_made) + " repo(s) made")
    return all_remotes

def clone_base_repo(url, dir_name):
    try:
        if os.path.isdir(dir_name):
            shutil.rmtree(dir_name)
        return Repo.clone_from(url, dir_name)
    except Exception as e:
        exit_with_error("Failed to clone repo - check your URL and credentials")
    logging.info("Cloned base repo")

def push_repo_to_remotes(repo, remotes):
    for name, remote in remotes:
        r = Remote.add(repo, name, remote)
        r.push("master")
    logging.info("Base repo pushed to all student repos")

CONFIG_FILE_NAME = "_config.yml"
logging.getLogger("requests").setLevel(logging.WARNING)
logging.basicConfig(format=":: %(levelname)s: %(message)s", level=logging.DEBUG)

print("[Assigner]")

print("\nSet Up")
# Get commandline arguments
args = get_arguments()
# Parse URL
repo_url = parse_repo_url(args.hwrepo)
# Create/load config file
config = get_config(CONFIG_FILE_NAME)

print("\nGitLab Authentication")
gitlab_api = connect_to_gitlab(repo_url.host_name, config["private_token"])

print("\nRepository Creation & Permissions")
# Load roster from JSON file
roster = get_roster(args.roster)
# Create an assignment repo for each student
all_remotes = create_assignment_repos(roster, repo_url, gitlab_api)
# Clone base repo and push to each repository that was just created
local_repo = clone_base_repo(repo_url.full, repo_url.assignment_name)
# Push copy to each remote URL
push_repo_to_remotes(local_repo, all_remotes)

print("\nClean Up")
# Delete local repository
shutil.rmtree(repo_url.assignment_name)
logging.info("Deleted local copy of base repo")

print("\n[Done]")
