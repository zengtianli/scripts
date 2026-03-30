#!/usr/bin/env python3
"""VPS SSH 快捷操作工具。

用法:
    python3 vps_cmd.py status
    python3 vps_cmd.py logs <service>
    python3 vps_cmd.py nginx-add <subdomain> <port>

环境变量:
    VPS_IP — VPS IP 地址 (默认 104.218.100.67)
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import textwrap

VPS_IP = os.environ.get("VPS_IP", "104.218.100.67")
VPS_USER = "root"
VPS = f"{VPS_USER}@{VPS_IP}"


def ssh_run(cmd: str, timeout: int = 30) -> str:
    """在 VPS 上执行命令并返回输出。"""
    result = subprocess.run(
        ["ssh", "-o", "ConnectTimeout=10", VPS, cmd],
        capture_output=True, text=True, timeout=timeout,
    )
    if result.returncode != 0 and result.stderr:
        print(f"SSH error: {result.stderr.strip()}", file=sys.stderr)
    return result.stdout


def cmd_status():
    """显示 VPS 服务、端口、磁盘、内存状态。"""
    script = textwrap.dedent("""\
        echo '=== Services ==='
        systemctl list-units --type=service --state=running --no-pager | grep -E 'nginx|oauth|marzban|docker'
        echo
        echo '=== Key Ports ==='
        ss -tlnp | grep -E '8443|9100|8000|7891|443|1080' | sort -t: -k2 -n
        echo
        echo '=== Disk ==='
        df -h /
        echo
        echo '=== Memory ==='
        free -h
        echo
        echo '=== Docker ==='
        docker ps --format 'table {{.Names}}\\t{{.Status}}\\t{{.Ports}}' 2>/dev/null || echo 'Docker not running'
    """)
    print(ssh_run(script, timeout=15))


def cmd_logs(service: str, lines: int = 30):
    """查看服务日志。"""
    print(ssh_run(f"journalctl -u {service} --no-pager -n {lines}", timeout=10))


def cmd_nginx_add(subdomain: str, port: int):
    """生成并部署 nginx 反向代理配置。"""
    hostname = subdomain if "." in subdomain else f"{subdomain}.tianlizeng.cloud"

    config = textwrap.dedent(f"""\
        server {{
            listen 8443 ssl http2;
            server_name {hostname};

            ssl_certificate     /etc/nginx/ssl/origin.pem;
            ssl_certificate_key /etc/nginx/ssl/origin-key.pem;

            location / {{
                proxy_pass http://127.0.0.1:{port};
                proxy_set_header Host $host;
                proxy_set_header X-Real-IP $remote_addr;
                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                proxy_set_header X-Forwarded-Proto $scheme;
                proxy_http_version 1.1;
                proxy_set_header Upgrade $http_upgrade;
                proxy_set_header Connection "upgrade";
                proxy_read_timeout 86400;
            }}
        }}
    """)

    conf_name = hostname.replace(".", "_")
    remote_path = f"/etc/nginx/sites-available/{conf_name}"

    # Upload config
    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", suffix=".conf", delete=False) as f:
        f.write(config)
        tmp = f.name

    subprocess.run(["scp", tmp, f"{VPS}:{remote_path}"], check=True)
    os.unlink(tmp)

    # Enable and reload
    cmds = f"""
        ln -sf {remote_path} /etc/nginx/sites-enabled/{conf_name}
        nginx -t && systemctl reload nginx
    """
    output = ssh_run(cmds)
    print(output)
    print(f"✓ Nginx reverse proxy: {hostname} → localhost:{port}")
    print(f"\n下一步: 用 cf_api.py 添加 DNS 和 Origin Rule:")
    print(f"  python3 cf_api.py dns add {subdomain}")
    print(f"  python3 cf_api.py origin-rules add {hostname} 8443")


def main():
    parser = argparse.ArgumentParser(description="VPS SSH management tool")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("status", help="Show VPS status overview")

    logs_p = sub.add_parser("logs", help="Tail service logs")
    logs_p.add_argument("service", help="Systemd service name")
    logs_p.add_argument("-n", "--lines", type=int, default=30, help="Number of lines")

    nginx_p = sub.add_parser("nginx-add", help="Add nginx reverse proxy for a subdomain")
    nginx_p.add_argument("subdomain", help="Subdomain or full hostname")
    nginx_p.add_argument("port", type=int, help="Backend port on localhost")

    args = parser.parse_args()

    if args.command == "status":
        cmd_status()
    elif args.command == "logs":
        cmd_logs(args.service, args.lines)
    elif args.command == "nginx-add":
        cmd_nginx_add(args.subdomain, args.port)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
