import datetime
import sys
import traceback


class CliPrinter:
    WHITE = '\033[97m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    GREEN = '\033[92m'
    RED = '\033[91m'
    GREY = '\033[90m'
    END = '\033[0m'

    ERROR = 'ERROR'
    DEBUG = 'DEBUG'
    UNKNOWN = 'UNKNOWN'
    DEDRM = 'DEDRM'
    WRONG_KEY = 'WRONG KEY'
    CORRUPT = 'CORRUPT'
    NONE = 'NONE'
    RESPONSE = 'RESPONSE'

    def __init__(self, start=None):
        self.start = start
        self.progress_running = False
        self.line_needs_finishing = False

    def _get_colour_and_prefix(self, mode=None, success=None):
        colour = self.WHITE

        if mode == self.UNKNOWN:
            colour = self.BLUE
        elif mode == self.DEDRM:
            colour = self.GREEN
            if success is True:
                prefix = 'DECRYPTED'

        if mode == self.ERROR:
            prefix = 'ERROR'
            colour = self.RED
        elif mode is None:
            prefix = 'OGRECLIENT'
        else:
            prefix = mode

        if success is True:
            colour = self.GREEN
        elif success is False:
            colour = self.RED
            if prefix is None:
                prefix = 'ERROR'

        return colour, prefix

    def e(self, msg, mode=ERROR, excp=None, notime=False):
        if excp is not None:
            self.p(msg, mode, success=False, notime=notime, extra=self.format_excp(excp))
        else:
            self.p(msg, mode, success=False, notime=notime)

    def p(self, msg, mode=None, notime=False, success=None, extra=None, nonl=False):
        if self.start is None:
            notime = True

        if self.line_needs_finishing is True:
            self.line_needs_finishing = False
            sys.stdout.write('{}\n'.format(msg))
            return

        if self.progress_running is True:
            self.progress_running = False
            sys.stdout.write('\n')

        colour, prefix = self._get_colour_and_prefix(mode, success=success)

        out = sys.stdout

        if success is False:
            out = sys.stderr

        if notime is True:
            out.write('{}[{: <10}]          {}{}{}'.format(
                CliPrinter.YELLOW, prefix, colour, msg, CliPrinter.END
            ))
        else:
            t = self._get_time_elapsed()
            out.write('{}[{: <10}]{} {: >4} {}{}{}'.format(
                CliPrinter.YELLOW, prefix, CliPrinter.GREY, t, colour, msg, CliPrinter.END
            ))

        if extra is not None:
            out.write('\n{}[{: <10}]          {}> {}{}'.format(
                CliPrinter.YELLOW, prefix, CliPrinter.WHITE, CliPrinter.END, extra
            ))

        if nonl is True:
            self.line_needs_finishing = True
        else:
            out.write('\n')

    def progress(self, amount, mode):
        self.progress_running = True
        colour, prefix = self._get_colour_and_prefix(mode)

        t = self._get_time_elapsed()
        sys.stdout.write('\r{}[{: <10}]{} {: >4} {}{}{}'.format(
            CliPrinter.YELLOW, prefix, CliPrinter.GREY, t, colour, (amount * '#'), CliPrinter.END
        ))
        sys.stdout.flush()

    def _get_time_elapsed(self, formatted=True):
        ts = datetime.datetime.now() - self.start
        if formatted is True:
            formatted_ts = '{:02}:{:02}:{:02}'.format(
                ts.seconds // 3600,
                ts.seconds % 3600 // 60,
                ts.seconds % 60
            )
            return formatted_ts
        else:
            return ts

    def format_excp(self, ex, debug=False):
        msg = '{}: {}'.format(ex.__class__.__name__, ex)

        if debug is True:
            ex_type, ex, tb = sys.exc_info()
            if tb is not None:
                msg += '\n{}'.format(traceback.extract_tb(tb))

        return msg


class DummyPrinter:
    def e(self, msg, mode=None, excp=None, notime=False):
        pass

    def p(self, msg, mode=None, notime=False, success=None, extra=None, nonl=False):
        pass

    def progress(self, amount, mode):
        pass
