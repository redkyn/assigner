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

CONFIG_FILE_NAME = "_config.yml"
logging.getLogger("requests").setLevel(logging.WARNING)
logging.basicConfig(format=":: %(levelname)s: %(message)s", level=logging.DEBUG)

print("Setup")
# Get commandline arguments
parser = argparse.ArgumentParser()
parser.add_argument('hwrepo', help="URL to repository where assignment exists")
parser.add_argument('roster', help="File name for class roster")
args = parser.parse_args()

# Parse URL
parsed_url = urlparse(args.hwrepo)
path_entries = parsed_url.path.split('/')
if parsed_url.netloc:
    host = parsed_url.netloc
else:
    host = path_entries[0]
logging.info("Host: " + host)

try: # Is there a reason this is done with a try-catch instead of an if-else?
    group = path_entries[1]
    if not group:
        raise Exception
    logging.info("Group: " + group)
except Exception as e:
    logging.error("Group part was not found in the provided URL")
    sys.exit(1)
    
try: # Ditto here
    assignment = path_entries[2]
    if not assignment:
        raise Exception
    if not assignment.endswith('.git'): # Why raise an exception over this if you're just going to strip it anyway?
        raise Exception("Assignment must end with .git identifier")
    assignment_name = assignment.rstrip('.git') # This will happily strip any hanging ., g, i, or t from the end of the assignment name. Ex: "asdfg.git".rstrip(".git") -> "asdf". Better way is to just chop the last four chars off the end of assignment.
    logging.info("Assignment: " + assignment_name)
except Exception as e:
    if not e:
        logging.error("Assignment part was not found in provided URL")
    else:
        logging.error(e)
    sys.exit(1)

# Create/load config file
if not os.path.isfile(CONFIG_FILE_NAME):
    logging.info("Creating new config file")
    with open(CONFIG_FILE_NAME, 'w') as f:
        f.write("private_token: \n")
logging.info("Loading config file")
with open(CONFIG_FILE_NAME, 'r') as f:
    config = yaml.load(f)
if not config["private_token"]: #nit: if "private_token" not in config: reads better to me
    logging.warning("""
        No GitLab private token has been set in {}.
        Add it in order to speed up authentication.
        """.format(CONFIG_FILE_NAME))

# Load roster from JSON file
try:
    with open(args.roster, encoding='utf-8') as dataFile:
        roster = json.loads(dataFile.read())
    sections = roster['sections']
    studentCount = 0
    for sec in sections:
        studentCount += len(sec['students'])
except Exception as e: #I would catch this as close to where it's thrown as possible. Also, you can just do 'except' if you don't care about what the exception was.
    logging.error("Failed to open roster file with provided name.")
    sys.exit(1)
logging.info(
    "Roster loaded: {} (sections: {}, students: {})".format(
        args.roster, str(len(sections)), str(studentCount)))

print("GitLab Authentication")
try:
    if config["private_token"]: #nit, use 'in' 
        logging.info("Private key found.")
        glab = gitlab.Gitlab(host, token=config["private_token"])
    else:
        logging.info("No private key found.")
        glab = gitlab.Gitlab(host)
        userName = input('> GitLab User Name: ')
        userPw = getpass.getpass('> GitLab Password: ')
        glab.login(userName, userPw)
except Exception as e: #nit, just use 'except' if you don't care about e
    logging.error("""
        GitLab authentication failed.
        Please check your credentials.""")
    sys.exit(1)
logging.info("Authentication succcessful!")

# Get group ID
for g in glab.getall(glab.getgroups): # This is going to get really slow if there are a lot of groups. Is it possible to search by group name?
    if g['name'] == group:
        group_id = g['id']
        break

allUsers = glab.getall(glab.getusers)
all_remotes = []

print("Repository Creation & Permissions")
# Create an assignment repo for each student
for sec in sections:
    logging.info("Creating repos for students in section " + sec['name'])
    repos_made = 0
    for student in sec['students']:
        project_name = assignment_name + '-'
        project_name += sec["name"] + '-'
        project_name += student["username"]
        glab.createproject(
            project_name,
            namespace_id = group_id,
            visibility_level = 0)
        project = glab.getproject(group + '/' + project_name)
        for u in allUsers: # This seems expensive, especially if you're looping over 5,000 users for each student!
            if u['username'] == student['username']:
                # Developer = 30
                glab.addprojectmember(project['id'], u['id'], 30)
                repos_made += 1
                # Add url to remote list for use later
                url = "git@{}:{}/{}.git".format(host, group, project_name)
                all_remotes.append((student["username"], url.lower()))
                break
    logging.info('Done, ' + str(repos_made) + ' assignment(s) made')

print("Push Initial Code")
# Clone base repo and push to each repository that was just created
try:
    if os.path.isdir(assignment_name):
        shutil.rmtree(assignment_name) #careful! don't want to blow away stuff if you run this in the wrong directory. 
    local_repo = Repo.clone_from(args.hwrepo, assignment_name)
except Exception as e:
    logging.error("""
        Failed to clone remote repo.
        Please check your URL and credentials.""")
    sys.exit(1)

# Push copy to each remote URL
for name, remote in all_remotes:
    r = Remote.add(local_repo, name, remote)
    r.push("master")

print("Cleaning Up")
# Delete local repository
logging.info("Delete clone assignment repository")
shutil.rmtree(assignment_name)
