#!/usr/bin/env python3
"""Cloudflare API CLI — DNS 和 Origin Rules 管理工具。

用法:
    python3 cf_api.py dns list [--filter NAME]
    python3 cf_api.py dns add <subdomain> [--ip IP] [--no-proxy]
    python3 cf_api.py dns delete <subdomain>
    python3 cf_api.py origin-rules list
    python3 cf_api.py origin-rules add <hostname> <port>

环境变量 (从 ~/.personal_env source):
    CF_API_TOKEN — Cloudflare API Bearer token
    CF_ZONE_ID   — Zone ID (tianlizeng.cloud)
    VPS_IP       — 默认 A 记录目标 IP
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
import urllib.error

API_BASE = "https://api.cloudflare.com/client/v4"
API_KEY = os.environ.get("CF_API_KEY", "")
API_EMAIL = os.environ.get("CF_API_EMAIL", "")
API_TOKEN = os.environ.get("CF_API_TOKEN", "")
ZONE_ID = os.environ.get("CF_ZONE_ID", "")
DEFAULT_IP = os.environ.get("VPS_IP", "104.218.100.67")


def _headers():
    h = {"Content-Type": "application/json"}
    # Prefer Global API Key (X-Auth-Key + X-Auth-Email)
    if API_KEY and API_EMAIL:
        h["X-Auth-Key"] = API_KEY
        h["X-Auth-Email"] = API_EMAIL
    elif API_TOKEN:
        h["Authorization"] = f"Bearer {API_TOKEN}"
    return h


def _request(method: str, url: str, data: dict | None = None) -> dict:
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=_headers(), method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        err = json.loads(e.read())
        print(f"Error {e.code}: {json.dumps(err.get('errors', []), indent=2)}")
        sys.exit(1)


# ---------------------------------------------------------------------------
# DNS
# ---------------------------------------------------------------------------
def dns_list(filter_name: str | None = None):
    """列出 DNS 记录。"""
    url = f"{API_BASE}/zones/{ZONE_ID}/dns_records?per_page=100"
    if filter_name:
        url += f"&name={filter_name}"
    result = _request("GET", url)
    records = result.get("result", [])
    if not records:
        print("No records found.")
        return
    for r in records:
        proxy = "🟠" if r["proxied"] else "⬜"
        print(f"{proxy} {r['name']:45s} {r['type']:5s} → {r['content']:20s}  (id: {r['id'][:12]}...)")


def dns_add(subdomain: str, ip: str = DEFAULT_IP, proxied: bool = True):
    """添加 A 记录。"""
    name = subdomain if "." in subdomain else f"{subdomain}.tianlizeng.cloud"
    data = {"type": "A", "name": name, "content": ip, "proxied": proxied, "ttl": 1}
    result = _request("POST", f"{API_BASE}/zones/{ZONE_ID}/dns_records", data)
    if result.get("success"):
        r = result["result"]
        print(f"✓ Created: {r['name']} → {r['content']} (proxied={r['proxied']})")
    else:
        print("Failed:", result)


def dns_delete(subdomain: str):
    """删除 DNS 记录。"""
    name = subdomain if "." in subdomain else f"{subdomain}.tianlizeng.cloud"
    # Find record ID
    url = f"{API_BASE}/zones/{ZONE_ID}/dns_records?name={name}"
    result = _request("GET", url)
    records = result.get("result", [])
    if not records:
        print(f"Record not found: {name}")
        sys.exit(1)
    for r in records:
        result = _request("DELETE", f"{API_BASE}/zones/{ZONE_ID}/dns_records/{r['id']}")
        if result.get("success"):
            print(f"✓ Deleted: {r['name']} ({r['type']} → {r['content']})")


# ---------------------------------------------------------------------------
# Origin Rules
# ---------------------------------------------------------------------------
def origin_rules_list():
    """列出 Origin Rules。"""
    url = f"{API_BASE}/zones/{ZONE_ID}/rulesets/phases/http_request_origin/entrypoint"
    result = _request("GET", url)
    rules = result.get("result", {}).get("rules", [])
    if not rules:
        print("No origin rules found.")
        return
    for r in rules:
        port = r.get("action_parameters", {}).get("origin", {}).get("port", "?")
        print(f"[{r.get('enabled', '?')}] port={port}  {r.get('description', '')}")
        print(f"  expression: {r['expression'][:120]}...")
        print()


def origin_rules_add(hostname: str, port: int):
    """把 hostname 加入现有 Origin Rule 的 expression 中。"""
    name = hostname if "." in hostname else f"{hostname}.tianlizeng.cloud"
    # Get current ruleset
    url = f"{API_BASE}/zones/{ZONE_ID}/rulesets/phases/http_request_origin/entrypoint"
    result = _request("GET", url)
    ruleset = result.get("result", {})
    ruleset_id = ruleset.get("id")
    rules = ruleset.get("rules", [])

    if not rules:
        print("No existing origin rules to modify.")
        sys.exit(1)

    # Find the rule with matching port
    target_rule = None
    for r in rules:
        rp = r.get("action_parameters", {}).get("origin", {}).get("port")
        if rp == port:
            target_rule = r
            break

    if not target_rule:
        print(f"No origin rule found for port {port}.")
        sys.exit(1)

    # Check if hostname already in expression
    expr = target_rule["expression"]
    if name in expr:
        print(f"'{name}' already in origin rule for port {port}.")
        return

    # Add hostname to the expression
    # Expression format: (http.host in {"a" "b" "c"})
    insert_point = expr.rfind('"')
    if insert_point == -1:
        print("Cannot parse expression format.")
        sys.exit(1)
    new_expr = expr[:insert_point + 1] + f' "{name}"' + expr[insert_point + 1:]

    # Patch the rule
    patch_url = f"{API_BASE}/zones/{ZONE_ID}/rulesets/{ruleset_id}/rules/{target_rule['id']}"
    patch_data = {
        "action": target_rule["action"],
        "action_parameters": target_rule["action_parameters"],
        "description": target_rule.get("description", ""),
        "enabled": target_rule.get("enabled", True),
        "expression": new_expr,
    }
    result = _request("PATCH", patch_url, patch_data)
    if result.get("success"):
        print(f"✓ Added '{name}' to origin rule (port {port})")
    else:
        print("Failed:", result)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    if not ZONE_ID or not (API_KEY or API_TOKEN):
        print("Error: CF_ZONE_ID and (CF_API_KEY+CF_API_EMAIL or CF_API_TOKEN) must be set.")
        print("Run: source ~/.personal_env")
        sys.exit(1)

    parser = argparse.ArgumentParser(description="Cloudflare API CLI")
    sub = parser.add_subparsers(dest="command")

    # dns
    dns = sub.add_parser("dns", help="DNS record management")
    dns_sub = dns.add_subparsers(dest="action")

    dns_sub.add_parser("list").add_argument("--filter", default=None, help="Filter by name")
    add_p = dns_sub.add_parser("add")
    add_p.add_argument("subdomain", help="Subdomain or full hostname")
    add_p.add_argument("--ip", default=DEFAULT_IP, help="IP address")
    add_p.add_argument("--no-proxy", action="store_true", help="DNS only (no CF proxy)")
    dns_sub.add_parser("delete").add_argument("subdomain", help="Subdomain to delete")

    # origin-rules
    ori = sub.add_parser("origin-rules", help="Origin Rules management")
    ori_sub = ori.add_subparsers(dest="action")
    ori_sub.add_parser("list")
    ori_add = ori_sub.add_parser("add")
    ori_add.add_argument("hostname", help="Hostname to add")
    ori_add.add_argument("port", type=int, help="Origin port")

    args = parser.parse_args()

    if args.command == "dns":
        if args.action == "list":
            dns_list(args.filter)
        elif args.action == "add":
            dns_add(args.subdomain, args.ip, not args.no_proxy)
        elif args.action == "delete":
            dns_delete(args.subdomain)
        else:
            dns.print_help()
    elif args.command == "origin-rules":
        if args.action == "list":
            origin_rules_list()
        elif args.action == "add":
            origin_rules_add(args.hostname, args.port)
        else:
            ori.print_help()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
