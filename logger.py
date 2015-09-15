"""Lightweight logging.
"""
import logging
import sys

__all__ = ['configure_logger']


class CustomFormatter(logging.Formatter):
    def __init__(self):
        logging.Formatter.__init__(self)
        self._info_fmt = '%(message)s'
        self._fmt = '%(levelname)s: %(message)s'

    def format(self, record):
        record.message = record.getMessage()

        if record.levelno == logging.INFO:
            s = self._info_fmt % record.__dict__
        else:
            s = self._fmt % record.__dict__
        return s


class CustomStreamHandler(logging.Handler):
    def __init__(self, stdout=None, stderr=None, formatter=None):
        logging.Handler.__init__(self)
        self.stdout = sys.stdout if stdout is None else stdout
        self.stderr = sys.stderr if stderr is None else stderr
        self.formatter = formatter

    def flush(self):
        """Flushes the stream."""
        for stream in (self.stdout, self.stderr):
            stream.flush()

    def emit(self, record):
        try:
            msg = self.format(record)
            if record.levelno > logging.INFO:
                stream = self.stderr
            else:
                stream = self.stdout
            fs = "%s\n"
            stream.write(fs % msg.encode('utf-8'))
            self.flush()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)


def configure_logger(logger, debug=False, stdout=None, stderr=None):
    """Configure logger to output logging modules to console via
    stdout and stderr.

    Inputs
    ------
    logger : logging.Logger
        Logger instance to configure.

    debug : bool, optional
        If True, DEBUG level messages output to stdout.
        (Default: False)

    stdout : file handle, optional
        Stream to which to write DEBUG and INFO messages.
        (Default: sys.stdout)

    stderr : file handle, optional
        Stream to which to write WARNING, ERROR, and CRITICAL messages.
        (Default: sys.stderr)
    """
    # Set the log level of logger (either to DEBUG or INFO).
    level = logging.DEBUG if debug else logging.INFO
    logger.setLevel(level)

    # Get rid of any extant logging handlers that are installed.
    while logger.handlers:
        top_level_logger.handlers.pop()

    # Install custom-configured handler and formatter.
    fmt = CustomFormatter()
    handler = logging.Handler()
    handler = CustomStreamHandler(stdout=stdout, stderr=stderr,
                                  formatter=fmt)
    logger.addHandler(handler)
