import contextlib
import sys
from tqdm import tqdm


# Some of the following is borrowed straight from
# https://github.com/tqdm/tqdm/blob/master/examples/redirect_print.py
class DummyTqdmFile(object):
    """Dummy file-like that will write to tqdm"""
    file = None
    def __init__(self, file):
        self.file = file

    def write(self, x):
        # Avoid print() second call (useless \n)
        # pylint: disable=len-as-condition
        if len(x.rstrip()) > 0:
            tqdm.write(x, file=self.file)

    def flush(self):
        return getattr(self.file, "flush", lambda: None)()


@contextlib.contextmanager
def tqdm_redirect_output():
    orig_out_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = map(DummyTqdmFile, orig_out_err)
        yield orig_out_err[0]
    # Relay exceptions
    except Exception as exc:
        raise exc
    # Always restore sys.stdout/err if necessary
    finally:
        sys.stdout, sys.stderr = orig_out_err


def tqdm_enumerate(iterable, stdout):
    return enumerate(tqdm(iterable, file=stdout, dynamic_ncols=True))


class Progress(object):
    """
    Wraps `tqdm`'s progress bar,
    redirecting stdout and stderr so that log messages
    do not clobber the progress indicator.

    When an instance of this class is created, stdout and stderr
    are redirected; the redirection is undone by a call to `finish()`.

    The typical use of this is as follows:

    progress = Progress()
    for thing in progress.iterate(list_o_things):
        do_stuff(thing)
        log_messages(thing)
    progress.finish()

    Technically this ought to be done with a `with` block, but that adds
    an extra level of indentation.
    """
    def __init__(self):
        self.orig_out_err = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = map(DummyTqdmFile, self.orig_out_err)

    def iterate(self, iterable):
        return tqdm(iterable, file=self.orig_out_err[0], dynamic_ncols=True)

    def enumerate(self, iterable):
        return enumerate(self.iterate(iterable))

    def finish(self):
        sys.stdout, sys.stderr = self.orig_out_err
