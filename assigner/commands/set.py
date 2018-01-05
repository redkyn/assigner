import logging

from assigner.config import config_context


help = "Set configuration values"

logger = logging.getLogger(__name__)


@config_context
def set_conf(conf, args):
    """Sets <key> to <value> in the config.
    """
    conf[args.key] = args.value


def setup_parser(parser):
    parser.add_argument("key", help="Key to set")
    parser.add_argument("value", help="Value to set")
    parser.set_defaults(run=set_conf)
