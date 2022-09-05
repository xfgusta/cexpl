"""Main entry point for cex and python -m cex"""

import signal
import sys

from . import cli

def main():
    """Main command line entry point"""
    # prevent sigpipe
    if not sys.stdout.isatty():
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)

    try:
        cli.main(sys.argv[1:])
    except KeyboardInterrupt:
        pass

if __name__ == '__main__':
    main()
