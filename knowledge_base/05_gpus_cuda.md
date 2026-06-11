# GPU Computing and CUDA

Graphics Processing Units (GPUs) have evolved from fixed-function graphics chips to highly programmable, general-purpose parallel processors (GPGPU). They are designed for execution of compute-intensive, highly parallel calculations.

## CPU vs. GPU Architecture
- **CPU (Central Processing Unit)**: Designed for low-latency sequential processing. It has large cache memories and sophisticated control logic (like branch prediction, out-of-order execution) to execute a single thread of instructions as quickly as possible.
- **GPU (Graphics Processing Unit)**: Designed for high-throughput parallel processing. It dedicates most of its transistors to arithmetic logic units (ALUs) rather than caches and control logic. It excels when executing thousands of simple threads concurrently.

## CUDA (Compute Unified Device Architecture)
CUDA is a parallel computing platform and programming model developed by NVIDIA for programming its GPUs using C, C++, and Fortran.

### SIMT (Single Instruction, Multiple Threads)
NVIDIA uses the SIMT execution model. Under SIMT, the GPU execution engine processes threads in groups of 32 parallel threads called **warps**. All threads in a warp execute the same instruction at the same time. If threads in a warp take different execution paths (e.g., in an `if-else` statement), **warp divergence** occurs, forcing the paths to be executed sequentially, which degrades performance.

### CUDA Thread Hierarchy
To map computations to GPU hardware, CUDA organizes threads into a hierarchy:
1. **Thread**: The basic unit of execution on the GPU. Executes a single kernel instance.
2. **Block (Thread Block)**: A collection of threads that can synchronize with each other and share local memory. A block can contain up to 1024 threads.
3. **Grid**: A collection of thread blocks that execute the same kernel.

In code, blocks and grids can be 1D, 2D, or 3D.
```cpp
// Kernel function executed on GPU, indicated by __global__
__global__ void vectorAdd(float *A, float *B, float *C, int N) {
    int i = blockDim.x * blockIdx.x + threadIdx.x; // Global thread index
    if (i < N) {
        C[i] = A[i] + B[i];
    }
}

int main() {
    // Launching kernel with 256 threads per block
    int threadsPerBlock = 256;
    int blocksPerGrid = (N + threadsPerBlock - 1) / threadsPerBlock;
    vectorAdd<<<blocksPerGrid, threadsPerBlock>>>(d_A, d_B, d_C, N);
}
```

## CUDA Memory Hierarchy
Understanding memory tiers is crucial for optimizing GPU performance:
1. **Registers**: Private to each thread, fastest access speed.
2. **Local Memory**: Private to each thread, stored in off-chip global memory, used when register spilling occurs.
3. **Shared Memory**: Shared among all threads in a thread block, on-chip, extremely fast. Used for caching and thread cooperation.
4. **Global Memory**: Shared by all threads across the entire GPU, off-chip, slow access latency.
5. **Constant/Texture Memory**: Read-only, cached memory shared by all threads.
