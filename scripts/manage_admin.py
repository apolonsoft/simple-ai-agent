#!/usr/bin/env python3
"""CLI utility to create or promote platform administrator users."""

import argparse
import asyncio
import sys
from pathlib import Path

# Add apps/api to path so we can import models and database configurations
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root / "apps" / "api"))

from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models.user import UserModel
from app.core.security import get_password_hash


async def create_admin(email: str, password: str, role: str, full_name: str | None = None):
    async with AsyncSessionLocal() as session:
        stmt = select(UserModel).where(UserModel.email == email)
        result = await session.scalars(stmt)
        existing = result.first()
        if existing:
            print(f"[!] User with email '{email}' already exists. Current role: {existing.role}")
            print(f"    Use 'promote' command if you want to update their role.")
            return

        user = UserModel(
            email=email,
            hashed_password=get_password_hash(password),
            role=role,
            full_name=full_name,
            is_active=True,
            is_banned=False,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        print(f"[✓] Successfully created {role} user:")
        print(f"    ID:    {user.id}")
        print(f"    Email: {user.email}")
        print(f"    Role:  {user.role}")


async def promote_user(email: str, role: str):
    async with AsyncSessionLocal() as session:
        stmt = select(UserModel).where(UserModel.email == email)
        result = await session.scalars(stmt)
        user = result.first()
        if not user:
            print(f"[x] Error: User with email '{email}' not found.")
            return

        old_role = user.role
        user.role = role
        await session.commit()
        await session.refresh(user)
        print(f"[✓] Successfully updated role for '{email}':")
        print(f"    Previous: {old_role}")
        print(f"    Current:  {user.role}")


async def list_admins():
    async with AsyncSessionLocal() as session:
        stmt = select(UserModel).where(UserModel.role.in_(["admin", "super_admin"])).order_by(UserModel.created_at)
        result = await session.scalars(stmt)
        admins = result.all()
        if not admins:
            print("[i] No admin or super_admin accounts found in database.")
            return

        print(f"\nFound {len(admins)} administrator account(s):")
        print("-" * 65)
        print(f"{'Role':<14} | {'Email':<30} | {'Status'}")
        print("-" * 65)
        for a in admins:
            status = "Banned" if a.is_banned else ("Active" if a.is_active else "Inactive")
            print(f"{a.role:<14} | {a.email:<30} | {status}")
        print("-" * 65 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Manage Admin and Super Admin accounts")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Create command
    create_parser = subparsers.add_parser("create", help="Create a new administrator account")
    create_parser.add_argument("--email", required=True, help="User email address")
    create_parser.add_argument("--password", required=True, help="User password")
    create_parser.add_argument(
        "--role",
        choices=["admin", "super_admin"],
        default="admin",
        help="Role level (default: admin)",
    )
    create_parser.add_argument("--name", default=None, help="Optional full name")

    # Promote command
    promote_parser = subparsers.add_parser("promote", help="Promote an existing user to admin or super_admin")
    promote_parser.add_argument("--email", required=True, help="User email address to promote")
    promote_parser.add_argument(
        "--role",
        choices=["user", "admin", "super_admin"],
        default="super_admin",
        help="Target role (default: super_admin)",
    )

    # List command
    subparsers.add_parser("list", help="List all administrator and super_admin users")

    args = parser.parse_args()

    if args.command == "create":
        asyncio.run(create_admin(args.email, args.password, args.role, args.name))
    elif args.command == "promote":
        asyncio.run(promote_user(args.email, args.role))
    elif args.command == "list":
        asyncio.run(list_admins())


if __name__ == "__main__":
    main()
