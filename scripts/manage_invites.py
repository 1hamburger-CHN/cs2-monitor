#!/usr/bin/env python3
"""Invite code management CLI."""
import secrets, sys, asyncio
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models import InviteCode


def generate_code() -> str:
    return "CS2-" + secrets.token_hex(4).upper()


async def create_code(max_uses: int = 1, days_valid: int = 365):
    code_str = generate_code()
    expires = datetime.now(timezone.utc) + timedelta(days=days_valid)
    async with AsyncSessionLocal() as db:
        code = InviteCode(code=code_str, max_uses=max_uses, expires_at=expires)
        db.add(code)
        await db.commit()
        print(f"Invite code: {code_str}  (uses:{max_uses}  expires:{expires.strftime('%Y-%m-%d')})")


async def list_codes():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(InviteCode).order_by(InviteCode.created_at.desc()))
        for c in result.scalars().all():
            status = "VALID" if c.is_valid else "INVALID"
            print(f"{c.code:<20}  {c.used_count}/{c.max_uses}  {status}  expires:{c.expires_at}")


async def deactivate_code(code_str: str):
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(InviteCode).where(InviteCode.code == code_str.strip().upper()))
        code = result.scalar_one_or_none()
        if code:
            code.is_active = False
            await db.commit()
            print(f"Deactivated: {code_str}")
        else:
            print(f"Not found: {code_str}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/manage_invites.py create|list|deactivate [args]")
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "create":
        uses = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        days = int(sys.argv[3]) if len(sys.argv) > 3 else 365
        asyncio.run(create_code(uses, days))
    elif cmd == "list":
        asyncio.run(list_codes())
    elif cmd == "deactivate" and len(sys.argv) > 2:
        asyncio.run(deactivate_code(sys.argv[2]))
    else:
        print(f"Unknown command: {cmd}")
