"""Admin CLI.

Usage: ``uv run python -m app.cli hash-password [password]``

Prints an Argon2id hash for ``ADMIN_PASSWORD_HASH``. The plaintext password
is never logged, echoed, or stored.
"""

import argparse
import getpass

from app.core.security import hash_password


def main() -> None:
    parser = argparse.ArgumentParser(prog="app.cli", description="Portfolio backend admin CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    hash_parser = subparsers.add_parser(
        "hash-password",
        help="Generate an Argon2id hash for the ADMIN_PASSWORD_HASH env var",
    )
    hash_parser.add_argument("password", nargs="?", help=argparse.SUPPRESS)

    args = parser.parse_args()
    if args.command == "hash-password":
        password: str = args.password or getpass.getpass("Password: ")
        print(hash_password(password))


if __name__ == "__main__":
    main()
