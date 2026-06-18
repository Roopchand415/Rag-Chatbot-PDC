import streamlit as st
import pandas as pd
from rag_engine import RAGEngine, load_env_key

st.set_page_config(page_title="PDC RAG Chatbot", page_icon="🤖", layout="wide")

# Initialize Session State
if "engine" not in st.session_state:
    st.session_state.engine = RAGEngine(kb_dir='knowledge_base')
    st.session_state.engine.load_documents()
    st.session_state.engine.build_index_sequential()

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "👋 Hello! I am your **Parallel and Distributed Computing (PDC) RAG Chatbot**.\n\nYou can ask me questions about:\n* **Flynn's Taxonomy**\n* **Performance Laws**\n* **Shared Memory & OpenMP**\n* **Distributed Memory & MPI**\n* **GPU Architectures & CUDA**\n* **Distributed Systems**"}
    ]

# Sidebar
with st.sidebar:
    st.title("PDC RAG Bot")
    st.markdown("Parallel Computing Demo")
    
    st.header("🛠️ Configurations")
    api_key_input = st.text_input("Gemini API Key", type="password", placeholder="Paste your API key here...")
    st.caption("Allows conversational answers. If empty, the app runs in **Offline Extractive** mode.")
    
    st.header("⚡ Parallel Engine Settings")
    execution_mode = st.selectbox("Execution Mode", ["parallel", "sequential"])
    worker_count = st.slider("Active Worker Cores", 1, 7, 4)
    workload_intensity = st.slider("Simulated Workload Intensity", 0, 250000, 100000, step=10000)
    
    if st.button("Reload Index", use_container_width=True):
        with st.spinner("Reloading Index..."):
            st.session_state.engine.load_documents()
            if execution_mode == 'parallel':
                st.session_state.engine.build_index_parallel(num_workers=worker_count)
            else:
                st.session_state.engine.build_index_sequential()
        st.success("Knowledge base reloaded successfully!")
    
    st.header("🟢 Engine Status")
    status = "Online" if api_key_input or load_env_key() else "Offline Mode"
    st.markdown(f"**Status:** {status}")
    st.markdown(f"**Chunks Loaded:** {len(st.session_state.engine.chunks)}")
    
    st.info("💡 **How It Works:** When you submit a query, the backend splits the question's matching workload across active cores.")

# Main Layout
col1, col2 = st.columns([2, 1])

with col1:
    st.header("Parallel RAG Bot Assistant")
    
    # Display Chat
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
    # Chat Input
    if query := st.chat_input("Ask a question about PDC (e.g., Explain Amdahl's Law)..."):
        # Add user message to state and display
        st.session_state.messages.append({"role": "user", "content": query})
        with st.chat_message("user"):
            st.markdown(query)
            
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                # Run search
                api_key = api_key_input if api_key_input else load_env_key()
                
                if execution_mode == "parallel":
                    retrieved_chunks, search_time = st.session_state.engine.search_parallel(
                        query, top_k=4, num_workers=worker_count, workload_intensity=workload_intensity
                    )
                else:
                    retrieved_chunks, search_time = st.session_state.engine.search_sequential(
                        query, top_k=4, workload_intensity=workload_intensity
                    )
                
                if api_key:
                    answer = st.session_state.engine.generate_llm_answer(query, retrieved_chunks, api_key)
                else:
                    answer = st.session_state.engine.generate_offline_answer(query, retrieved_chunks)
                    
                st.markdown(answer)
                
                # Update the metrics in session state
                st.session_state.last_search_time = search_time * 1000
                st.session_state.last_cores_used = worker_count if execution_mode == 'parallel' else 1
                
        st.session_state.messages.append({"role": "assistant", "content": answer})

with col2:
    st.header("Metrics & Benchmarking")
    
    search_time = st.session_state.get('last_search_time', 0.0)
    cores_used = st.session_state.get('last_cores_used', 1)
    
    # Display Metrics
    col_a, col_b = st.columns(2)
    col_a.metric("Search Latency", f"{search_time:.2f} ms")
    col_b.metric("Active Workers", cores_used)
    
    st.divider()
    st.subheader("Performance Benchmark")
    st.markdown("Executes multi-run searches to compare sequential vs parallel times.")
    
    bench_query = st.text_input("Benchmark Query", value="Explain shared memory")
    if st.button("Run Benchmark", use_container_width=True):
        with st.spinner("Benchmarking..."):
            results = st.session_state.engine.benchmark(
                bench_query, num_runs=3, num_workers=worker_count, workload_intensity=workload_intensity
            )
            st.session_state.benchmark_results = results
            
    if 'benchmark_results' in st.session_state:
        res = st.session_state.benchmark_results
        
        col_c, col_d = st.columns(2)
        col_c.metric("Speedup Ratio ($S_p$)", f"{res['speedup']:.2f}x")
        col_d.metric("Parallel Efficiency ($E_p$)", f"{res['efficiency']*100:.1f}%")
        
        # Chart
        chart_data = pd.DataFrame(
            [res['sequential_time_ms'], res['parallel_time_ms']],
            index=["Sequential", "Parallel"],
            columns=["Time (ms)"]
        )
        st.bar_chart(chart_data)
