import argparse
import logging

from initialise.baserow import initialise_baserow


def _set_log_level(level: str):
    log_level = logging.INFO
    match level:
        case "WARN":
            log_level = logging.WARNING
        case "DEBUG":
            log_level = logging.DEBUG

    logging.basicConfig(level=log_level)


def _start_operation(system: str):
    match system:
        case "baserow":
            initialise_baserow()


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        prog="HyUi Initialiser",
        description="Various functions to initialise the HyUi environment",
    )

    parser.add_argument("--operation", choices=["baserow"], required=True)
    parser.add_argument(
        "--log-level", choices=["DEBUG", "INFO", "WARNING"], default="INFO"
    )

    args = parser.parse_args()

    _set_log_level(args.log_level)
    _start_operation(args.operation)
