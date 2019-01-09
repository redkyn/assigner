import logging

from requests.exceptions import HTTPError

from assigner.backends.decorators import requires_config_and_backend

help = "Create a new template repo"

logger = logging.getLogger(__name__)


@requires_config_and_backend
def new(conf, backend, args):
    """
    Creates a new template repository for an assignment so that you can add the
    instructions, sample code, etc.
    """
    hw_name = args.name
    dry_run = args.dry_run
    namespace = conf.namespace
    backend_conf = conf.backend

    if dry_run:
        url = backend.repo.build_url(backend_conf, namespace, hw_name)
        print(
            "Created repo for {}:\n\t{}\n\t{}".format(hw_name, url, "(ssh url not available)"))
    else:
        try:
            repo = backend.template_repo.new(hw_name, namespace, backend_conf)
            print("Created repo for {}:\n\t{}\n\t{}".format(hw_name, repo.url, repo.ssh_url))
        except HTTPError as e:
            if e.response.status_code == 400:
                logger.warning("Repository %s already exists!", hw_name)
            else:
                raise


def setup_parser(parser):
    parser.add_argument("name",
                        help="Name of the assignment.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Don't actually do it.")
    parser.set_defaults(run=new)
