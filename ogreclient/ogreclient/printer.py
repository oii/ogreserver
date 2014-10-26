from __future__ import absolute_import

import datetime
import sys
import threading
import traceback

PROGBAR_LEN = 40


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

    TAB_SIZE = 4

    DEFAULT = 'OGRECLIENT'
    ERROR = 'ERROR'
    DEBUG = 'DEBUG'
    UNKNOWN = 'UNKNOWN'

    DEDRM = 'DEDRM'
    WRONG_KEY = 'WRONG KEY'
    CORRUPT = 'CORRUPT'
    NONE = 'NONE'
    RESPONSE = 'RESPONSE'
    STATS = 'STATISTICS'

    log_output = False
    logs = []

    def __init__(self, notimer=False, debug=False, progressbar_len=PROGBAR_LEN, progressbar_char="#"):
        self.notimer = notimer
        self.debug = debug
        self.progressbar_len = progressbar_len
        self.progressbar_char = progressbar_char

        # start the timer if it's in use
        if notimer is False:
            self.start = datetime.datetime.now()

        # used internally for tracking state
        self.progress_running = False
        self.line_needs_finishing = False

        # create a mutex for thread-safe printing
        self.lock = threading.Lock()


    def _get_colour_and_prefix(self, mode=None, success=None):
        colour = self.WHITE

        if mode == self.UNKNOWN:
            colour = self.BLUE
        elif success is True:
            colour = self.GREEN

        if mode == self.ERROR:
            prefix = 'ERROR'
            colour = self.RED
        elif mode is None:
            prefix = self.DEFAULT
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
            self.p(msg, mode, success=False, notime=notime, extra=self.format_excp(excp, self.debug))
        else:
            self.p(msg, mode, success=False, notime=notime)

    def p(self, msg, mode=None, notime=False, success=None, extra=None, nonl=False, tabular=False):
        # print a newline if required (this also ends any active progress bars)
        self.print_newline()

        # setup for print
        colour, prefix = self._get_colour_and_prefix(mode, success=success)

        # default stdout
        out = sys.stdout

        if success is False:
            out = sys.stderr

        # log all prints to a stack for later use
        if self.log_output is True:
            self.logs.append(u'[{: <10}]  {}'.format(prefix, msg))

        # calculate and format elapsed time
        t = self._get_time_elapsed(notime)

        # format tabular data
        if tabular is True and type(msg) is list:
            msg = self._format_tabular(msg)

        # thread-safe printing to stdout
        with self.lock:
            out.write(u'{}[{: <10}]{} {}{}{}{}'.format(
                CliPrinter.YELLOW, prefix, CliPrinter.GREY, t, colour, msg, CliPrinter.END
            ))

            if type(extra) is list:
                t = self._get_time_prefix(notime=True)
                for line in extra:
                    out.write(u'\n{}[{: <10}]  {}{}> {}{}'.format(
                        CliPrinter.YELLOW, prefix, CliPrinter.WHITE, t, CliPrinter.END, line
                    ))
            elif extra is not None:
                t = self._get_time_prefix(notime=True)
                out.write(u'\n{}[{: <10}]  {}{}> {}{}'.format(
                    CliPrinter.YELLOW, prefix, CliPrinter.WHITE, t, CliPrinter.END, extra
                ))

            if nonl is True:
                self.line_needs_finishing = True
            else:
                out.write(u'\n')

            out.flush()


    def progressi(self, amount, mode=None, notime=False):
        colour, prefix = self._get_colour_and_prefix(mode)

        self.progress_running = True

        t = self._get_time_elapsed(notime)
        sys.stdout.write(u'\r{}[{: <10}]{} {}{}{}{}'.format(
            CliPrinter.YELLOW, prefix, CliPrinter.GREY, t, colour,
            (amount * self.progressbar_char),
            CliPrinter.END
        ))
        sys.stdout.flush()

    def progressf(self, num_blocks=None, block_size=1, total_size=None, notime=False):
        if num_blocks is None or total_size is None:
            raise ProgressfArgumentError

        self.progress_running = True

        colour, prefix = self._get_colour_and_prefix(None)

        # calculate progress bar size
        progress = float(num_blocks * block_size) / float(total_size)
        progress = progress if progress < 1 else 1

        t = self._get_time_elapsed(notime)
        sys.stdout.write(u'\r{}[{: <10}]{} {}{}[ {}{} ] {}%{}'.format(
            CliPrinter.YELLOW, prefix, CliPrinter.GREY, t, colour,
            self.progressbar_char * int(progress * self.progressbar_len),
            ' ' * (self.progressbar_len - int(progress * self.progressbar_len)),
            round(progress * 100, 1),
            CliPrinter.END
        ))
        sys.stdout.flush()

    def _get_time_prefix(self, notime=False):
        if self.notimer is True:
            # no timer at global printer level
            return ' '
        elif notime is True:
            # no timer displayed on this particular print
            return ' ' * 9
        else:
            return ''

    def _get_time_elapsed(self, notime=False, formatted=True):
        if self.notimer is True or notime is True:
            return self._get_time_prefix(notime)

        ts = datetime.datetime.now() - self.start
        if formatted is True:
            formatted_ts = '{:02}:{:02}:{:02}'.format(
                ts.seconds // 3600,
                ts.seconds % 3600 // 60,
                ts.seconds % 60
            )
            # return formatted time with space padding
            return '{: <4} '.format(formatted_ts)
        else:
            return ts


    def _format_tabular(self, data):
        column_tab_sizes = {}

        # iterate columns
        for colindex in range(len(data[0])):
            # get the longest string in this column
            len_max_string = max(len(str(row[colindex])) for row in data)
            # calculate the number of tabs required
            num_tabs = 1
            while len_max_string - (CliPrinter.TAB_SIZE * num_tabs) > 0:
                num_tabs += 1
            # store for later
            column_tab_sizes[colindex] = num_tabs

        # assume the first item in the list is the table header
        header_row = data.pop(0)

        # create table header
        header = ''
        for colindex in range(len(header_row)):
            header += '| {}{}'.format(
                header_row[colindex],
                self._get_padding(header_row[colindex], column_tab_sizes[colindex])
            )

        # create table separator
        separator = '+{}\n'.format(len(header) * '-')

        table = ''
        for row in data:
            # check for separator row
            sep = True
            for item in row:
                if item != '-':
                    sep = False
                    break
            if sep is True:
                table += separator
                continue

            # output rows
            for colindex in range(len(row)):
                table += '| {}{}'.format(
                    row[colindex],
                    self._get_padding(row[colindex], column_tab_sizes[colindex])
                )
            table += '\n'

        # compose table and remove trailing newline
        return '\n{0}{1}\n{0}{2}{0}'.format(separator, header, table)[:-1]

    def _get_padding(self, word, num_tabs):
        return ' ' * ((CliPrinter.TAB_SIZE * num_tabs) - len(str(word)))


    def format_excp(self, ex, debug=False):
        msg = '{}: {}'.format(ex.__class__.__name__, ex)

        if debug is True:
            ex_type, ex, tb = sys.exc_info()
            if tb is not None:
                msg += '\n{}'.format(traceback.extract_tb(tb))

            if hasattr(ex, 'inner_excp') and ex.inner_excp is not None:
                msg += '\nInner Exception:\n > {}: {}'.format(
                    ex.inner_excp.__class__.__name__, ex.inner_excp
                )

        return msg

    def close(self):
        self.print_newline()

    def print_newline(self):
        with self.lock:
            if self.line_needs_finishing is True or self.progress_running is True:
                self.progress_running = False
                self.line_needs_finishing = False
                sys.stdout.write(u'\n')
                sys.stdout.flush()


class DummyPrinter:
    def e(self, msg, mode=None, excp=None, notime=False):
        pass

    def p(self, msg, mode=None, notime=False, success=None, extra=None, nonl=False):
        pass

    def progressi(self, amount, mode=None):
        pass

    def progressf(self, num_blocks=None, block_size=None, total_size=None):
        pass


class ProgressfArgumentError(Exception):
    def __init__(self):
        super(ProgressfArgumentError, self).__init__(
            'You must supply num_blocks and total_size'
        )
