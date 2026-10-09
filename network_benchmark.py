#!/usr/bin/env python3
"""Compare sequential, ThreadPoolExecutor and ProcessPoolExecutor for 20 URLs."""

from __future__ import annotations

import argparse
import statistics
import time
import urllib.error
import urllib.request
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

WORKERS = 4
REPEATS = 3
TIMEOUT = 10


@dataclass(frozen=True)
class FetchResult:
    url: str
    ok: bool
    bytes_read: int
    error: str = ""


def load_urls(path: Path) -> list[str]:
    urls = [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    if len(urls) != 20:
        raise ValueError(f"Expected exactly 20 URLs in {path}, got {len(urls)}")
    return urls


def fetch_url(url: str) -> FetchResult:
    request = urllib.request.Request(url, headers={"User-Agent": "OS-P-4-benchmark/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            data = response.read()
        return FetchResult(url=url, ok=True, bytes_read=len(data))
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return FetchResult(url=url, ok=False, bytes_read=0, error=f"{type(exc).__name__}: {exc}")


def sequential(urls: list[str]) -> list[FetchResult]:
    return [fetch_url(url) for url in urls]


def threaded(urls: list[str]) -> list[FetchResult]:
    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        return list(executor.map(fetch_url, urls))


def processed(urls: list[str]) -> list[FetchResult]:
    with ProcessPoolExecutor(max_workers=WORKERS) as executor:
        return list(executor.map(fetch_url, urls))


def benchmark(
    name: str,
    function: Callable[[list[str]], list[FetchResult]],
    urls: list[str],
) -> tuple[list[float], float, int, int, list[FetchResult]]:
    times: list[float] = []
    last_results: list[FetchResult] = []

    for attempt in range(1, REPEATS + 1):
        started = time.perf_counter()
        last_results = function(urls)
        elapsed = time.perf_counter() - started
        times.append(elapsed)
        ok_count = sum(result.ok for result in last_results)
        print(f"{name:20s} run {attempt}: {elapsed:.6f} s, successful: {ok_count}/20")

    successful = sum(result.ok for result in last_results)
    total_bytes = sum(result.bytes_read for result in last_results)
    return times, statistics.median(times), successful, total_bytes, last_results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", nargs="?", type=Path, default=Path("urls.txt"))
    args = parser.parse_args()

    urls = load_urls(args.file.resolve())
    methods = [
        ("Sequential", sequential),
        ("ThreadPoolExecutor", threaded),
        ("ProcessPoolExecutor", processed),
    ]

    rows: list[tuple[str, float, int, int]] = []
    final_results: list[FetchResult] = []
    for name, function in methods:
        _, median, successful, total_bytes, final_results = benchmark(name, function, urls)
        rows.append((name, median, successful, total_bytes))
        print()

    print("## Network benchmark")
    print("| Method | Successful (last run) | Bytes (last run) | Median of 3 runs, s |")
    print("|---|---:|---:|---:|")
    for name, median, successful, total_bytes in rows:
        print(f"| {name} | {successful}/20 | {total_bytes} | {median:.6f} |")

    failed = [result for result in final_results if not result.ok]
    if failed:
        print("\nFailed URLs (last run):")
        for result in failed:
            print(f"- {result.url}: {result.error}")


if __name__ == "__main__":
    main()
