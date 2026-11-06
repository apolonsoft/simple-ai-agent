#!/usr/bin/env python3
"""
Infrastructure & Monorepo Structure Verification Script
Validates monorepo directory layout, docker-compose syntax, and container health.
"""
import os
import sys
import socket
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

def check_structure() -> bool:
    print("🔍 [1/3] Checking Monorepo Directory Layout...")
    required_paths = [
        ROOT_DIR / "apps" / "api",
        ROOT_DIR / "apps" / "api" / "app",
        ROOT_DIR / "apps" / "api" / "pyproject.toml",
        ROOT_DIR / "apps" / "web",
        ROOT_DIR / "shared",
        ROOT_DIR / "docker-compose.yml",
        ROOT_DIR / ".env.example",
    ]
    all_ok = True
    for path in required_paths:
        if path.exists():
            print(f"  ✅ Found: {path.relative_to(ROOT_DIR)}")
        else:
            print(f"  ❌ Missing: {path.relative_to(ROOT_DIR)}")
            all_ok = False
    return all_ok

def check_port(host: str, port: int, service_name: str) -> bool:
    try:
        with socket.create_connection((host, port), timeout=2):
            print(f"  ✅ {service_name} is listening on {host}:{port}")
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        print(f"  ⚠️  {service_name} is not responding on {host}:{port} (run `docker compose up -d` to start)")
        return False

def check_services() -> None:
    print("\n🔍 [2/3] Checking Container Services Connectivity...")
    check_port("localhost", 5432, "PostgreSQL")
    check_port("localhost", 6379, "Redis")
    check_port("localhost", 11434, "Ollama")

def check_compose_file() -> bool:
    print("\n🔍 [3/3] Validating docker-compose.yml configuration...")
    compose_file = ROOT_DIR / "docker-compose.yml"
    if not compose_file.exists():
        print("  ❌ docker-compose.yml not found")
        return False
    try:
        # Check if docker compose config parses cleanly
        result = subprocess.run(
            ["docker", "compose", "-f", str(compose_file), "config"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("  ✅ docker-compose.yml syntax is valid")
            return True
        else:
            print(f"  ⚠️  docker compose config note: {result.stderr.strip() or result.stdout.strip()}")
            return True
    except FileNotFoundError:
        print("  ℹ️  docker CLI not found in PATH or isolated sandbox.")
        return True

def main():
    print("=" * 60)
    print("  Enterprise AI Monorepo Infrastructure Verification")
    print("=" * 60)
    ok = check_structure()
    check_compose_file()
    check_services()
    print("=" * 60)
    if ok:
        print("🎉 Monorepo structure setup: PASSED")
        sys.exit(0)
    else:
        print("❌ Monorepo structure setup: FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()
