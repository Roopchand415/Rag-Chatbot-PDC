# Distributed Memory Programming and MPI

In distributed memory architectures, processors or nodes have their own private, local memory. There is no global address space. Nodes must communicate and share data explicitly by sending and receiving messages over a network interface.

## Message Passing Interface (MPI)
MPI is the standard programming model for distributed memory systems. It provides a set of library functions for C, C++, and Fortran to write portable parallel programs.

### Basic MPI Functions
- `MPI_Init`: Initializes the MPI execution environment. Must be called before any other MPI routines.
- `MPI_Finalize`: Terminates the MPI execution environment.
- `MPI_Comm_size`: Returns the total number of processes in a communicator group.
- `MPI_Comm_rank`: Returns the unique identifier (rank, from $0$ to $p-1$) of the calling process within a communicator group.

```c
#include <mpi.h>
#include <stdio.h>

int main(int argc, char** argv) {
    MPI_Init(&argc, &argv);
    int size, rank;
    MPI_Comm_size(MPI_COMM_WORLD, &size);
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    printf("Hello from process %d of %d\n", rank, size);
    MPI_Finalize();
    return 0;
}
```

---

## MPI Communication Types

### 1. Point-to-Point Communication
Involves data transfer between exactly two specific processes: one sender and one receiver.
- **Blocking Send/Receive (`MPI_Send` / `MPI_Recv`)**: The sender/receiver waits until the message buffer can be safely reused or read. It blocks execution, which can lead to deadlocks if not paired correctly (e.g., if both processes try to `MPI_Recv` first).
- **Non-blocking Send/Receive (`MPI_Isend` / `MPI_Irecv`)**: Starts a communication task and returns immediately, allowing the process to perform computation in parallel with communication. The programmer must later call `MPI_Wait` or `MPI_Test` to ensure the communication has finished.

### 2. Collective Communication
Involves all processes within a communicator group (e.g., `MPI_COMM_WORLD`) participating in a joint data transfer or computation:
- **`MPI_Bcast` (Broadcast)**: One process (the root) sends the same data to all other processes in the communicator.
- **`MPI_Scatter`**: Splits a buffer of data from the root process into equal parts and sends one part to each process.
- **`MPI_Gather`**: Collects individual blocks of data from each process and aggregates them in rank order on the root process.
- **`MPI_Reduce`**: Collects data from all processes and performs an associative/commutative mathematical reduction operation (like SUM, MAX, MIN, PROD) on it, saving the result on the root process.
- **`MPI_Allreduce`**: Performs a reduction operation and distributes the final result to all processes.
