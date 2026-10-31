"""Ship the daily-refreshed live models and data to a deployed API without touching git.

The daily job retrains the live models, which changes ~25 MB of model files each time;
committing them daily would bloat the repository. Instead the job packs them into one
``live_bundle.tar.gz`` and uploads it to a public Supabase Storage bucket; the API
downloads it when it starts and whenever it has changed (see ``src/api/refresher.py``).

Contents: ``models/live/``, ``data/processed/live_city_day.csv``,
``data/processed/live_nowcast.json`` and ``data/processed/live_forecasts.json`` (nothing
else is ever extracted).

Environment:
    LIVE_BUNDLE_URL        public download URL (API side), e.g.
                           https://<project>.supabase.co/storage/v1/object/public/live/live_bundle.tar.gz
    SUPABASE_URL           project URL (job side, already used by the API)
    SUPABASE_SERVICE_ROLE_KEY   service-role key, only in the job's secrets, never in the API
    LIVE_BUNDLE_BUCKET     bucket name, default ``live``

Usage::

    python -m src.live_bundle pack            # write data/live_bundle.tar.gz
    python -m src.live_bundle upload          # pack and upload
    python -m src.live_bundle sync            # download and install if the URL's file changed
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tarfile
import tempfile
from pathlib import Path

import httpx

from src.data_loader import PROJECT_ROOT

BUNDLE_PATH = PROJECT_ROOT / "data" / "live_bundle.tar.gz"
ETAG_PATH = PROJECT_ROOT / "data" / "cache" / "live_bundle_etag.json"
OBJECT_NAME = "live_bundle.tar.gz"
# Paths (relative to the project root) a bundle may contain.
CONTENT = ("models/live", "data/processed/live_city_day.csv", "data/processed/live_nowcast.json",
           "data/processed/live_forecasts.json")


def pack(out: Path = BUNDLE_PATH, root: Path = PROJECT_ROOT) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(out, "w:gz") as tar:
        for rel in CONTENT:
            if (root / rel).exists():
                tar.add(root / rel, arcname=rel)
    return out


def _allowed(name: str) -> bool:
    parts = Path(name).parts
    return (not Path(name).is_absolute() and ".." not in parts
            and any(name == c or name.startswith(c + "/") for c in CONTENT))


def install(bundle: Path, root: Path = PROJECT_ROOT) -> list[str]:
    """Extract a bundle over ``root``. Only the expected paths are accepted (a bundle with any
    other path is refused whole); each folder is replaced in one move, so the API never reads
    a half-written ``models/live``. Returns the installed top-level paths."""
    with tarfile.open(bundle, "r:gz") as tar:
        members = tar.getmembers()
        bad = [m.name for m in members if not _allowed(m.name) or not (m.isfile() or m.isdir())]
        if bad:
            raise ValueError(f"Refusing bundle with unexpected paths: {bad[:3]}")
        with tempfile.TemporaryDirectory(dir=root) as tmp:
            tar.extractall(tmp, filter="data")
            done = []
            for rel in CONTENT:
                src, dst = Path(tmp) / rel, root / rel
                if not src.exists():
                    continue
                dst.parent.mkdir(parents=True, exist_ok=True)
                if src.is_dir():
                    old = dst.with_name(dst.name + ".old")
                    if old.exists():
                        shutil.rmtree(old)
                    if dst.exists():
                        dst.rename(old)
                    shutil.move(str(src), str(dst))
                    shutil.rmtree(old, ignore_errors=True)
                else:
                    shutil.move(str(src), str(dst))
                done.append(rel)
    return done


def upload(bundle: Path = BUNDLE_PATH) -> str:
    """Upload to the Supabase Storage bucket (replacing the previous file); returns the public URL."""
    base, key = os.environ["SUPABASE_URL"].rstrip("/"), os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    bucket = os.getenv("LIVE_BUNDLE_BUCKET", "live")
    r = httpx.post(f"{base}/storage/v1/object/{bucket}/{OBJECT_NAME}", content=bundle.read_bytes(), timeout=300,
                   headers={"Authorization": f"Bearer {key}", "apikey": key, "x-upsert": "true",
                            "Content-Type": "application/gzip"})
    r.raise_for_status()
    return f"{base}/storage/v1/object/public/{bucket}/{OBJECT_NAME}"


def sync(url: str | None = None, root: Path = PROJECT_ROOT) -> bool:
    """Download the bundle and install it if the file at ``url`` changed since the last sync
    (ETag / Last-Modified). Returns True if new files were installed."""
    url = url or os.getenv("LIVE_BUNDLE_URL")
    if not url:
        return False
    seen = json.loads(ETAG_PATH.read_text(encoding="utf-8")) if ETAG_PATH.exists() else {}
    head = httpx.head(url, timeout=30, follow_redirects=True)
    head.raise_for_status()
    tag = head.headers.get("etag") or head.headers.get("last-modified") or head.headers.get("content-length")
    if tag and seen.get(url) == tag:
        return False
    with tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False) as f:
        tmp = Path(f.name)
    try:
        with httpx.stream("GET", url, timeout=300, follow_redirects=True) as r:
            r.raise_for_status()
            with tmp.open("wb") as out:
                for chunk in r.iter_bytes():
                    out.write(chunk)
        install(tmp, root)
    finally:
        tmp.unlink(missing_ok=True)
    ETAG_PATH.parent.mkdir(parents=True, exist_ok=True)
    ETAG_PATH.write_text(json.dumps({**seen, url: tag}), encoding="utf-8")
    return True


def main() -> None:
    cmd = sys.argv[1] if len(sys.argv) > 1 else "pack"
    if cmd == "pack":
        print(f"Wrote {pack()} ({BUNDLE_PATH.stat().st_size / 1e6:.1f} MB)")
    elif cmd == "upload":
        pack()
        print(f"Uploaded {BUNDLE_PATH.stat().st_size / 1e6:.1f} MB to {upload()}")
    elif cmd == "sync":
        if not os.getenv("LIVE_BUNDLE_URL"):
            sys.exit("LIVE_BUNDLE_URL is not set")
        print("Installed a newer bundle" if sync() else "Bundle unchanged")
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
