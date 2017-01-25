from requests.exceptions import HTTPError

from baserepo import BaseRepo, Repo
from config import config_context

help = "Create a new base repo"

logger = logging.getLogger(__name__)


@config_context
def new(conf, args):
    """Creates a new base repository for an assignment so that you can add the
    instructions, sample code, etc.
    """
    hw_name = args.name
    dry_run = args.dry_run
    host = conf.gitlab_host
    namespace = conf.namespace
    token = conf.token

    if dry_run:
        url = Repo.build_url(host, namespace, hw_name)
        print("Created repo at {}.".format(url))
    else:
        try:
            repo = BaseRepo.new(hw_name, namespace, host, token)
            print("Created repo at {}.".format(repo.url))
        except HTTPError as e:
            if e.response.status_code == 400:
                logger.warning("Repository {} already exists!".format(hw_name))
            else:
                raise


def setup_parser(parser):
    parser.add_argument("name",
                           help="Name of the assignment.")
    parser.add_argument("--dry-run", action="store_true",
                           help="Don't actually do it.")
    parser.set_defaults(run=new)
