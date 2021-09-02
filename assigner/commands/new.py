import logging

from assigner.backends.decorators import requires_config_and_backend
from assigner.backends.exceptions import (
    AssignerGroupNotFound,
    RepositoryAlreadyExists,
)

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

    try:
        if dry_run:
            url = backend.repo.build_url(backend_conf, namespace, hw_name)
            ssh_url = "(ssh url not available)"
        else:
            repo = backend.template_repo.new(hw_name, namespace, backend_conf)
            url = repo.url
            ssh_url = repo.ssh_url

        print("Created repo for {}:\n\t{}\n\t{}".format(hw_name, url, ssh_url))

    except AssignerGroupNotFound as e:
        logger.error(e)

        do_create_group = input("\nDo you want to create this group? [y/N]: ")
        if do_create_group.lower() == "y":
            backend.repo.create_group(conf["namespace"], conf["backend"])
            print("{} created!".format(conf["namespace"]))

    except RepositoryAlreadyExists as e:
        logger.warning("Repository %s already exists!", hw_name)
        logger.debug(e)


def setup_parser(parser):
    parser.add_argument("name",
                        help="Name of the assignment.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Don't actually do it.")
    parser.set_defaults(run=new)
