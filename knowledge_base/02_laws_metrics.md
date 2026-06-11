# Performance Laws and Metrics in Parallel Computing

Evaluating parallel programs requires mathematical models that explain how performance changes as we add more processors. Two fundamental laws describe these limits: Amdahl's Law and Gustafson's Law.

## Amdahl's Law (Fixed Workload)
Amdahl's Law calculates the maximum theoretical speedup of an application when a part of it is parallelized. It assumes a **fixed workload** (problem size remains constant).

### Formula
Let:
- $f$ be the fraction of the program that is serial/sequential (cannot be parallelized). Thus, $(1-f)$ is the parallelizable fraction.
- $p$ be the number of processors.

The speedup $S_p$ is given by:
$$S_p = \frac{1}{f + \frac{1 - f}{p}}$$

### Implications of Amdahl's Law
- As the number of processors $p$ approaches infinity ($p \to \infty$), the speedup is limited by the serial fraction:
  $$\lim_{p \to \infty} S_p = \frac{1}{f}$$
- For example, if $10\%$ of a program is serial ($f = 0.10$), the maximum possible speedup is $1 / 0.10 = 10$, no matter how many processors or cores are used.
- This highlights the **serial bottleneck**: even a tiny serial portion can severely limit parallel performance.

---

## Gustafson's Law (Scaled Workload)
Gustafson's Law (also known as Gustafson-Barsis's Law) argues that in practice, users do not keep the problem size fixed when they get more computing power. Instead, they **scale the workload** to solve larger problems in the same amount of time.

### Formula
Let:
- $f$ be the serial fraction of the execution time on $p$ processors.
- $p$ be the number of processors.

The scaled speedup $S_p$ is given by:
$$S_p = p + (1 - p) \times f$$

### Implications of Gustafson's Law
- Gustafson's Law suggests that speedup is **linear** with respect to the number of processors, with a slope of $(1-f)$.
- It shows that parallel processing is highly effective for large datasets because the serial part of the program remains constant, while the parallelizable part grows with the problem size.

---

## Sources of Parallel Overhead
Parallel programs rarely achieve perfect linear speedup ($S_p = p$) due to overhead:
1. **Communication Overhead**: The time processors spend exchanging data or messages (especially in distributed memory systems).
2. **Synchronization Overhead**: Processors waiting for each other at synchronization points (like barriers or locks) to maintain consistency.
3. **Load Imbalance**: Some processors receiving more work than others, causing some to idle while waiting for the bottleneck processor to finish.
4. **Creation Overhead**: The time required to spawn and destroy threads or processes.
