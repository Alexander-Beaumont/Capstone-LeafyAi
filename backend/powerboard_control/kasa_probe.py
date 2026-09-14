#!/usr/bin/env python3
"""Read-only probe for the physical Kasa powerboards configured in environment."""
from __future__ import annotations

import asyncio
import os


async def main() -> int:
    from kasa import Discover

    user = os.getenv("LEAFY_KASA_USERNAME") or os.getenv("KASA_USERNAME") or ""
    password = os.getenv("LEAFY_KASA_PASSWORD") or os.getenv("KASA_PASSWORD") or ""
    timeout = int(os.getenv("LEAFY_KASA_DISCOVERY_TIMEOUT", "5"))
    hosts = [
        os.getenv("LEAFY_POWERBOARD_1_IP", "").strip(),
        os.getenv("LEAFY_POWERBOARD_2_IP", "").strip(),
    ]
    hosts = [host for host in hosts if host]
    if not hosts:
        print("No powerboard IPs configured. Set LEAFY_POWERBOARD_1_IP / LEAFY_POWERBOARD_2_IP.")
        return 0
    failed = False
    for host in hosts:
        kwargs = {"discovery_timeout": timeout, "timeout": timeout}
        if user and password:
            kwargs.update(username=user, password=password)
        print(f"\nProbing {host} ...")
        try:
            dev = await Discover.discover_single(host, **kwargs)
            if dev is None:
                print("  FAIL: no supported Kasa device discovered")
                failed = True
                continue
            await dev.update()
            print(
                f"  PASS: model={getattr(dev, 'model', None)} "
                f"alias={getattr(dev, 'alias', None)!r} host={dev.host}"
            )
            children = list(dev.children or [])
            print(f"  children={len(children)}")
            for i, child in enumerate(children):
                print(
                    f"    [{i}] alias={getattr(child, 'alias', None)!r} "
                    f"is_on={getattr(child, 'is_on', None)}"
                )
        except Exception as exc:
            failed = True
            print(f"  FAIL: {exc}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
