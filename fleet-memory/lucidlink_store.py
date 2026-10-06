"""A LangGraph BaseStore over a LucidLink filespace: a namespace is a directory under
the root, a key is a "<key>.json" file in it, and updates take an exclusive lock on the
file. Search matches on fields only; semantic retrieval is LangMem's or Mem0's job on top.
"""

import json
import os
from collections.abc import Iterable
from contextlib import suppress
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import lucidlink
from langgraph.store.base import (
    BaseStore,
    GetOp,
    Item,
    ListNamespacesOp,
    Op,
    PutOp,
    Result,
    SearchItem,
    SearchOp,
)


def open_filespace(
    token_file: str | Path, filespace: str | None = None
) -> tuple[lucidlink.Client, lucidlink.Filespace]:
    """Log in with a service-account token from a file only its owner can read, and link a filespace by name."""
    filespace = filespace or os.environ.get("LUCIDLINK_FILESPACE")
    if not filespace:
        raise SystemExit("set LUCIDLINK_FILESPACE to the name of the filespace")
    path = Path(token_file).expanduser()
    if not path.is_file():
        raise SystemExit(f"no token file at {path}")
    if path.stat().st_mode & 0o077:
        raise SystemExit(f"{path} is readable by other users; run: chmod 600 {path}")
    client = lucidlink.Client()
    client.login(lucidlink.ServiceAccountCredentials(token=path.read_text().strip()))
    workspace = client.get_workspace(client.list_workspaces()[0].id)  # a token is tied to exactly one workspace
    return client, workspace.link_filespace(name=filespace)


class LucidLinkStore(BaseStore):
    def __init__(self, filespace: lucidlink.Filespace, root: str = "/memory"):
        self.filespace = filespace
        self.fs = filespace.fs
        self.root = root.rstrip("/")

    def _dir(self, namespace: tuple[str, ...]) -> str:
        return "/".join((self.root, *namespace))

    def _path(self, namespace: tuple[str, ...], key: str) -> str:
        return f"{self._dir(namespace)}/{key}.json"

    def _mkdirs(self, namespace: tuple[str, ...]) -> None:
        # an agent granted only /memory/shared can see /memory but may not create it
        dirs = [self.root]
        for part in namespace:
            dirs.append(f"{dirs[-1]}/{part}")
        for d in dirs:
            if not self.fs.dir_exists(d):
                with suppress(FileExistsError):
                    self.fs.create_dir(d)

    def _write(self, path: str, value: dict[str, Any], created_at: str, updated_at: str) -> None:
        doc = {"value": value, "created_at": created_at, "updated_at": updated_at}
        self.fs.write_file(path, json.dumps(doc, ensure_ascii=False).encode())

    def _get(self, namespace: tuple[str, ...], key: str) -> Item | None:
        try:
            doc = json.loads(self.fs.read_file(self._path(namespace, key)))
        except FileNotFoundError:
            return None
        return Item(
            value=doc["value"],
            key=key,
            namespace=namespace,
            created_at=datetime.fromisoformat(doc["created_at"]),
            updated_at=datetime.fromisoformat(doc["updated_at"]),
        )

    def _put(self, namespace: tuple[str, ...], key: str, value: dict[str, Any] | None) -> None:
        path = self._path(namespace, key)
        if value is None:
            with suppress(FileNotFoundError):
                self.fs.delete(path)
            return
        self._mkdirs(namespace)
        now = datetime.now(timezone.utc).isoformat()
        try:
            with self.fs.open(path, "r+b", lock_type="exclusive") as f:
                created_at = json.loads(f.read()).get("created_at", now)
                self._write(path, value, created_at, now)  # write_file, not f.write: the audit trail attributes it
        except FileNotFoundError:
            self._write(path, value, now, now)

    def _search(self, op: SearchOp) -> list[SearchItem]:
        try:
            entries = self.fs.read_dir(self._dir(op.namespace_prefix))
        except FileNotFoundError:
            return []
        wanted = op.filter or {}
        hits = []
        for entry in sorted(entries, key=lambda e: e.name):
            if entry.type != "file" or not entry.name.endswith(".json") or entry.name.startswith("."):
                continue
            item = self._get(op.namespace_prefix, entry.name[:-5])
            if item and all(item.value.get(k) == v for k, v in wanted.items()):
                hits.append(SearchItem(item.namespace, item.key, item.value, item.created_at, item.updated_at))
        return hits[op.offset : op.offset + op.limit]

    def _namespaces(self, namespace: tuple[str, ...] = ()) -> list[tuple[str, ...]]:
        found = [namespace] if namespace else []
        try:
            entries = self.fs.read_dir(self._dir(namespace))
        except FileNotFoundError:
            return found
        for entry in entries:
            if entry.type == "dir":
                found += self._namespaces(namespace + (entry.name,))
        return found

    def batch(self, ops: Iterable[Op]) -> list[Result]:
        results: list[Result] = []
        wrote = False
        for op in ops:
            if isinstance(op, PutOp):
                self._put(op.namespace, op.key, op.value)
                wrote = True
                results.append(None)
            elif isinstance(op, GetOp):
                results.append(self._get(op.namespace, op.key))
            elif isinstance(op, SearchOp):
                results.append(self._search(op))
            elif isinstance(op, ListNamespacesOp):
                results.append(self._namespaces()[op.offset : op.offset + op.limit])
            else:
                raise NotImplementedError(type(op).__name__)
        if wrote:
            self.filespace.sync_all()  # make the writes visible to every other client
        return results

    async def abatch(self, ops: Iterable[Op]) -> list[Result]:
        return self.batch(ops)
