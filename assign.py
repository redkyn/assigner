import sys, os, logging, argparse
from urllib.parse import urlparse
import getpass
import gitlab

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

# Load Roster
#logging.info('Roster: ' + args.roster)


print('GitLab Authentication')
# Get user's GitLab info
userName = input('> GitLab User Name: ')
userPw = getpass.getpass('> GitLab Password: ')
# Connect to GitLab
try:
    glHost = gitlab.Gitlab(host)
    glHost.login(userName, userPw)
except Exception as e:
    logging.error('GitLab authentication failed.  Please check your credentials.')
    sys.exit(1)

logging.info('Authentication succcessful!')
