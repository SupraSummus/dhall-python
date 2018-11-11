from contextlib import contextmanager
from time import time
import logging
import sys


# TODO someday replace sys.stderr with logging, maybe
logger = logging.getLogger(__name__)


@contextmanager
def timeit(title):
    start = time()
    yield
    end = time()
    print('{} took {:.1f}ms'.format(title, (end - start) * 1000), file=sys.stderr)
