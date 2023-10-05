import sys

__all__ = ("main",)


def main():
    import argparse

    from sqs_polling.main import main as _main

    parser = argparse.ArgumentParser(description="SQS polling")
    parser.add_argument(
        "-f", "--func_name", type=str, help="polling function name", required=True
    )
    parser.add_argument("-q", "--queue_url", type=str, help="queue url")
    parser.add_argument("-c", "--concurrency", type=int, help="concurrency", default=1)
    parser.add_argument(
        "-t", "--visibility_timeout", type=int, help="sqs visibility timeout", default=0
    )
    parser.add_argument("-w", "--max_workers", type=int, help="max workers", default=1)
    args = parser.parse_args()
    main_args = {}
    if args.concurrency > 1:
        main_args["max_number_of_messages"] = args.concurrency
    if args.visibility_timeout > 0:
        main_args["visibility_timeout"] = args.visibility_timeout
    if args.max_workers:
        main_args["max_workers"] = args.max_workers
    sys.exit(_main(args.func_name, **main_args))


if __name__ == "__main__":
    main()
