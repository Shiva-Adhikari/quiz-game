import logging


def _logging():
    # Configure only for your application
    log = logging.getLogger(__name__)  # or use a specific name like 'myapp'
    log.setLevel(logging.DEBUG)

    # Create handler and formatter
    handler = logging.StreamHandler()
    formatter = logging.Formatter('\n%(levelname)s | %(asctime)s | %(filename)s | def: %(funcName)s | Lineno: %(lineno)s >> "%(message)s"\n')
    handler.setFormatter(formatter)
    log.addHandler(handler)

    return log


logger = _logging()
