import argparse
import getpass
import gitlab
from git import Repo, Remote
import json
import logging
import os
import shutil
import sys
from urllib.parse import urlparse
import yaml

def exit_with_error(msg):
    logging.error(msg)
    sys.exit(1)

CONFIG_FILE_NAME = "_config.yml"
logging.getLogger("requests").setLevel(logging.WARNING)
logging.basicConfig(format=":: %(levelname)s: %(message)s", level=logging.DEBUG)

print("[Assigner]")

print("\nParsing URL Arguments")
# Get commandline arguments
parser = argparse.ArgumentParser()
parser.add_argument("hwrepo", help="URL to repository where assignment exists")
parser.add_argument("roster", help="File name for class roster")
args = parser.parse_args()

# Parse URL
parsed_url = urlparse(args.hwrepo)
path_entries = parsed_url.path.split('/')
if len(path_entries) < 3:
    exit_with_error(
        "The provided URL is invalid. \n" +
        "Required format: [hostname]/[group]/[repo].git")
# Get host name
if parsed_url.netloc:
    host = parsed_url.netloc
else:
    host = path_entries[0]
if not host:
    exit_with_error("Host part was not found in the provided URL")
logging.info("Host: " + host)
# Get group name
group_name = path_entries[1]
if not group_name:
    exit_with_error("Group part was not found in the provided URL")
logging.info("Group: " + group_name)
# Get assignment name
assignment = path_entries[2]
if not assignment:
    exit_with_error("Assignment part was not found in provided URL")
if not assignment.endswith('.git'):
    exit_with_error("Assignment must end with .git identifier")
assignment_name = assignment[:-4]
logging.info("Assignment: " + assignment_name)

# Create/load config file
if not os.path.isfile(CONFIG_FILE_NAME):
    logging.info("Creating new config file")
    with open(CONFIG_FILE_NAME, 'w') as f:
        f.write("private_token: \n")
with open(CONFIG_FILE_NAME, 'r') as f:
    config = yaml.load(f)
logging.info("Config loaded")

# Load roster from JSON file
try:
    with open(args.roster, encoding="utf-8") as dataFile:
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
        args.roster, str(len(roster["sections"])), str(studentCount)))
if not studentCount:
    logging.info("Exiting because no students were found in roster file")
    sys.exit(1)

print("\nGitLab Authentication")
try:
    if config["private_token"]:
        logging.info("Private key found")
        glab = gitlab.Gitlab(host, token=config["private_token"])
    else:
        logging.info("No private key found, add it to speed up authentication")
        glab = gitlab.Gitlab(host)
        userName = input('> GitLab User Name: ')
        userPw = getpass.getpass('> GitLab Password: ')
        glab.login(userName, userPw)
except:
    exit_with_error("GitLab authentication failed - check your credentials")
logging.info("Authentication succcessful")

# Get group ID
group = glab.getgroups(group_name)
group_id = group["id"]
all_remotes = []

print("\nRepository Creation & Permissions")
# Create an assignment repo for each student
for sec in roster["sections"]:
    logging.info("Creating repos for students in section " + sec["name"])
    repos_made = 0
    for student in sec["students"]:
        project_name = assignment_name + "-"
        project_name += sec["name"] + "-"
        project_name += student["username"]
        glab.createproject(
            project_name,
            namespace_id=group_id,
            visibility_level=0)
        project = glab.getproject(group_name + "/" + project_name)
        # Get student GitLab id
        matching_users = glab.getusers(student["username"])
        if len(matching_users) != 1:
            logging.warning(
                "Student {} {} with username '{}' not found on GitLab".format(
                    student["firstname"],
                    student["lastname"],
                    student["username"]))
            continue;
        user = matching_users[0]
        # Developer = 30
        glab.addprojectmember(project["id"], user["id"], 30)
        repos_made += 1
        # Add url to remote list for use later
        url = "git@{}:{}/{}.git".format(host, group_name, project_name)
        all_remotes.append((student["username"], url.lower()))
    logging.info("Done, " + str(repos_made) + " repo(s) made")

# Clone base repo and push to each repository that was just created
try:
    if os.path.isdir(assignment_name):
        shutil.rmtree(assignment_name)
    local_repo = Repo.clone_from(args.hwrepo, assignment_name)
except Exception as e:
    exit_with_error("Failed to clone repo - check your URL and credentials")
logging.info("Cloned base repo")

# Push copy to each remote URL
for name, remote in all_remotes:
    r = Remote.add(local_repo, name, remote)
    r.push("master")
logging.info("Base repo pushed to all student repos")

print("\nClean Up")
# Delete local repository
shutil.rmtree(assignment_name)
logging.info("Deleted local copy of base repo")

print("\n[Done]")
