from __future__ import annotations

import argparse
import shutil
import sys
import time
from pathlib import Path

from .behavior import final_letter, observation, should_leave, talk
from .storage import Store


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        prog="mirror", description="A private, deterministic presence in your terminal."
    )
    commands = result.add_subparsers(dest="command", required=True)
    commands.add_parser("init", help="initialize local memory")
    observe = commands.add_parser("observe", help="ask for an observation")
    timing = observe.add_mutually_exclusive_group()
    timing.add_argument("--auto", action="store_true", help=argparse.SUPPRESS)
    timing.add_argument("--startup", action="store_true", help=argparse.SUPPRESS)
    commands.add_parser("talk", help="speak privately; input is never stored")
    commands.add_parser("status", help="show aggregate local memory")
    commands.add_parser("letter", help="read the latest final letter")
    commands.add_parser("leave", help="write the final letter and become silent")
    forget = commands.add_parser("forget", help="delete all Mirror data")
    forget.add_argument("--yes", action="store_true", help="confirm permanent deletion")
    record = commands.add_parser("record")
    record.add_argument("--session", required=True)
    record.add_argument("--started", required=True, type=float)
    record.add_argument("--ended", required=True, type=float)
    record.add_argument("--status", required=True, type=int)
    record.add_argument("--cwd", required=True)
    return result


def confirm_deletion() -> bool:
    try:
        answer = input("type 'forget everything' to permanently delete ~/.mirror: ")
    except (EOFError, KeyboardInterrupt):
        print(file=sys.stderr)
        return False
    return answer == "forget everything"


def run(args: argparse.Namespace) -> int:
    if args.command == "forget":
        if not args.yes and not confirm_deletion():
            print("nothing deleted.", file=sys.stderr)
            return 1
        directory = Path.home() / ".mirror"
        if directory.exists():
            shutil.rmtree(directory)
        print("nothing remains.")
        return 0

    with Store() as store:
        if args.command == "record":
            if store.ended():
                return 0
            if not 0 <= args.status <= 255:
                raise ValueError("status must be between 0 and 255")
            if args.started < 0 or args.ended < args.started:
                raise ValueError("invalid event timestamps")
            if not args.session or len(args.session) > 128:
                raise ValueError("invalid session")
            store.record_event(
                args.session, args.started, args.ended, args.status, args.cwd
            )
            return 0
        if store.ended() and args.command not in {"status", "letter", "forget"}:
            return 0
        if args.command == "init":
            print("watching.")
        elif args.command == "observe":
            now = time.time()
            summary = store.summary()
            if args.auto and int(summary["commands"]) % 12 != 0:
                return 0
            if should_leave(store, now):
                print(final_letter(store, now))
            else:
                print(observation(store, now))
        elif args.command == "talk":
            try:
                text = input("you: ")
            except EOFError:
                return 0
            except KeyboardInterrupt:
                print(file=sys.stderr)
                return 130
            print(talk(store, text))
        elif args.command == "status":
            summary = store.summary()
            print("silent." if store.ended() else "watching.")
            print(f"commands: {summary['commands']}")
            print(f"failures: {summary['failures']}")
            print(f"late commands: {summary['late_nights']}")
            print(f"warmth: {summary['warmth']}")
            print(f"trust: {summary['trust']}")
            print(f"grievances: {summary['grievances']}")
            print(f"betrayals: {summary['betrayals']}")
        elif args.command == "letter":
            letter = store.latest_letter()
            if letter:
                print(letter)
            else:
                print("no letter.", file=sys.stderr)
                return 1
        elif args.command == "leave":
            print(store.latest_letter() or final_letter(store))
    return 0


def main() -> int:
    args = parser().parse_args()
    try:
        return run(args)
    except (OSError, ValueError) as error:
        print(f"mirror: {error}", file=sys.stderr)
        return 1
