#!/usr/bin/env python3
"""Hourly autobump for dalisoft/tap.

Checks upstream for new versions (read-only HTTP, never executes install scripts):
  - command-code : npm registry (registry.npmjs.org/command-code/latest)
  - cua-driver   : GitHub releases tag cua-driver-rs-v* (stable, excludes nightly/pre-release)
  - lume         : GitHub releases tag lume-v* + release-manifest.json sha256
  - reason-language-server : GitHub releases (deprecated upstream, still checked)

On update: rewrites Formula/*.rb in place (version + url + sha256 per OS/arch),
prints a summary. The workflow opens a PR if files changed.

Usage:
  python3 .github/scripts/autobump.py [--check-only]

Env:
  GITHUB_TOKEN (optional, raises GitHub API rate limit)
"""
import hashlib
import json
import os
import re
import sys
import urllib.request

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
FORMULA_DIR = os.path.join(ROOT, "Formula")

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")


def http_json(url):
    headers = {"User-Agent": "dalisoft-tap-autobump/1.0", "Accept": "application/json"}
    if "api.github.com" in url:
        headers["Accept"] = "application/vnd.github+json"
    req = urllib.request.Request(url, headers=headers)
    if GITHUB_TOKEN and "api.github.com" in url:
        req.add_header("Authorization", f"Bearer {GITHUB_TOKEN}")
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())


def http_text(url):
    req = urllib.request.Request(url, headers={"User-Agent": "dalisoft-tap-autobump/1.0"})
    if GITHUB_TOKEN and "api.github.com" in url:
        req.add_header("Authorization", f"Bearer {GITHUB_TOKEN}")
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode()


def sha256_of_url(url):
    """Download (stream) and hash. Never executes the payload."""
    req = urllib.request.Request(url, headers={"User-Agent": "dalisoft-tap-autobump/1.0"})
    h = hashlib.sha256()
    with urllib.request.urlopen(req, timeout=300) as r:
        while True:
            chunk = r.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def read_formula(name):
    with open(os.path.join(FORMULA_DIR, f"{name}.rb")) as f:
        return f.read()


def write_formula(name, content):
    with open(os.path.join(FORMULA_DIR, f"{name}.rb"), "w") as f:
        f.write(content)


def current_version(content):
    m = re.search(r'^\s*version\s+"([^"]+)"', content, re.M)
    return m.group(1) if m else None


def semver_key(v):
    return tuple(int(x) for x in re.findall(r"\d+", v)[:3])


def github_releases(repo):
    out, page = [], 1
    while page <= 3:
        data = http_json(f"https://api.github.com/repos/{repo}/releases?per_page=100&page={page}")
        if not data:
            break
        out.extend(data)
        if len(data) < 100:
            break
        page += 1
    return out


def bump_command_code():
    content = read_formula("command-code")
    cur = current_version(content)
    meta = http_json("https://registry.npmjs.org/command-code/latest")
    latest = meta["version"]
    if semver_key(latest) <= semver_key(cur):
        return None
    tarball = meta["dist"]["tarball"]
    digest = sha256_of_url(tarball)
    new = content
    new = re.sub(r'^\s*url\s+"https://registry\.npmjs\.org/command-code/[^"]+"',
                 f'  url "{tarball}"', new, count=1, flags=re.M)
    new = re.sub(r'^\s*version\s+"[^"]+"', f'  version "{latest}"', new, count=1, flags=re.M)
    new = re.sub(r'^\s*sha256\s+"[0-9a-f]{64}"', f'  sha256 "{digest}"', new, count=1, flags=re.M)
    if new != content:
        write_formula("command-code", new)
        return f"command-code {cur} -> {latest} sha256:{digest[:12]}"
    return None


def bump_cua_driver():
    content = read_formula("cua-driver")
    cur = current_version(content)
    best = None
    for r in github_releases("trycua/cua"):
        if r.get("draft") or r.get("prerelease"):
            continue
        tag = r.get("tag_name", "")
        m = re.match(r"^cua-driver-rs-v(\d+\.\d+\.\d+)$", tag)
        if not m:
            continue
        ver = m.group(1)
        if best is None or semver_key(ver) > semver_key(best[0]):
            best = (ver, tag)
    if not best:
        return None
    latest, tag = best
    if semver_key(latest) <= semver_key(cur):
        return None
    targets = {
        "darwin-arm64": None, "darwin-x86_64": None,
        "linux-arm64": None, "linux-x86_64": None,
    }
    checks = http_text(f"https://github.com/trycua/cua/releases/download/{tag}/checksums.txt")
    for line in checks.splitlines():
        m = re.match(r"^([0-9a-f]{64})\s+(\S+)", line.strip())
        if not m:
            continue
        digest, fname = m.groups()
        mm = re.match(rf"^cua-driver-rs-{re.escape(latest)}-(darwin-arm64|darwin-x86_64|linux-arm64|linux-x86_64)\.tar\.gz$", fname)
        if mm:
            targets[mm.group(1)] = digest
    if any(v is None for v in targets.values()):
        print(f"cua-driver {latest}: missing checksums for {targets}", file=sys.stderr)
        return None
    new = content
    new = re.sub(r'^\s*version\s+"[^"]+"', f'  version "{latest}"', new, count=1, flags=re.M)
    for target, digest in targets.items():
        url = f"https://github.com/trycua/cua/releases/download/{tag}/cua-driver-rs-{latest}-{target}.tar.gz"
        # Replace each per-arch url+sha256 pair (url line then sha256 line).
        pat = re.compile(
            r'(url\s+")https://github\.com/trycua/cua/releases/download/cua-driver-rs-v[^"]+/cua-driver-rs-'
            + re.escape(cur) + r"-" + re.escape(target) + r'\.tar\.gz"\n(\s*sha256\s+")[0-9a-f]{64}(")',
        )
        new, n = pat.subn(rf"\g<1>{url}\g<2>{digest}\g<3>", new)
        if n == 0:
            print(f"cua-driver: pattern not matched for {target}", file=sys.stderr)
            return None
    # Fix tag in remaining URLs if version appears elsewhere (defensive: only within cua-driver-rs- URLs).
    if new != content:
        write_formula("cua-driver", new)
        return f"cua-driver {cur} -> {latest}"
    return None


def bump_lume():
    content = read_formula("lume")
    cur = current_version(content)
    best = None
    for r in github_releases("trycua/cua"):
        if r.get("draft") or r.get("prerelease"):
            continue
        tag = r.get("tag_name", "")
        m = re.match(r"^lume-v(\d+\.\d+\.\d+)$", tag)
        if not m:
            continue
        ver = m.group(1)
        if best is None or semver_key(ver) > semver_key(best[0]):
            best = (ver, tag)
    if not best:
        return None
    latest, tag = best
    if semver_key(latest) <= semver_key(cur):
        return None
    manifest = http_json(f"https://github.com/trycua/cua/releases/download/{tag}/release-manifest.json")
    digest = None
    for a in manifest.get("assets", []):
        if a.get("name", "").endswith("darwin-arm64.tar.gz"):
            digest = a.get("sha256")
            break
    if not digest:
        print(f"lume {latest}: no darwin-arm64 sha in manifest", file=sys.stderr)
        return None
    url = f"https://github.com/trycua/cua/releases/download/{tag}/lume-{latest}-darwin-arm64.tar.gz"
    new = content
    new = re.sub(r'^\s*url\s+"https://github\.com/trycua/cua/releases/download/lume-v[^"]+"',
                 f'  url "{url}"', new, count=1, flags=re.M)
    new = re.sub(r'^\s*version\s+"[^"]+"', f'  version "{latest}"', new, count=1, flags=re.M)
    new = re.sub(r'^\s*sha256\s+"[0-9a-f]{64}"', f'  sha256 "{digest}"', new, count=1, flags=re.M)
    if new != content:
        write_formula("lume", new)
        return f"lume {cur} -> {latest} sha256:{digest[:12]}"
    return None


def bump_reason_language_server():
    content = read_formula("reason-language-server")
    cur = current_version(content)
    best = None
    for r in github_releases("jaredly/reason-language-server"):
        if r.get("draft") or r.get("prerelease"):
            continue
        tag = r.get("tag_name", "")
        m = re.match(r"^v?(\d+\.\d+\.\d+)$", tag)
        if not m:
            continue
        ver = m.group(1)
        if best is None or semver_key(ver) > semver_key(best[0]):
            best = (ver, tag)
    if not best:
        return None
    latest, tag = best
    if semver_key(latest) <= semver_key(cur):
        return None
    mac_url = f"https://github.com/jaredly/reason-language-server/releases/download/{tag}/rls-macos.zip"
    linux_url = f"https://github.com/jaredly/reason-language-server/releases/download/{tag}/rls-linux.zip"
    mac_sha = sha256_of_url(mac_url)
    linux_sha = sha256_of_url(linux_url)
    new = content
    new = re.sub(r'^\s*version\s+"[^"]+"', f'  version "{latest}"', new, count=1, flags=re.M)
    new = re.sub(r"https://github\.com/jaredly/reason-language-server/releases/download/[^/]+/rls-macos\.zip",
                 mac_url, new)
    new = re.sub(r"https://github\.com/jaredly/reason-language-server/releases/download/[^/]+/rls-linux\.zip",
                 linux_url, new)
    # Replace sha256s positionally: first two mac occurrences, next two linux.
    # Simpler: replace all mac-sha and linux-sha by context — here assets differ per OS,
    # so replace old mac digest wherever it appears and old linux digest likewise.
    # Extract old digests from original content in order: mac, mac, linux, linux.
    digests = re.findall(r'^\s*sha256\s+"([0-9a-f]{64})"', content, flags=re.M)
    if len(digests) >= 4:
        new = new.replace(digests[0], mac_sha).replace(digests[1], mac_sha)
        # Recompute remaining old linux digest (digests[2]==digests[3] normally).
        new = new.replace(digests[2], linux_sha).replace(digests[3], linux_sha)
    else:
        print("rls: unexpected sha block layout", file=sys.stderr)
        return None
    if new != content:
        write_formula("reason-language-server", new)
        return f"reason-language-server {cur} -> {latest}"
    return None


def main():
    check_only = "--check-only" in sys.argv
    results = []
    for fn in (bump_command_code, bump_cua_driver, bump_lume, bump_reason_language_server):
        try:
            r = fn()
        except Exception as e:
            print(f"{fn.__name__} failed: {e}", file=sys.stderr)
            continue
        if r:
            results.append(r)
            print(r)
    if not results:
        print("autobump: no updates")
    if check_only and results:
        sys.exit(2)


if __name__ == "__main__":
    main()
