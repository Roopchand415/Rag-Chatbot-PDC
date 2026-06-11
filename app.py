import os
import atexit
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from rag_engine import RAGEngine, load_env_key

app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)  # Enable Cross-Origin Resource Sharing

# Initialize and load the RAGEngine
engine = RAGEngine(kb_dir='knowledge_base')
engine.load_documents()
engine.build_index_sequential()

# Load default API Key from environment/.env
DEFAULT_API_KEY = load_env_key()

@app.route('/')
def index():
    """Serves the main dashboard user interface."""
    return render_template('index.html')

@app.route('/api/status', methods=['GET'])
def get_status():
    """Returns the current status of the knowledge base indexing and environment API keys."""
    global DEFAULT_API_KEY
    # Re-check key in case they updated .env
    DEFAULT_API_KEY = load_env_key()
    
    # Hide the key itself for safety but report if a valid key is configured
    has_key = bool(DEFAULT_API_KEY) and (DEFAULT_API_KEY != 'YOUR_GEMINI_API_KEY_HERE')
    
    return jsonify({
        'status': 'success',
        'document_count': len(engine.chunks),
        'is_indexed': engine.is_indexed,
        'kb_directory': os.path.abspath(engine.kb_dir),
        'has_env_key': has_key
    })

@app.route('/api/reload', methods=['POST'])
def reload_kb():
    """Reloads documents from the knowledge base and rebuilds the index."""
    global DEFAULT_API_KEY
    try:
        engine.load_documents()
        engine.build_index_sequential()
        DEFAULT_API_KEY = load_env_key()
        return jsonify({
            'status': 'success',
            'message': 'Knowledge base and environment variables reloaded successfully.',
            'document_count': len(engine.chunks)
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to reload knowledge base: {str(e)}'
        }), 500

@app.route('/api/query', methods=['POST'])
def query_bot():
    """Handles chatbot user queries."""
    global DEFAULT_API_KEY
    data = request.json or {}
    query = data.get('query', '').strip()
    api_key = data.get('api_key', '').strip()
    num_workers = data.get('num_workers', None)
    workload_intensity = data.get('workload_intensity', 0)
    mode = data.get('mode', 'parallel')

    if not query:
        return jsonify({
            'status': 'error',
            'message': 'Query cannot be empty.'
        }), 400

    # If no key was supplied in the query request UI, use the .env key if configured
    if not api_key:
        api_key = DEFAULT_API_KEY
        # Validate that it's not the default placeholder template text
        if api_key == 'YOUR_GEMINI_API_KEY_HERE':
            api_key = ''

    try:
        if num_workers is not None:
            num_workers = int(num_workers)
        if workload_intensity is not None:
            workload_intensity = int(workload_intensity)

        # 1. Retrieve relevant chunks using selected mode (parallel vs sequential search)
        if mode == 'parallel':
            retrieved_chunks, elapsed_time = engine.search_parallel(
                query, top_k=4, num_workers=num_workers, workload_intensity=workload_intensity
            )
        else:
            retrieved_chunks, elapsed_time = engine.search_sequential(
                query, top_k=4, workload_intensity=workload_intensity
            )

        # 2. Generate the answer (using Gemini API or Offline Extractive Fallback)
        if api_key:
            answer = engine.generate_llm_answer(query, retrieved_chunks, api_key)
        else:
            answer = engine.generate_offline_answer(query, retrieved_chunks)

        # 3. Format results for response
        formatted_chunks = []
        for chunk_id, score, text in retrieved_chunks:
            formatted_chunks.append({
                'chunk_id': chunk_id,
                'score': float(score),
                'text': text
            })

        return jsonify({
            'status': 'success',
            'answer': answer,
            'retrieved_chunks': formatted_chunks,
            'search_time_ms': elapsed_time * 1000,
            'cores_used': num_workers or (engine._executor_workers or 1),
            'mode': mode,
            'is_offline': not bool(api_key)
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'An error occurred: {str(e)}'
        }), 500

@app.route('/api/benchmark', methods=['POST'])
def run_benchmark():
    """Runs a performance benchmark comparing sequential vs parallel search."""
    data = request.json or {}
    query = data.get('query', 'Explain shared memory and message passing').strip()
    num_workers = data.get('num_workers', None)
    workload_intensity = data.get('workload_intensity', 100000)
    num_runs = data.get('num_runs', 3)

    if not query:
        query = "Explain shared memory"

    try:
        if num_workers is not None:
            num_workers = int(num_workers)
        workload_intensity = int(workload_intensity)
        num_runs = int(num_runs)

        benchmark_results = engine.benchmark(
            query, num_runs=num_runs, num_workers=num_workers, workload_intensity=workload_intensity
        )

        return jsonify({
            'status': 'success',
            'benchmark': benchmark_results
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Benchmark run failed: {str(e)}'
        }), 500

@atexit.register
def shutdown_resources():
    print("Shutting down RAG Engine process pool...")
    engine.shutdown_executor()

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)
