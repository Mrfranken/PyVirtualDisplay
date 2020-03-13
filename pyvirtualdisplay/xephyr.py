from easyprocess import EasyProcess

from pyvirtualdisplay.abstractdisplay import AbstractDisplay

PROGRAM = "Xephyr"


class XephyrDisplay(AbstractDisplay):
    """
    Xephyr wrapper

    Xephyr is an X server outputting to a window on a pre-existing X display
    """

    has_displayfd = False
    has_resizeable = False

    def __init__(
        self, size=(1024, 768), color_depth=24, bgcolor="black", randomizer=None
    ):
        """
        :param bgcolor: 'black' or 'white'
        """
        self.color_depth = color_depth
        self.size = size
        self.bgcolor = bgcolor
        self.screen = 0
        self.process = None
        self.display = None
        AbstractDisplay.__init__(self, randomizer=randomizer)

    @classmethod
    def check_installed(cls):
        p = EasyProcess([PROGRAM, "-help"])
        p.enable_stdout_log = False
        p.enable_stderr_log = False
        p.call()
        helptext = p.stdout
        cls.has_displayfd = "-displayfd" in helptext
        cls.has_resizeable = "-resizeable" in helptext

    @property
    def _cmd(self):
        cmd = [
            PROGRAM,
            dict(black="-br", white="-wr")[self.bgcolor],
            "-screen",
            "x".join(map(str, list(self.size) + [self.color_depth])),
            self.new_display_var,
        ]
        if self.check_startup:
            if self.has_displayfd:
                cmd += ["-displayfd", str(self.check_startup_fd)]
        if self.has_resizeable:
            cmd += ["-resizeable"]
        return cmd
