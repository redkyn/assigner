import logging
import datetime

from assigner.config import config_context

help = "Interactively initialize a new configuration"

logger = logging.getLogger(__name__)


def prompt(explanation, default=None):
    prompt_string = ''
    if default is not None:
        prompt_string = "{} (default: {}): ".format(explanation, default)
    else:
        prompt_string = "{}: ".format(explanation)
    value = input(prompt_string)

    if value == '':
        if default is not None:
            return default

        return prompt(explanation, default)

    return value


def guess_semester():
    now = datetime.datetime.now()
    if now.month < 5:
        semester = 'SP'
    elif now.month < 8:
        semester = 'SS'
    else:
        semester = 'FS'

    return "{}-{}".format(now.year, semester)


@config_context
def init(conf, _):
    conf['gitlab-host'] = "https://{}".format(prompt("Gitlab server to use", "gitlab.com"))
    conf['token'] = prompt("Gitlab access token (from {}/profile/personal_access_tokens)"
                           .format(conf['gitlab-host']))
    conf['semester'] = prompt("Year and semester, in the format YYYY-(FS|SP|SS)", guess_semester())
    conf['namespace'] = prompt("Gitlab group to create repositories under", "{}-CS1001"
                               .format(conf['semester']))
    do_canvas = input("Do you want to configure Canvas integration? [y/N]: ")
    if do_canvas.lower() == 'y':
        conf['canvas-host'] = prompt("Canvas server to use (???.instructure.com)")
        conf['canvas-token'] = prompt("Canvas access token (from {}/profile/settings)"
                                      .format(conf['canvas-host']))

    print("Congratulations, you're ready to go!")


def setup_parser(parser):
    parser.set_defaults(run=init)
