import sys, os, logging, argparse
from urllib.parse import urlparse
import json
import getpass
import gitlab

logging.getLogger("requests").setLevel(logging.WARNING)
logging.basicConfig(format=':: %(levelname)s: %(message)s', level=logging.DEBUG)

print('Setup')
# Get commandline arguments
parser = argparse.ArgumentParser()
parser.add_argument('hwrepo', help='Full URL to repository where assignment exists')
parser.add_argument('roster', help='File name for class roster')
args = parser.parse_args()
# Parse URL
parsedUrl = urlparse(args.hwrepo)
pathEntries = parsedUrl.path.split('/')
if parsedUrl.netloc:
    host = parsedUrl.netloc
else:
    host = pathEntries[0]
logging.info('Host: ' + host)
try:
    group = pathEntries[1]
    if not group:
        raise Exception
    logging.info('Group: ' + group)
except Exception as e:
    logging.error('Group part was not found in the provided URL')
    sys.exit(1)
try:
    assignment = pathEntries[2]
    if not assignment:
        raise Exception
    if not assignment.endswith('.git'):
        raise Exception('Assignment must end with .git identifier')
    logging.info('Assignment: ' + assignment.rstrip('.git'))
except Exception as e:
    if not e:
        logging.error('Assignment part was not found in provided URL')
    else:
        logging.error(e)
    sys.exit(1)

# Load roster from JSON file
try:
    with open(args.roster, encoding='utf-8') as dataFile:
        roster = json.loads(dataFile.read())
    sections = roster['sections']
    studentCount = 0
    for sec in sections:
        studentCount += len(sec['students'])
except Exception as e:
    logging.error('Failed to open roster file with provided name.')
    sys.exit(1)
logging.info('Roster loaded: {0} (sections: {1}, students: {2})'.format(args.roster, str(len(sections)), str(studentCount)))

print('GitLab Authentication')
# Get user's GitLab info
userName = input('> GitLab User Name: ')
userPw = getpass.getpass('> GitLab Password: ')
# Connect to GitLab
try:
    git = gitlab.Gitlab(host)
    git.login(userName, userPw)
except Exception as e:
    logging.error('GitLab authentication failed.  Please check your credentials.')
    sys.exit(1)

logging.info('Authentication succcessful!')

# Get group ID
for g in git.getall(git.getgroups):
    if g['name'] == group:
        groupId = g['id']

allUsers = git.getall(git.getusers)

# Create an assignment repo for each student
print('Repository Creation & Permissions')
for sec in sections:
    logging.info('Creating repos for students in section ' + sec['name'])
    studentsAdded = 0
    for student in sec['students']:
        projectName = '{0}-{1}-{2}'.format(assignment.rstrip('.git'), sec['name'], student['username'])
        git.createproject(projectName, namespace_id=groupId, visibility_level=0)
        project = git.getproject(group + '/' + projectName)
        for u in allUsers:
            if u['username'] == student['username']:
                git.addprojectmember(project['id'], u['id'], 30) # Developer = 30
                studentsAdded += 1
                break
    logging.info('Done, ' + str(studentsAdded) + ' assignment(s) made')

# Clone base repo and push to each repository that was just created
print('Push Initial Code')
