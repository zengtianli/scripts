#!/usr/bin/env python3
"""统一 LLM 调用模块 — 支持 Anthropic (MMKG) 和 OpenAI (智谱) 格式。

用法:
    from tools.llm_client import chat

    # 自动选择可用 provider（按 default_order 顺序 fallback）
    response = chat("你是助手", "帮我分析这个文件")

    # 指定 provider
    response = chat("你是助手", "帮我分析", provider="zhipu")

    # 指定模型
    response = chat("你是助手", "帮我分析", model="glm-5")

也可直接运行测试:
    python3 llm_client.py                    # 用默认 provider
    python3 llm_client.py --provider zhipu   # 指定 provider
    python3 llm_client.py --provider mmkg    # 指定 provider
"""

import json
import os
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import yaml

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
_CONFIG_FILE = Path(__file__).parent / "llm_providers.yaml"
_config = None


def _load_config() -> dict:
    global _config
    if _config is None:
        with open(_CONFIG_FILE, encoding="utf-8") as f:
            _config = yaml.safe_load(f)
    return _config


def _get_provider_config(name: str) -> dict:
    cfg = _load_config()
    if name not in cfg["providers"]:
        raise ValueError(f"Unknown provider: {name}")
    return cfg["providers"][name]


# ---------------------------------------------------------------------------
# Anthropic API format (MMKG)
# ---------------------------------------------------------------------------
def _call_anthropic(
    system: str,
    message: str,
    provider_cfg: dict,
    model: str | None = None,
    max_tokens: int | None = None,
) -> str:
    """Call Anthropic Messages API."""
    base_url = provider_cfg.get("base_url") or os.environ.get(
        provider_cfg.get("base_url_env", ""), ""
    )
    api_key = provider_cfg.get("api_key") or os.environ.get(
        provider_cfg.get("api_key_env", ""), ""
    )
    if not base_url or not api_key:
        raise ConnectionError(
            f"Missing base_url or api_key for anthropic provider "
            f"(env: {provider_cfg.get('base_url_env')}, {provider_cfg.get('api_key_env')})"
        )

    url = f"{base_url.rstrip('/')}/v1/messages"
    payload = {
        "model": model or provider_cfg["model"],
        "max_tokens": max_tokens or provider_cfg.get("max_tokens", 4096),
        "system": system,
        "messages": [{"role": "user", "content": message}],
    }
    data = json.dumps(payload).encode("utf-8")
    headers = {
        "x-api-key": api_key,
        "content-type": "application/json",
        "anthropic-version": "2023-06-01",
        "user-agent": "llm-client/1.0",
    }

    timeout = provider_cfg.get("timeout", 120)
    max_retries = provider_cfg.get("max_retries", 3)

    for attempt in range(max_retries + 1):
        req = Request(url, data=data, headers=headers, method="POST")
        try:
            with urlopen(req, timeout=timeout) as resp:
                body = json.loads(resp.read().decode("utf-8"))
                # Skip thinking blocks, find text block
                for block in body.get("content", []):
                    if block.get("type") == "text":
                        return block["text"]
                # Fallback: return last block content
                return body["content"][-1].get("text", str(body["content"][-1]))
        except HTTPError as e:
            if e.code == 429 and attempt < max_retries:
                wait = 2**attempt
                print(f"  [{provider_cfg.get('_name', 'anthropic')}] Rate limited, retry in {wait}s...")
                time.sleep(wait)
                continue
            raise


# ---------------------------------------------------------------------------
# OpenAI API format (ZhiPu / DeepSeek / etc.)
# ---------------------------------------------------------------------------
def _call_openai(
    system: str,
    message: str,
    provider_cfg: dict,
    model: str | None = None,
    max_tokens: int | None = None,
) -> str:
    """Call OpenAI Chat Completions API."""
    base_url = provider_cfg.get("base_url") or os.environ.get(
        provider_cfg.get("base_url_env", ""), ""
    )
    api_key = provider_cfg.get("api_key") or os.environ.get(
        provider_cfg.get("api_key_env", ""), ""
    )
    if not base_url or not api_key:
        raise ConnectionError(f"Missing base_url or api_key for openai provider")

    url = f"{base_url.rstrip('/')}/chat/completions"
    payload = {
        "model": model or provider_cfg["model"],
        "max_tokens": max_tokens or provider_cfg.get("max_tokens", 4096),
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": message},
        ],
    }
    data = json.dumps(payload).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    timeout = provider_cfg.get("timeout", 120)
    max_retries = provider_cfg.get("max_retries", 2)

    for attempt in range(max_retries + 1):
        req = Request(url, data=data, headers=headers, method="POST")
        try:
            with urlopen(req, timeout=timeout) as resp:
                body = json.loads(resp.read().decode("utf-8"))
                return body["choices"][0]["message"]["content"]
        except HTTPError as e:
            if e.code == 429 and attempt < max_retries:
                wait = 2**attempt
                print(f"  [{provider_cfg.get('_name', 'openai')}] Rate limited, retry in {wait}s...")
                time.sleep(wait)
                continue
            raise


# ---------------------------------------------------------------------------
# Unified Interface
# ---------------------------------------------------------------------------
_CALLERS = {
    "anthropic": _call_anthropic,
    "openai": _call_openai,
}


def chat(
    system: str,
    message: str,
    provider: str | None = None,
    model: str | None = None,
    max_tokens: int | None = None,
) -> str:
    """Send a chat message and get a response.

    Auto-fallback across providers if the preferred one fails.

    Args:
        system: System prompt
        message: User message
        provider: Force a specific provider (skip fallback)
        model: Override model name
        max_tokens: Override max tokens

    Returns:
        Response text from the LLM
    """
    cfg = _load_config()

    if provider:
        # Use specified provider, no fallback
        providers = [provider]
    else:
        providers = cfg.get("default_order", list(cfg["providers"].keys()))

    last_error = None
    for pname in providers:
        pcfg = cfg["providers"].get(pname)
        if not pcfg:
            continue
        pcfg["_name"] = pname
        api_format = pcfg.get("api_format", "openai")
        caller = _CALLERS.get(api_format)
        if not caller:
            continue

        try:
            return caller(system, message, pcfg, model=model, max_tokens=max_tokens)
        except Exception as e:
            last_error = e
            print(f"  [{pname}] 调用失败: {e}，尝试下一个 provider...")
            continue

    raise ConnectionError(
        f"所有 provider 均失败。最后错误: {last_error}"
    )


# ---------------------------------------------------------------------------
# CLI test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="LLM Client 测试")
    parser.add_argument("--provider", help="指定 provider (mmkg/zhipu)")
    parser.add_argument("--model", help="指定模型")
    parser.add_argument("--message", default="你好，请用一句话介绍自己。", help="测试消息")
    args = parser.parse_args()

    print(f"测试 LLM 调用 (provider={args.provider or 'auto'})...")
    try:
        result = chat(
            system="你是一个测试助手。简短回复。",
            message=args.message,
            provider=args.provider,
            model=args.model,
        )
        print(f"响应: {result}")
    except Exception as e:
        print(f"失败: {e}", file=sys.stderr)
        sys.exit(1)
