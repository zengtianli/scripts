#!/usr/bin/env python3
"""Typeless 批量加词脚本

用法:
    # 从文件导入（一行一个词）
    python3 typeless_batch_add.py words.txt

    # 直接传入词语
    python3 typeless_batch_add.py --words "Claude,Anthropic,LangChain,RAG"

    # 查看当前字典
    python3 typeless_batch_add.py --list

Token 获取: 脚本会自动通过 CDP 从运行中的 Typeless 获取 token。
需要先用调试模式启动 Typeless:
    /Applications/Typeless.app/Contents/MacOS/Typeless --remote-debugging-port=9222 &
"""

import argparse
import json
import os
import sys
import time
import urllib.request

# 绕过本地代理，确保 CDP 连接和 API 请求不被拦截
os.environ.setdefault("no_proxy", "127.0.0.1,localhost")

API_BASE = "https://api.typeless.com"
CDP_PORT = 9222


def get_token_from_cdp():
    """通过 CDP 从运行中的 Typeless 获取 token"""
    try:
        targets = json.loads(
            urllib.request.urlopen(f"http://127.0.0.1:{CDP_PORT}/json/list").read()
        )
    except Exception:
        print("错误: 无法连接 Typeless 调试端口。请先用调试模式启动:")
        print("  /Applications/Typeless.app/Contents/MacOS/Typeless --remote-debugging-port=9222 &")
        sys.exit(1)

    hub = next((t for t in targets if t.get("title") == "Hub"), None)
    if not hub:
        print("错误: 找不到 Typeless Hub 窗口")
        sys.exit(1)

    import asyncio
    try:
        import websockets
    except ImportError:
        print("安装 websockets...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "websockets", "-q"])
        import websockets

    async def _get():
        async with websockets.connect(hub["webSocketDebuggerUrl"]) as ws:
            await ws.send(json.dumps({
                "id": 1,
                "method": "Runtime.evaluate",
                "params": {
                    "expression": "window.ipcRenderer.invoke('user:get-current').then(r => JSON.stringify(r))",
                    "awaitPromise": True,
                    "returnByValue": True,
                },
            }))
            resp = json.loads(await ws.recv())
            data = json.loads(resp["result"]["result"]["value"])
            return data["refresh_token"]

    return asyncio.run(_get())


def api_request(method, path, token, data=None, params=None):
    """发送 API 请求"""
    url = f"{API_BASE}{path}"
    if params:
        url += "?" + "&".join(f"{k}={v}" for k, v in params.items())

    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("User-Agent", "Typeless/1.0")
    if data:
        req.add_header("Content-Type", "application/json")

    resp = urllib.request.urlopen(req)
    return json.loads(resp.read())


def list_words(token):
    """列出当前字典所有词"""
    all_words = []
    offset = 0
    size = 150
    while True:
        result = api_request("GET", "/user/dictionary/list", token,
                             params={"size": str(size), "offset": str(offset)})
        words = result.get("data", {}).get("words", [])
        all_words.extend(words)
        total = result.get("data", {}).get("total_count", 0)
        if len(all_words) >= total or not words:
            break
        offset += size
    return all_words


def add_word(token, term):
    """添加单个词"""
    return api_request("POST", "/user/dictionary/add", token, data={"term": term})


def delete_word(token, term):
    """按词名删除（先查 ID 再删）"""
    all_words = list_words(token)
    match = next((w for w in all_words if w["term"] == term), None)
    if not match:
        return {"status": "NOT_FOUND", "msg": f"'{term}' not found in dictionary"}
    return api_request("POST", "/user/dictionary/delete", token,
                       data={"user_dictionary_id": match["user_dictionary_id"]})


def batch_add(token, words):
    """批量添加词语"""
    # 获取已有词，避免重复
    existing = {w["term"].lower() for w in list_words(token)}
    new_words = [w for w in words if w.lower() not in existing]
    skipped = len(words) - len(new_words)

    if skipped:
        print(f"跳过 {skipped} 个已存在的词")

    if not new_words:
        print("没有新词需要添加")
        return

    print(f"开始添加 {len(new_words)} 个新词...")
    success = 0
    failed = []

    for i, word in enumerate(new_words, 1):
        try:
            result = add_word(token, word)
            if result.get("status") == "OK":
                success += 1
                print(f"  [{i}/{len(new_words)}] + {word}")
            else:
                failed.append((word, result.get("msg", "unknown error")))
                print(f"  [{i}/{len(new_words)}] x {word} - {result.get('msg')}")
        except Exception as e:
            failed.append((word, str(e)))
            print(f"  [{i}/{len(new_words)}] x {word} - {e}")
        # 避免 rate limit
        if i % 10 == 0:
            time.sleep(0.5)

    print(f"\n完成: 成功 {success}, 失败 {len(failed)}")
    if failed:
        print("失败列表:")
        for word, err in failed:
            print(f"  - {word}: {err}")


def main():
    parser = argparse.ArgumentParser(description="Typeless 批量加词")
    parser.add_argument("file", nargs="?", help="词表文件（一行一个词）")
    parser.add_argument("--words", "-w", help="逗号分隔的词语列表")
    parser.add_argument("--list", "-l", action="store_true", help="列出当前字典")
    parser.add_argument("--delete", "-d", help="逗号分隔的要删除的词语")
    args = parser.parse_args()

    token = get_token_from_cdp()
    print("Token 获取成功\n")

    if args.delete:
        for term in args.delete.split(","):
            term = term.strip()
            if not term:
                continue
            try:
                result = delete_word(token, term)
                print(f"  删除: {term} - {result.get('msg', 'ok')}")
            except Exception as e:
                print(f"  删除失败: {term} - {e}")
        return

    if args.list:
        words = list_words(token)
        print(f"字典共 {len(words)} 个词:")
        for w in words:
            source = "自动" if w.get("auto") else "手动"
            print(f"  - {w['term']} ({source})")
        return

    if args.words:
        word_list = [w.strip() for w in args.words.split(",") if w.strip()]
    elif args.file:
        with open(args.file) as f:
            word_list = []
            for line in f:
                line = line.strip()
                # 跳过空行、Markdown 标题、引用块、分隔线、HTML 注释
                if not line or line.startswith("#") or line.startswith(">") or line == "---":
                    continue
                word_list.append(line)
    else:
        parser.print_help()
        return

    if not word_list:
        print("词表为空")
        return

    print(f"准备添加 {len(word_list)} 个词: {', '.join(word_list[:10])}{'...' if len(word_list) > 10 else ''}")
    batch_add(token, word_list)


if __name__ == "__main__":
    main()
