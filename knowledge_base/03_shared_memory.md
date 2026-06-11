# Shared Memory Programming and OpenMP

In shared memory architectures, all processors or cores have access to a single, global memory space. Threads communicate implicitly by reading and writing to shared variables.

## Shared Memory Concepts
- **Thread**: The smallest unit of execution that can be managed by the operating system. Threads within a process share the process's memory space, files, and resources.
- **Process**: An execution environment with its own private memory space. A process can contain multiple threads.

## OpenMP (Open Multi-Processing)
OpenMP is an Application Program Interface (API) that supports multi-platform shared-memory multiprocessing programming in C, C++, and Fortran. It uses compiler directives (pragmas), runtime library routines, and environment variables.

### Key OpenMP Constructs
1. **Parallel Regions**: Instructs the compiler to spawn a team of threads to execute the block of code.
   ```c
   #pragma omp parallel
   {
       int id = omp_get_thread_num();
       printf("Hello from thread %d\n", id);
   }
   ```
2. **Work-Sharing (Loop Parallelism)**: Distributes loop iterations among the threads.
   ```c
   #pragma omp parallel for
   for (int i = 0; i < N; i++) {
       A[i] = B[i] + C[i];
   }
   ```
3. **Data Scope Clauses**:
   - `shared(var)`: All threads access the same memory location for the variable.
   - `private(var)`: Each thread gets its own uninitialized local copy of the variable.
   - `reduction(operator:var)`: Computes a global reduction (like sum or product) in parallel by giving each thread a private accumulator and combining them at the end.
     ```c
     int sum = 0;
     #pragma omp parallel for reduction(+:sum)
     for (int i = 0; i < N; i++) {
         sum += array[i];
     }
     ```

## Synchronization and Safety Issues
Because memory is shared, multiple threads can access the same data simultaneously, leading to synchronization issues:

### 1. Race Conditions
A race condition occurs when two or more threads attempt to read and write a shared memory location simultaneously, and at least one access is a write. The final output depends on the random ordering of thread execution.
- **Solution**: Use mutual exclusion (mutexes, critical sections, atomic updates).
  ```c
  #pragma omp critical
  {
      // Only one thread at a time can execute this block
      shared_counter++;
  }
  ```

### 2. Deadlocks
A deadlock is a situation where two or more threads are unable to proceed because each is waiting for the other to release a lock or resource.
- **Conditions for Deadlock (Coffman Conditions)**:
  1. Mutual Exclusion
  2. Hold and Wait
  3. No Preemption
  4. Circular Wait

### 3. Barriers
A barrier is a synchronization point where all threads must wait until every thread in the team has arrived before any are allowed to proceed.
```c
#pragma omp barrier
```
