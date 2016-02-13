from __future__ import absolute_import
from __future__ import unicode_literals

import datetime
import sys
import threading
import traceback

PROGBAR_LEN = 40


class CliPrinter:
    class Colours:
        nocolour = False
        _default = None

        @property
        def default(self):
            return self._default or self._colours.itervalues().next()

        @default.setter
        def default(self, val):
            self._default = val

        def __getattr__(self, key):
            if self.nocolour:
                return ''
            _colours = {
                'NORMAL': '\033[37m',
                'WHITE': '\033[97m',
                'CYAN': '\033[96m',
                'MAGENTA': '\033[95m',
                'BLUE': '\033[94m',
                'YELLOW': '\033[93m',
                'GREEN': '\033[92m',
                'RED': '\033[91m',
                'GREY': '\033[90m',
                'END': '\033[0m',
            }
            try:
                return _colours[key]
            except KeyError:
                raise AttributeError

    colours = Colours()

    TAB_SIZE = 4

    log_output = False
    logs = []

    def __init__(self, use_prefix=False, notimer=False, debug=False, progressbar_len=PROGBAR_LEN, progressbar_char="#", nocolour=False, app_name=None, default_colour=None):
        if use_prefix is True and app_name is None:
            raise IllegalArgumentError('You must supply app_name when use_prefix is True')

        self.app_name = app_name
        self.use_prefix = use_prefix
        self.notimer = notimer
        self.debug = debug
        self.progressbar_len = progressbar_len
        self.progressbar_char = progressbar_char
        self.colours.nocolour = nocolour
        self.colours.default = default_colour

        # start the timer if it's in use
        if notimer is False:
            self.start = datetime.datetime.now()

        # used internally for tracking state
        self.progress_running = False
        self.line_needs_finishing = False

        # create a mutex for thread-safe printing
        self.lock = threading.Lock()


    @staticmethod
    def _get_colour(success=None, bold=False):
        colour = CliPrinter.colours.default or CliPrinter.colours.NORMAL

        if bold:
            colour = CliPrinter.colours.WHITE

        if success is True:
            colour = CliPrinter.colours.GREEN
        elif success is False:
            colour = CliPrinter.colours.RED

        return colour

    def _get_prefix(self, prefix):
        prefix = ''

        if self.use_prefix is True:
            prefix = '[{: <10}] '.format(prefix.upper() or self.app_name.upper())

        return prefix


    def e(self, msg=None, prefix=None, excp=None, notime=False):
        if msg is None and excp is None:
            raise IllegalArgumentError('You must supply either msg or excp')

        if excp:
            # format the exception object into printables
            excp_msg, inner_msg, traceback = self.format_excp(excp, self.debug)

            if self.debug:
                self.p(excp_msg, prefix, success=False, notime=notime, extra=traceback)
            else:
                # display supplied friendly message, or print exception message
                if not msg:
                    msg = excp_msg
                else:
                    extra = str(excp)

                self.p(msg, prefix, success=False, notime=notime, extra=extra or inner_msg)
        else:
            self.p(msg, prefix, success=False, notime=notime)


    def p(self, msg, prefix=None, notime=False, success=None, extra=None, nonl=False, tabular=False, bold=False):
        # print a newline if required (this also ends any active progress bars)
        self.print_newline()

        # setup for print
        colour = CliPrinter._get_colour(success=success, bold=bold)
        prefix = self._get_prefix(prefix)

        # default stdout
        out = sys.stdout

        if success is False:
            out = sys.stderr

        # log all prints to a stack for later use
        if self.log_output is True:
            self.logs.append('{}  {}'.format(prefix, msg))

        if self.start is None:
            notime = True

        # calculate and format elapsed time
        t = self._get_time_elapsed(notime)

        # format tabular data
        if tabular is True and type(msg) is list:
            msg = self._format_tabular(msg)

        # thread-safe printing to stdout
        with self.lock:
            out.write('{}{}{}{}{}{}'.format(
                prefix, CliPrinter.colours.GREY,
                t, colour, msg, CliPrinter.colours.END
            ))

            if type(extra) is list:
                for line in extra:
                    out.write('\n{}> {}{}'.format(
                        prefix, CliPrinter.colours.END, line
                    ))
            elif extra is not None:
                out.write('\n{}> {}{}'.format(
                    prefix, CliPrinter.colours.END, extra
                ))

            if nonl is True:
                self.line_needs_finishing = True
            else:
                out.write('\n')

            out.flush()


    def progressi(self, amount, prefix=None, notime=False):
        colour = CliPrinter._get_colour()
        prefix = self._get_prefix(prefix)

        self.progress_running = True

        t = self._get_time_elapsed(notime)
        sys.stdout.write('\r{}{}{}{}{}{}'.format(
            prefix, CliPrinter.colours.GREY, t, colour,
            (amount * self.progressbar_char),
            CliPrinter.colours.END
        ))
        sys.stdout.flush()


    def progressf(self, num_blocks=None, block_size=1, total_size=None, extra=None, notime=False, prefix=None):
        if num_blocks is None or total_size is None:
            raise ProgressfArgumentError

        if extra is None:
            extra = ''

        self.progress_running = True

        colour = CliPrinter._get_colour()
        prefix = self._get_prefix(prefix)

        # calculate progress bar size
        progress = float(num_blocks * block_size) / float(total_size)
        progress = progress if progress < 1 else 1

        t = self._get_time_elapsed(notime)
        sys.stdout.write('\r{}{}{}{}[ {}{} ] {}%{}'.format(
            prefix, CliPrinter.colours.GREY, t, colour,
            self.progressbar_char * int(progress * self.progressbar_len),
            ' ' * (self.progressbar_len - int(progress * self.progressbar_len)),
            round(progress * 100, 1),
            CliPrinter.colours.GREY, extra,
            CliPrinter.colours.END
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
        """
        Accepts an exception object and returns a tuple of message, inner_message,
        if available and a formatted stacktrace
        """
        msg = '{}: {}'.format(ex.__class__.__name__, ex)
        inner_msg = ''
        stacktrace = ''

        if hasattr(ex, 'inner_excp') and isinstance(ex.inner_excp, Exception):
            inner_msg = unicode(ex.inner_excp)

        if debug is True:
            # extract and print the latest exception; which is good for printing
            # immediately when the exception occurs
            _, _, tb = sys.exc_info()
            if tb is not None:
                stacktrace += ''.join(traceback.format_tb(tb))[:-1]

            # the ex.inner_excp from CoreException mechanism provides a way to
            # wrap a lower exception in a meaningful application specific one
            if hasattr(ex, 'inner_excp') and isinstance(ex.inner_excp, Exception):
                stacktrace += '\nInner Exception:\n  {}: {}\n'.format(
                    ex.inner_excp.__class__.__name__, ex.inner_excp
                )
                if hasattr(ex, 'inner_traceback') and ex.inner_traceback is not None:
                    stacktrace += ex.inner_traceback

        return msg, inner_msg, stacktrace

    def close(self):
        self.print_newline()

    def print_newline(self):
        with self.lock:
            if self.line_needs_finishing is True or self.progress_running is True:
                self.progress_running = False
                self.line_needs_finishing = False
                sys.stdout.write('\n')
                sys.stdout.flush()


class DummyPrinter:
    def e(self, *args, **kwargs):
        pass

    def p(self, *args, **kwargs):
        pass

    def progressi(self, *args, **kwargs):
        pass

    def progressf(self, *args, **kwargs):
        pass


class IllegalArgumentError(ValueError):
    pass


class ProgressfArgumentError(IllegalArgumentError):
    def __init__(self):
        super(ProgressfArgumentError, self).__init__(
            'You must supply num_blocks and total_size'
        )


class CoreException(Exception):
    def __init__(self, message=None, inner_excp=None):
        super(CoreException, self).__init__(message)
        self.inner_excp = inner_excp

        # extract traceback from inner_excp
        if inner_excp is not None:
            # this is not guaranteed to work since sys.exc_info() gets only
            # the _most recent_ exception
            _, _, tb = sys.exc_info()
            if tb is not None:
                self.inner_traceback = ''.join(traceback.format_tb(tb))[:-1]
