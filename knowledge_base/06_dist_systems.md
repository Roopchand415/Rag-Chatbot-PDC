# Distributed Systems and MapReduce

A distributed system is a collection of independent computers that appears to its users as a single coherent system. These systems allow computing tasks and storage to scale horizontally by adding more machines.

## CAP Theorem
Formulated by Eric Brewer, the CAP theorem states that a distributed data store can simultaneously provide at most two of the following three guarantees:
1. **Consistency (C)**: Every read receives the most recent write or an error.
2. **Availability (A)**: Every non-failing node returns a non-error response for every request (without a guarantee that it contains the most recent write).
3. **Partition Tolerance (P)**: The system continues to operate despite an arbitrary number of messages being dropped or delayed by the network between nodes.

Since physical networks are bound to experience failures, **Partition Tolerance (P) is mandatory** in real-world systems. Therefore, systems must choose between:
- **CP (Consistency and Partition Tolerance)**: Blocks requests if data consistency cannot be guaranteed (e.g., HBase, MongoDB).
- **AP (Availability and Partition Tolerance)**: Returns old data but remains fully available (e.g., Cassandra, DynamoDB).

---

## MapReduce Programming Model
MapReduce is a software framework pioneered by Google for processing large datasets in parallel on clusters of commodity hardware. It consists of two primary user-defined phases:

1. **Map Phase**: Takes a set of data and converts it into another set of data, where individual elements are broken down into key-value pairs.
   - $\text{Map}(k_1, v_1) \to \text{list}(k_2, v_2)$
2. **Shuffle and Sort (Framework-controlled)**: Groups all intermediate values associated with the same intermediate key together.
3. **Reduce Phase**: Takes the outputs from a map task, combines those data tuples into a smaller set of tuples, and writes the output.
   - $\text{Reduce}(k_2, \text{list}(v_2)) \to \text{list}(k_3, v_3)$

### Example: Word Count
- **Input**: `"hello world hello"`
- **Map Output**: `("hello", 1), ("world", 1), ("hello", 1)`
- **Shuffle & Sort**: `("hello", [1, 1]), ("world", [1])`
- **Reduce Output**: `("hello", 2), ("world", 1)`

---

## Hadoop Distributed File System (HDFS)
HDFS is the primary storage system used by Hadoop applications. It uses a master/slave architecture:
- **NameNode (Master)**: Manages the file system namespace, directories, metadata, and controls block mapping. It is a single point of failure (unless high availability is configured).
- **DataNodes (Slaves)**: Store the actual blocks of data and perform read/write operations as directed by the NameNode. HDFS automatically replicates blocks (default is 3 copies) across different racks to achieve fault tolerance.
