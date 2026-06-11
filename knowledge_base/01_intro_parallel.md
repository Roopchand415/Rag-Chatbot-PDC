# Introduction to Parallel and Distributed Computing

Parallel and Distributed Computing (PDC) is a field of computer science that focuses on executing multiple computations simultaneously to solve complex problems faster or to handle large scales of data.

## Parallel vs. Distributed Computing
- **Parallel Computing**: Typically refers to running multiple processes or threads on a single physical machine with multiple processors or cores. These processors share a common memory space (Shared Memory) or communicate via a high-speed internal bus. The primary goal is to increase performance (speedup).
- **Distributed Computing**: Involves multiple autonomous computers (called nodes or machines) that communicate over a network. Each computer has its own private memory (Distributed Memory). The primary goals include scalability, fault tolerance, resource sharing, and handling massive data sets that cannot fit on a single system.

## Flynn's Taxonomy
Michael J. Flynn proposed a classification system for computer architectures based on the number of concurrent instruction streams and data streams:

1. **SISD (Single Instruction Stream, Single Data Stream)**
   - A sequential, non-parallel computer. A single processor executes one instruction at a time on a single data stream.
   - Example: Traditional single-core CPUs.

2. **SIMD (Single Instruction Stream, Multiple Data Streams)**
   - A single instruction is applied to multiple data elements simultaneously. Excellent for vector and matrix operations.
   - Example: Vector processors, MMX/SSE instructions in modern CPUs, and GPUs (Graphics Processing Units).

3. **MISD (Multiple Instruction Streams, Single Data Stream)**
   - Multiple processors execute different instructions on the same data stream. This is a rare architecture, mostly used for fault tolerance or specialized systems.
   - Example: Space shuttle flight control computers, systolic arrays.

4. **MIMD (Multiple Instruction Streams, Multiple Data Streams)**
   - Multiple autonomous processors execute different instructions on different data streams. This is the most common architecture for modern parallel computers.
   - Example: Multi-core PCs, clusters, supercomputers.

## Basic Performance Metrics
To evaluate the performance of a parallel system, we use the following metrics:
- **Speedup ($S_p$)**: The ratio of the time taken to run a program sequentially ($T_1$) to the time taken to run it in parallel using $p$ processors ($T_p$).
  $$S_p = \frac{T_1}{T_p}$$
- **Efficiency ($E_p$)**: The fraction of time that the processors are usefully employed. It is the speedup divided by the number of processors.
  $$E_p = \frac{S_p}{p} = \frac{T_1}{p \times T_p}$$
- **Scaleup**: Measures the ability of a $p$-times larger system to solve a $p$-times larger problem in the same amount of time.
- **Sizeup**: Measures the ability of a $p$-times larger system to solve a $p$-times larger problem in less time.
