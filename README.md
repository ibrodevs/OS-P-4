# OS-P-4 — Variant B

Laboratory work about Python threads, processes, the GIL, CPU-bound work, I/O-bound work, and memory isolation.

## Requirements

- Python 3.10+
- No third-party packages are required.

## 1. Sum numbers from `numbers.txt`

The benchmark compares three variants:

1. one thread (ordinary sequential execution);
2. four `threading.Thread` workers;
3. four `multiprocessing` workers.

Every variant is executed **3 times**, and the script prints the **median** time. All variants must produce the same sum.

A small `numbers.txt` is included so the script can be checked immediately. For a meaningful benchmark, generate a larger file first:

```bash
python3 generate_numbers.py --count 2000000
python3 cpu_benchmark.py
```

The script prints a Markdown table like this:

| Method | Sum | Median of 3 runs, s |
|---|---:|---:|
| Sequential | same result | measured at runtime |
| 4 threads | same result | measured at runtime |
| 4 processes | same result | measured at runtime |

> Exact timings depend on CPU, storage, OS, Python version and file size, so the repository does not hard-code invented measurements.

### Why threads do not speed up CPU counting

In normal CPython, the **GIL (Global Interpreter Lock)** allows only one thread at a time to execute Python bytecode in a process. Summing and parsing integers is CPU-bound Python work, so four threads mostly take turns instead of executing that Python code on four CPU cores at the same time. Thread creation and context switching can even make the threaded version a little slower.

### Why processes can speed up CPU work, but cost more

Each process has its **own Python interpreter and its own GIL**, so four processes can execute CPU-bound Python code on several CPU cores in parallel. This can reduce execution time when the input is large enough.

Processes are more expensive because the OS must create separate processes and address spaces, and Python must start worker interpreters and exchange data/results between them. For a very small `numbers.txt`, this overhead can be larger than the useful work, so multiprocessing may be slower. That is why the generator defaults to a large input for the real experiment.

## 2. Download 20 URLs

`urls.txt` contains exactly 20 URLs. The network benchmark compares:

1. sequential download;
2. `ThreadPoolExecutor(max_workers=4)`;
3. `ProcessPoolExecutor(max_workers=4)`.

Run:

```bash
python3 network_benchmark.py
```

Again, each method runs three times and the median is printed:

| Method | Successful | Median of 3 runs, s |
|---|---:|---:|
| Sequential | up to 20/20 | measured at runtime |
| ThreadPoolExecutor | up to 20/20 | measured at runtime |
| ProcessPoolExecutor | up to 20/20 | measured at runtime |

Network results naturally vary because they depend on DNS, latency, remote servers and the current Internet connection.

### Why threads speed up I/O

During blocking network I/O, CPython releases the GIL while a thread waits for the operating system. That means one thread can wait for a response while other threads start or receive other requests. Therefore threads are usually very effective for I/O-bound tasks such as downloading many URLs.

Processes can also download URLs in parallel, but for this task they normally add unnecessary process startup and inter-process communication overhead. Threads are cheaper because all workers live inside one process.

## 3. Threads share memory, processes do not

Run:

```bash
python3 memory_demo.py
```

Expected idea of the output:

```text
=== Thread ===
Parent before thread: [1, 2, 3]
Thread ...: [1, 2, 3, 4]
Parent after thread:  [1, 2, 3, 4]

=== Process ===
Parent before process: [1, 2, 3]
Process PID=...: [1, 2, 3, 5]
Parent after process:  [1, 2, 3]
```

A thread sees and changes the same global list because all threads of a process share one address space. A child process has a separate address space. On systems that use `fork`, memory initially looks the same because of copy-on-write, but a modification is private to the child. On systems that use `spawn`, the child starts a fresh interpreter; the parent still does not receive the child's ordinary global-list changes.

## Files

- `generate_numbers.py` — creates a reproducible large `numbers.txt`;
- `numbers.txt` — small ready-to-run input sample;
- `cpu_benchmark.py` — sequential / 4 threads / 4 processes CPU benchmark;
- `urls.txt` — exactly 20 URLs;
- `network_benchmark.py` — sequential / thread pool / process pool network benchmark;
- `memory_demo.py` — shared-memory vs process-isolation demonstration.

## Short conclusion

- **CPU-bound + threads:** usually no speedup in CPython because of the GIL.
- **CPU-bound + processes:** can use multiple CPU cores, but process startup/IPC costs more.
- **I/O-bound + threads:** usually a good speedup because waiting for I/O does not keep the GIL busy.
- **I/O-bound + processes:** works, but is usually heavier than necessary for network I/O.
- **Memory:** threads share ordinary objects; processes do not share ordinary mutable objects automatically.
