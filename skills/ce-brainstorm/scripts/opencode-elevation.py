#!/usr/bin/env python3
"""Read-only reasoning elevation through the OpenCode V2 session API.

Run under peer-job-runner.py. All provider work belongs to the newly created
session; interrupt it on failure or termination so server-side work cannot
outlive the worker. Only changed message content counts as progress.
"""
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time


def model_ref(value):
    match = re.fullmatch(r"([^/#\s]+)/([^#\s]+)(?:#([^#\s]+))?", value)
    if not match:
        raise ValueError("OpenCode model must be provider/model#variant (variant optional)")
    ref = {"providerID": match[1], "id": match[2]}
    if match[3]:
        ref["variant"] = match[3]
    return ref


def api(method, path, cwd, body=None):
    argv = ["opencode", "api", method, path]
    if body is not None:
        argv += ["--data", json.dumps(body)]
    proc = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, timeout=30)
    if proc.returncode:
        raise RuntimeError(proc.stderr[-800:] or f"OpenCode API exited {proc.returncode}")
    return json.loads(proc.stdout) if proc.stdout.strip() else {}


def classify_receipt(requested, served):
    # An omitted variant leaves the server default unconstrained. An explicit
    # variant is part of the requested identity and must match exactly.
    if not isinstance(served, dict) or not served.get("providerID") or not served.get("id"):
        return "unverified"
    return "matched" if all(served.get(key) == value for key, value in requested.items()) else "mismatch"


def confirm_model(ref, cwd):
    """Reject unavailable identities before creating any provider-capable session."""
    catalog = api("get", "/api/model", cwd)
    for model in catalog.get("data", []):
        if model.get("providerID") != ref["providerID"] or model.get("id") != ref["id"]:
            continue
        if not model.get("enabled"):
            raise ValueError("requested OpenCode model is disabled")
        if "variant" in ref and ref["variant"] not in {
            variant["id"] for variant in model.get("variants", [])
        }:
            raise ValueError(f"requested OpenCode variant is unavailable: {ref['variant']}")
        return
    raise ValueError(f"requested OpenCode model is unavailable: {ref['providerID']}/{ref['id']}")


def run(model, prompt_file, result_path):
    cwd = os.path.abspath(os.getcwd())
    session = None
    envelope = {"status": "failed", "requested_model": model}
    def terminate(signum, frame):
        raise InterruptedError(f"worker received signal {signum}")

    signal.signal(signal.SIGTERM, terminate)
    signal.signal(signal.SIGINT, terminate)
    try:
        ref = model_ref(model)
        confirm_model(ref, cwd)
        rules = [{"action": "*", "resource": "*", "effect": "deny"}]
        rules += [{"action": action, "resource": "*", "effect": "allow"}
                  for action in ("read", "glob", "grep", "webfetch", "websearch")]
        created = api("post", "/api/session", cwd, {
            "title": "Reasoning elevation", "model": ref,
            "location": {"directory": cwd}, "permissions": rules,
        })
        session = created["data"]["id"]
        if not re.fullmatch(r"ses[a-zA-Z0-9_-]+", session):
            raise RuntimeError("invalid OpenCode V2 session id")
        prompt = Path(prompt_file).read_text()
        api("post", f"/api/session/{session}/prompt", cwd, {"text": prompt})
        start = last_progress = time.monotonic()
        previous = None
        idle = float(os.environ.get("CE_ELEVATION_IDLE_SECS", "180"))
        hard = float(os.environ.get("CE_ELEVATION_HARD_SECS", "5400"))
        poll = float(os.environ.get("CE_ELEVATION_POLL_SECS", "5"))
        while True:
            page = api("get", f"/api/session/{session}/message?type=assistant&order=desc&limit=1", cwd)
            messages = page.get("data", [])
            current = json.dumps(messages, sort_keys=True)
            if messages and current != previous:
                print("[elevation] OpenCode message progress", flush=True)
                previous = current
                last_progress = time.monotonic()
            if messages:
                message = messages[0]
                if message.get("error"):
                    raise RuntimeError(json.dumps(message["error"])[:800])
                if message.get("time", {}).get("completed") and message.get("finish") != "tool-calls":
                    if message.get("finish") != "stop":
                        raise RuntimeError(f"incomplete OpenCode result: {message.get('finish')}")
                    output = "\n".join(part["text"] for part in message.get("content", [])
                                       if part.get("type") == "text")
                    if not output.strip():
                        raise RuntimeError("OpenCode returned no text")
                    served = message.get("model") or {}
                    receipt = classify_receipt(ref, served)
                    if receipt == "mismatch":
                        raise RuntimeError("OpenCode served a different provider, model, or requested variant")
                    served_name = f"{served.get('providerID', '')}/{served.get('id', '')}"
                    if served.get("variant"):
                        served_name += "#" + served["variant"]
                    envelope.update(status="ok", served_model=served_name,
                                    receipt=receipt, output=output)
                    break
            now = time.monotonic()
            if now - last_progress >= idle or now - start >= hard:
                raise TimeoutError("OpenCode elevation exceeded its idle or hard limit")
            time.sleep(max(0.1, poll))
    except Exception as exc:
        envelope.update(status="failed", evidence=str(exc)[:800])
    finally:
        if session:
            # A SIGKILL cannot be caught; the outer runner's longer grace and
            # matched hard cap leave this worker time to interrupt its session.
            signal.signal(signal.SIGTERM, signal.SIG_IGN)
            signal.signal(signal.SIGINT, signal.SIG_IGN)
            try:
                api("post", f"/api/session/{session}/interrupt", cwd)
            except Exception as exc:
                envelope.update(status="failed", evidence=f"session {session} interrupt failed: {exc}"[:800])
        target = Path(result_path)
        temporary = target.with_name(target.name + f".tmp.{os.getpid()}")
        temporary.write_text(json.dumps(envelope))
        temporary.replace(target)
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit("usage: opencode-elevation.py MODEL PROMPT_FILE RESULT_PATH")
    sys.exit(run(*sys.argv[1:]))
