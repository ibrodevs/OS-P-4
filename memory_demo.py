#!/usr/bin/env python3
"""Show that threads share memory while processes have separate memory."""

from __future__ import annotations

import multiprocessing as mp
import os
import threading

shared_list = [1, 2, 3]


def thread_worker() -> None:
    shared_list.append(4)
    print(f"Thread {threading.get_ident()}: {shared_list}")


def process_worker() -> None:
    shared_list.append(5)
    print(f"Process PID={os.getpid()}: {shared_list}")


def main() -> None:
    global shared_list

    print("=== Thread ===")
    shared_list = [1, 2, 3]
    print(f"Parent before thread: {shared_list}")
    thread = threading.Thread(target=thread_worker)
    thread.start()
    thread.join()
    print(f"Parent after thread:  {shared_list}")

    print("\n=== Process ===")
    shared_list = [1, 2, 3]
    print(f"Parent before process: {shared_list}")
    process = mp.Process(target=process_worker)
    process.start()
    process.join()
    print(f"Parent after process:  {shared_list}")

    print("\nConclusion:")
    print("- The thread changed the parent's list because threads share one address space.")
    print("- The process changed only its own copy; the parent's list stayed unchanged.")


if __name__ == "__main__":
    mp.freeze_support()
    main()
