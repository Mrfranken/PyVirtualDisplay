import fnmatch
import logging
import os
import select
import tempfile
import time
from threading import Lock

from easyprocess import EasyProcess, EasyProcessError

from pyvirtualdisplay import xauth

try:
    import fcntl
except ImportError:
    fcntl = None

MIN_DISPLAY_NR = 1000
USED_DISPLAY_NR_LIST = []

mutex = Lock()

log = logging.getLogger(__name__)


def lock_files():
    tmpdir = "/tmp"
    pattern = ".X*-lock"
    #        ls = path('/tmp').files('.X*-lock')
    # remove path.py dependency
    names = fnmatch.filter(os.listdir(tmpdir), pattern)
    ls = [os.path.join(tmpdir, child) for child in names]
    ls = [p for p in ls if os.path.isfile(p)]
    return ls


def search_for_display(randomizer=None):
    # search for free display
    ls = list(map(lambda x: int(x.split("X")[1].split("-")[0]), lock_files()))
    if len(ls):
        display = max(MIN_DISPLAY_NR, max(ls) + 3)
    else:
        display = MIN_DISPLAY_NR

    if randomizer:
        display = randomizer.generate()

    return display


class AbstractDisplay(object):
    """
    Common parent for Xvfb and Xephyr
    """

    def __init__(self, use_xauth=False, check_startup=False, randomizer=None):
        with mutex:
            self.display = search_for_display(randomizer=randomizer)
            while self.display in USED_DISPLAY_NR_LIST:
                self.display += 1

            USED_DISPLAY_NR_LIST.append(self.display)

        if use_xauth and not xauth.is_installed():
            raise xauth.NotFoundError()

        self.use_xauth = use_xauth
        self._old_xauth = None
        self._xauth_filename = None
        self.check_startup = check_startup
        if check_startup and not fcntl:
            self.check_startup = False
            log.warning(
                "fcntl module can't be imported, 'check_startup' parameter has been disabled"
            )
            log.warning("fnctl module does not exist on Windows")
        if self.check_startup:
            rp, wp = os.pipe()
            fcntl.fcntl(rp, fcntl.F_SETFD, fcntl.FD_CLOEXEC)
            # TODO: to properly allow to inherit fds to subprocess on
            # python 3.2+ the easyprocess needs small fix..
            fcntl.fcntl(wp, fcntl.F_SETFD, 0)
            self.check_startup_fd = wp
            self._check_startup_fd = rp
        self.proc = EasyProcess(self._cmd)

    @property
    def new_display_var(self):
        return ":%s" % (self.display)

    @property
    def _cmd(self):
        raise NotImplementedError()


