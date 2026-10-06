"""Two agents append a fact to the same shared memory file at the same time, two ways:

  python collision.py take1    read, think, write, with no lock               -> one fact is lost
  python collision.py take2    the same, under an exclusive lock on the file  -> both facts land

The agents read their tokens from ~/.lucidlink/agent-researcher.token and agent-analyst.token
unless two paths are given. The file is removed afterwards.

Env: LUCIDLINK_FILESPACE
"""

import argparse
import json
import multiprocessing as mp
import time

from lucidlink_store import LucidLinkStore, open_filespace

NAMESPACE, KEY = ("shared", "customers"), "acme"
PATH = "/memory/shared/customers/acme.json"
FACTS = {
    "researcher": "renewed early; procurement wants a single invoice",
    "analyst": "propose the annual tier; decision pending review",
}


def worker(name: str, token_file: str, take: str, barrier, results) -> None:
    client, filespace = open_filespace(token_file)
    fs = filespace.fs
    try:
        barrier.wait(timeout=30)
        started = time.perf_counter()
        waited = 0.0
        if take == "take1":
            doc = json.loads(fs.read_file(PATH))
            time.sleep(1.0)  # think, while the copy in hand goes stale
            doc["value"]["facts"].append({"by": name, "fact": FACTS[name]})
            fs.write_file(PATH, json.dumps(doc).encode())
        else:
            with fs.open(PATH, "r+b", lock_type="exclusive") as f:
                waited = time.perf_counter() - started
                doc = json.loads(f.read())
                time.sleep(1.0)
                doc["value"]["facts"].append({"by": name, "fact": FACTS[name]})
                fs.write_file(PATH, json.dumps(doc).encode())
        filespace.sync_all()
        results.put((name, round(time.perf_counter() - started, 2), round(waited, 2)))
    finally:
        client.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("take", choices=["take1", "take2"])
    parser.add_argument("token_a", nargs="?", default="~/.lucidlink/agent-researcher.token")
    parser.add_argument("token_b", nargs="?", default="~/.lucidlink/agent-analyst.token")
    args = parser.parse_args()

    client, filespace = open_filespace(args.token_a)
    store = LucidLinkStore(filespace)
    try:
        store.put(NAMESPACE, KEY, {"customer": "Acme", "facts": []})

        barrier = mp.Barrier(2)
        results = mp.Queue()
        workers = [
            mp.Process(target=worker, args=("researcher", args.token_a, args.take, barrier, results)),
            mp.Process(target=worker, args=("analyst", args.token_b, args.take, barrier, results)),
        ]
        for w in workers:
            w.start()
        for w in workers:
            w.join()
        if any(w.exitcode for w in workers):
            raise SystemExit("an agent failed, see above")
        timings = sorted(results.get(timeout=10) for _ in workers)

        time.sleep(2)  # let the last write propagate
        facts = store.get(NAMESPACE, KEY).value["facts"]
    finally:
        store.delete(NAMESPACE, KEY)
        client.close()

    print(f"== {args.take} ==")
    for name, total, waited in timings:
        print(f"  {name:10s} total {total:5.2f}s  waited on lock {waited:5.2f}s")
    print(f"  facts in the file afterwards: {len(facts)}  by={[f['by'] for f in facts]}")
    print("  VERDICT:", "LOST UPDATE" if len(facts) < 2 else "BOTH LANDED")


if __name__ == "__main__":
    mp.set_start_method("spawn")  # never fork a process that holds a client
    main()
