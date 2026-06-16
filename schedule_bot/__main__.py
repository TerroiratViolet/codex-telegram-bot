from __future__ import annotations

import argparse

from schedule_bot.app import run
from schedule_bot.responses import reply_for_text


def main() -> None:
    parser = argparse.ArgumentParser(description="Run or smoke-test the Telegram bot.")
    parser.add_argument(
        "--smoke-test",
        metavar="TEXT",
        help="Print the reply for TEXT without contacting Telegram.",
    )
    args = parser.parse_args()

    if args.smoke_test is not None:
        reply = reply_for_text(args.smoke_test, first_name="测试用户")
        if reply is not None:
            print(reply)
        return

    run()


if __name__ == "__main__":
    main()
