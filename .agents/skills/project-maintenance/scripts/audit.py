#!/usr/bin/env python3
"""Read-only Git/REST inventory. Only the explicitly requested receipt is written."""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import subprocess
import tempfile

REPOSITORY = "OpenCoven/psyche-research"


def command(args, cwd):
    try:
        result = subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.TimeoutExpired):
        raise RuntimeError(f"{args[0]} unavailable or timed out") from None
    if result.returncode:
        # Never retain raw CLI errors, which can contain URLs or credential material.
        raise RuntimeError(f"{args[0]} exited {result.returncode}")
    return result.stdout


def worktrees(raw):
    trees = []
    for block in raw.rstrip("\0").split("\0\0"):
        fields = {}
        for field in block.split("\0"):
            key, _, value = field.partition(" ")
            if key:
                fields[key] = value or True
        if "worktree" in fields:
            trees.append(fields)
    return trees


def local_inventory(root):
    data = {"head": command(["git", "rev-parse", "HEAD"], root).strip(),
            "branch": command(["git", "branch", "--show-current"], root).strip(),
            "worktrees": [], "branches": []}
    for tree in worktrees(command(["git", "worktree", "list", "--porcelain", "-z"], root)):
        item = {k: tree[k] for k in ("worktree", "HEAD", "branch", "detached", "locked", "prunable") if k in tree}
        item["disposition"] = "retain: owner release and deletion authority unverified"
        try:
            status = command(["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"], tree["worktree"])
            item["dirty"] = bool(status)
            # Paths only, never diffs or ignored application/private data.
            item["status"] = status.split("\0") if status else []
        except RuntimeError as exc:
            item["dirty"] = None
            item["error"] = str(exc)
        data["worktrees"].append(item)
    for line in command(["git", "for-each-ref", "--format=%(refname:short) %(objectname)", "refs/heads"], root).splitlines():
        name, sha = line.rsplit(" ", 1)
        data["branches"].append({"name": name, "sha": sha})
    return data


def api(root, path):
    return json.loads(command(["gh", "api", f"repos/{REPOSITORY}/{path}"], root))


def pages(root, path, field=None):
    """Paginate collections including check-runs; a failed page invalidates the collection."""
    values = []
    for page in range(1, 1001):
        delimiter = "&" if "?" in path else "?"
        result = api(root, f"{path}{delimiter}per_page=100&page={page}")
        batch = result[field] if field else result
        if not isinstance(batch, list):
            raise ValueError("Expected a REST collection")
        values.extend(batch)
        if len(batch) < 100:
            return values
    raise RuntimeError("REST pagination bound exceeded; inventory incomplete")


def remote_inventory(root):
    data = {"complete": True, "errors": [], "repository": REPOSITORY}

    def read(key, action):
        try:
            data[key] = action()
        except (RuntimeError, ValueError, KeyError, TypeError):
            data["complete"] = False
            data["errors"].append({"collection": key, "error": "REST read failed; refresh through connected REST tool"})

    read("main", lambda: {k: v for k, v in api(root, "branches/main").items() if k in ("name", "protected", "commit")})
    if "main" in data:
        data["main"] = {"name": data["main"]["name"], "protected": data["main"]["protected"], "sha": data["main"]["commit"]["sha"]}
    read("issues", lambda: [{"number": i["number"], "title": i["title"], "updated_at": i["updated_at"],
                            "labels": [x["name"] for x in i["labels"]], "milestone": (i["milestone"] or {}).get("title"),
                            "assignees": [x["login"] for x in i["assignees"]]}
                           for i in pages(root, "issues?state=open") if "pull_request" not in i])
    read("prs", lambda: [{"number": p["number"], "title": p["title"], "head": p["head"]["sha"],
                         "branch": p["head"]["ref"], "base": p["base"]["ref"], "draft": p["draft"]}
                        for p in pages(root, "pulls?state=open")])
    read("rulesets", lambda: [{"id": r["id"], "name": r["name"], "enforcement": r["enforcement"]} for r in pages(root, "rulesets")])
    read("runs_sample", lambda: [{k: r[k] for k in ("id", "head_sha", "status", "conclusion", "html_url")}
                                for r in api(root, "actions/runs?per_page=30")["workflow_runs"]])
    heads = {p["head"] for p in data.get("prs", [])}
    if "main" in data:
        heads.add(data["main"]["sha"])
    for sha in sorted(heads):
        read("checks:" + sha, lambda sha=sha: [{k: c[k] for k in ("name", "status", "conclusion", "head_sha", "details_url")}
                                              for c in pages(root, f"commits/{sha}/check-runs", "check_runs")])
        read("statuses:" + sha, lambda sha=sha: [{k: s[k] for k in ("context", "state", "target_url")}
                                                for s in pages(root, f"commits/{sha}/statuses")])
    return data


def write_receipt(path, data):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, temporary = tempfile.mkstemp(prefix=".audit-", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as stream:
            json.dump(data, stream, indent=2)
            stream.write("\n")
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def summary(data):
    remote = data["remote"]
    lines = ["# Agent maintenance inventory", "", f"Revision: `{data['local']['head']}`. Collected: {data['collected_at']}.", "",
             f"Local worktrees: {len(data['local']['worktrees'])}; automatic deletions: 0.", ""]
    if remote.get("skipped"):
        lines.append("Remote reads explicitly skipped; this is local evidence only.")
    else:
        issue_count = len(remote["issues"]) if "issues" in remote else "unknown"
        pr_count = len(remote["prs"]) if "prs" in remote else "unknown"
        lines.append(f"Remote inventory complete: {remote['complete']}. Open issues: {issue_count}; open PRs: {pr_count}.")
        if not remote["complete"]:
            lines.extend(["", "Remote inventory is incomplete. Missing collections require a connected REST refresh; counts above are partial."])
        for error in remote.get("errors", []):
            lines.append(f"- Missing: {error['collection']}")
        if "main" in remote:
            lines.extend(["", f"Main: `{remote['main']['sha']}`; branch protected: {remote['main']['protected']}."])
        if "issues" in remote:
            issues = remote["issues"]
            lines.extend(["", f"Issues missing labels: {sum(not i['labels'] for i in issues)}; missing milestone: {sum(not i['milestone'] for i in issues)}; unassigned: {sum(not i['assignees'] for i in issues)}."])
        if remote.get("prs"):
            lines.extend(["", "| PR | Head | Draft | Check runs | Commit statuses |", "| --- | --- | --- | --- | --- |"])
            for pr in remote["prs"]:
                checks = remote.get("checks:" + pr["head"])
                statuses = remote.get("statuses:" + pr["head"])
                check_state = "unknown" if checks is None else f"{len(checks)} total, {sum(c['status'] != 'completed' for c in checks)} pending, {sum(c['conclusion'] in ('failure', 'timed_out', 'cancelled', 'action_required', 'startup_failure', 'stale') for c in checks)} need review"
                status_state = "unknown" if statuses is None else f"{len(statuses)} records; inspect receipt for contexts"
                lines.append(f"| #{pr['number']} | `{pr['head'][:12]}` | {pr['draft']} | {check_state} | {status_state} |")
    lines.extend(["", "Apply project-maintenance and worktree-prune to interpret the receipt. This collector does not change issues, refs, application data or deployments.", ""])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--local-only", action="store_true")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args()
    root = Path(command(["git", "rev-parse", "--show-toplevel"], Path.cwd()).strip())
    data = {"schema": 1, "collected_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "local": local_inventory(root), "remote": {"skipped": True} if args.local_only else remote_inventory(root)}
    write_receipt(args.output, data)
    rendered = summary(data)
    print(rendered)
    if args.summary and os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as stream:
            stream.write(rendered)
    return 0 if args.local_only or data["remote"]["complete"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
