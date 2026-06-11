import os
import re
import math
import time
import requests
import multiprocessing
from concurrent.futures import ProcessPoolExecutor

# Common English stopwords to clean up TF-IDF calculation
STOPWORDS = set([
    'a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 'and', 'any', 'are', 'arent', 'as', 'at',
    'be', 'because', 'been', 'before', 'being', 'below', 'between', 'both', 'but', 'by', 'cant', 'cannot', 'could',
    'couldnt', 'did', 'didnt', 'do', 'does', 'doesnt', 'doing', 'dont', 'down', 'during', 'each', 'few', 'for', 'from',
    'further', 'had', 'hadnt', 'has', 'hasnt', 'have', 'havent', 'having', 'he', 'hed', 'hell', 'hes', 'her', 'here',
    'heres', 'hers', 'herself', 'him', 'himself', 'his', 'how', 'hows', 'i', 'id', 'ill', 'im', 'ive', 'if', 'in',
    'into', 'is', 'isnt', 'it', 'its', 'itself', 'lets', 'me', 'more', 'most', 'mustnt', 'my', 'myself', 'no', 'nor',
    'not', 'of', 'off', 'on', 'once', 'only', 'or', 'other', 'ought', 'our', 'ours', 'ourselves', 'out', 'over', 'own',
    'same', 'shannt', 'she', 'shed', 'shell', 'shes', 'should', 'shouldnt', 'so', 'some', 'such', 'than', 'that', 'thats',
    'the', 'their', 'theirs', 'them', 'themselves', 'then', 'there', 'theres', 'these', 'they', 'theyd', 'theyll',
    'theyre', 'theyve', 'this', 'those', 'through', 'to', 'too', 'under', 'until', 'up', 'very', 'was', 'wasnt', 'we',
    'wed', 'well', 'were', 'weve', 'werent', 'what', 'whats', 'when', 'whens', 'where', 'wheres', 'which', 'while',
    'who', 'whos', 'whom', 'why', 'whys', 'with', 'wont', 'would', 'wouldnt', 'you', 'youd', 'youll', 'youre', 'youve',
    'your', 'yours', 'yourself', 'yourselves'
])

def load_env_key():
    """Reads the Gemini API key from the local .env file if it exists."""
    if os.path.exists('.env'):
        try:
            with open('.env', 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('GEMINI_API_KEY='):
                        key = line.split('=', 1)[1].strip()
                        # Remove quotes if present
                        if key.startswith('"') and key.endswith('"'):
                            key = key[1:-1]
                        elif key.startswith("'") and key.endswith("'"):
                            key = key[1:-1]
                        return key
        except Exception as e:
            print(f"Error reading .env file: {e}")
    return None

def tokenize(text):
    """Cleans and tokenizes text into words, removing punctuation and stopwords."""
    text = text.lower()
    words = re.findall(r'[a-zA-Z0-9_\-\$]+', text)
    return [w for w in words if w not in STOPWORDS and len(w) > 1]

# Top-level helper function for multiprocessing pool to calculate TF for a chunk
def calculate_chunk_tf(args):
    """Worker function to calculate term frequency for a single chunk."""
    chunk_id, text = args
    tokens = tokenize(text)
    tf = {}
    for t in tokens:
        tf[t] = tf.get(t, 0) + 1
    # Normalize TF by total tokens in chunk
    total_tokens = len(tokens)
    if total_tokens > 0:
        for t in tf:
            tf[t] = tf[t] / total_tokens
    return chunk_id, tf, text

# Top-level helper function for parallel similarity matching with simulated workload
def calculate_chunk_similarity(args):
    """Worker function to calculate cosine similarity for a chunk against query vector.
    Can run an optional intensive math loop to simulate heavier data retrieval.
    """
    chunk_id, chunk_vector, query_vector, text, workload_intensity = args
    
    # Simulate intensive CPU calculation if requested
    if workload_intensity > 0:
        val = 1.0
        for _ in range(workload_intensity):
            val = math.sin(val) * math.cos(val) + math.tanh(val)

    # Vector dot product
    dot_product = 0.0
    for term, q_val in query_vector.items():
        if term in chunk_vector:
            dot_product += chunk_vector[term] * q_val
            
    # Vector magnitudes
    query_magnitude = math.sqrt(sum(val ** 2 for val in query_vector.values()))
    chunk_magnitude = math.sqrt(sum(val ** 2 for val in chunk_vector.values()))
    
    similarity = 0.0
    if query_magnitude > 0 and chunk_magnitude > 0:
        similarity = dot_product / (query_magnitude * chunk_magnitude)
        
    return chunk_id, similarity, text

class RAGEngine:
    def __init__(self, kb_dir='knowledge_base'):
        self.kb_dir = kb_dir
        self.chunks = []      # List of strings (paragraphs/sections)
        self.chunk_tfs = {}   # dict mapping chunk_id -> term frequencies
        self.idfs = {}        # dict mapping term -> idf value
        self.chunk_tfidfs = {} # dict mapping chunk_id -> tf-idf vector
        self.is_indexed = False
        self._executor = None
        self._executor_workers = None

    def get_executor(self, num_workers=None):
        """Retrieves or creates a persistent ProcessPoolExecutor to avoid spawn overhead."""
        if num_workers is None:
            num_workers = max(1, multiprocessing.cpu_count() - 1)
        
        if self._executor is None:
            self._executor = ProcessPoolExecutor(max_workers=num_workers)
            self._executor_workers = num_workers
        elif self._executor_workers != num_workers:
            self._executor.shutdown(wait=True)
            self._executor = ProcessPoolExecutor(max_workers=num_workers)
            self._executor_workers = num_workers
            
        return self._executor

    def shutdown_executor(self):
        """Cleans up executor resources."""
        if self._executor is not None:
            self._executor.shutdown(wait=True)
            self._executor = None
            self._executor_workers = None

    def load_documents(self):
        """Loads and splits knowledge base files into paragraph-sized chunks."""
        self.chunks = []
        if not os.path.exists(self.kb_dir):
            os.makedirs(self.kb_dir)
            return

        for filename in sorted(os.listdir(self.kb_dir)):
            if filename.endswith('.md') or filename.endswith('.txt'):
                filepath = os.path.join(self.kb_dir, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                topic = filename.replace('_', ' ').replace('.md', '').replace('.txt', '').title()
                raw_sections = re.split(r'\n(?=## )|\n{2,}', content)
                
                for idx, section in enumerate(raw_sections):
                    section = section.strip()
                    if len(section) > 50:  # Skip trivial short lines
                        # Inject document origin
                        formatted_section = f"[{topic}] {section}"
                        self.chunks.append(formatted_section)
        
        self.is_indexed = False

    def build_index_sequential(self):
        """Sequentially computes the TF-IDF vectors for all chunks."""
        start_time = time.time()
        self.chunk_tfs = {}
        self.idfs = {}
        self.chunk_tfidfs = {}
        
        for i, text in enumerate(self.chunks):
            _, tf, _ = calculate_chunk_tf((i, text))
            self.chunk_tfs[i] = tf

        total_docs = len(self.chunks)
        doc_counts = {}
        for tf in self.chunk_tfs.values():
            for term in tf.keys():
                doc_counts[term] = doc_counts.get(term, 0) + 1
        
        for term, count in doc_counts.items():
            self.idfs[term] = math.log((1 + total_docs) / (1 + count)) + 1

        for chunk_id, tf in self.chunk_tfs.items():
            tfidf = {}
            for term, val in tf.items():
                tfidf[term] = val * self.idfs.get(term, 0.0)
            self.chunk_tfidfs[chunk_id] = tfidf

        self.is_indexed = True
        return time.time() - start_time

    def build_index_parallel(self, num_workers=None):
        """Computes TF-IDF vectors in parallel using multiple processes."""
        start_time = time.time()
        self.chunk_tfs = {}
        self.idfs = {}
        self.chunk_tfidfs = {}
        
        tasks = [(i, text) for i, text in enumerate(self.chunks)]
        
        executor = self.get_executor(num_workers)
        results = list(executor.map(calculate_chunk_tf, tasks))
            
        for chunk_id, tf, _ in results:
            self.chunk_tfs[chunk_id] = tf

        total_docs = len(self.chunks)
        doc_counts = {}
        for tf in self.chunk_tfs.values():
            for term in tf.keys():
                doc_counts[term] = doc_counts.get(term, 0) + 1
        
        for term, count in doc_counts.items():
            self.idfs[term] = math.log((1 + total_docs) / (1 + count)) + 1

        for chunk_id, tf in self.chunk_tfs.items():
            tfidf = {}
            for term, val in tf.items():
                tfidf[term] = val * self.idfs.get(term, 0.0)
            self.chunk_tfidfs[chunk_id] = tfidf

        self.is_indexed = True
        return time.time() - start_time

    def search_sequential(self, query, top_k=4, workload_intensity=0):
        """Sequentially searches documents using cosine similarity."""
        start_time = time.time()
        
        # Vectorize query
        query_tokens = tokenize(query)
        query_tf = {}
        for t in query_tokens:
            query_tf[t] = query_tf.get(t, 0) + 1
        
        total_query_tokens = len(query_tokens)
        query_vector = {}
        if total_query_tokens > 0:
            for term, count in query_tf.items():
                tf_val = count / total_query_tokens
                query_vector[term] = tf_val * self.idfs.get(term, 0.0)

        # Calculate cosine similarity for all chunks sequentially
        results = []
        for chunk_id, chunk_vector in self.chunk_tfidfs.items():
            text = self.chunks[chunk_id]
            _, similarity, _ = calculate_chunk_similarity((chunk_id, chunk_vector, query_vector, text, workload_intensity))
            results.append((chunk_id, similarity, text))

        results.sort(key=lambda x: x[1], reverse=True)
        
        # Ensure we return top results. If no results have similarity > 0, return the top matching keyword occurrences as fallback.
        top_results = [r for r in results[:top_k] if r[1] > 0]
        if not top_results and results:
            top_results = results[:top_k]
            
        elapsed_time = time.time() - start_time
        return top_results, elapsed_time

    def search_parallel(self, query, top_k=4, num_workers=None, workload_intensity=0):
        """Searches documents in parallel using multiple processes."""
        start_time = time.time()
        
        # Vectorize query
        query_tokens = tokenize(query)
        query_tf = {}
        for t in query_tokens:
            query_tf[t] = query_tf.get(t, 0) + 1
        
        total_query_tokens = len(query_tokens)
        query_vector = {}
        if total_query_tokens > 0:
            for term, count in query_tf.items():
                tf_val = count / total_query_tokens
                query_vector[term] = tf_val * self.idfs.get(term, 0.0)

        # Prepare tasks for the pool
        tasks = []
        for chunk_id, chunk_vector in self.chunk_tfidfs.items():
            text = self.chunks[chunk_id]
            tasks.append((chunk_id, chunk_vector, query_vector, text, workload_intensity))

        # Distribute similarity calculations using persistent pool
        executor = self.get_executor(num_workers)
        results = list(executor.map(calculate_chunk_similarity, tasks))

        results.sort(key=lambda x: x[1], reverse=True)
        
        # Guarantee we get the best possible matching sections even if scores are 0
        top_results = [r for r in results[:top_k] if r[1] > 0]
        if not top_results and results:
            top_results = results[:top_k]
            
        elapsed_time = time.time() - start_time
        return top_results, elapsed_time

    def check_conversational_query(self, query):
        """Intercepts simple greetings and conversational statements so the bot always responds warmly."""
        clean_query = query.strip().lower().rstrip('?').rstrip('!')
        
        # Intercept creator questions
        creator_questions = [
            'who created you', 'who made you', 'who is your creator', 'who is your developer',
            'who programmed you', 'who built you', 'who is the creator of this bot'
        ]
        if any(q in clean_query for q in creator_questions):
            return "I was created by **ROOP CHAND**! 🎓"

        greetings = ['hi', 'hello', 'hey', 'greetings', 'hola', 'yo', 'good morning', 'good afternoon', 'good evening']
        if clean_query in greetings:
            return (
                "Hello! I am your Parallel and Distributed Computing (PDC) teaching assistant. 🤖\n\n"
                "I can help you review topics from your syllabus, such as:\n"
                "- **Flynn's Taxonomy** (SIMD, MIMD, etc.)\n"
                "- **Performance Metrics** (Amdahl's Law, speedup)\n"
                "- **Shared Memory** (OpenMP, synchronization, race conditions)\n"
                "- **Distributed Memory** (MPI, collective communications)\n"
                "- **GPU Acceleration** (CUDA grids, threads)\n"
                "- **Distributed Paradigms** (CAP Theorem, MapReduce, HDFS)\n\n"
                "What topic would you like to discuss today?"
            )
            
        identities = ['who are you', 'what is your name', 'what do you do', 'what are you']
        if any(id_q in clean_query for id_q in identities):
            return (
                "I am the **PDC RAG Chatbot**, an AI-powered academic assistant built to help student teachers "
                "and students understand Parallel and Distributed Computing concepts.\n\n"
                "I use a **Retrieval-Augmented Generation (RAG)** engine. This means I search local course note files "
                "in parallel, retrieve the most relevant sections, and use them to construct correct, precise, and simple answers."
            )
            
        status_q = ['how are you', 'how is it going', 'are you ok', 'how are things']
        if any(st_q in clean_query for st_q in status_q):
            return (
                "I am running perfectly! My local parallel indexing engine is loaded, and I am ready to process search queries "
                "across your CPU cores. 💻\n\n"
                "Ask me any question about parallel programming to test my response times!"
            )
            
        thanks = ['thank you', 'thanks', 'cool', 'awesome', 'great', 'ok', 'okay']
        if clean_query in thanks or any(th in clean_query for th in ['thank you', 'thanks']):
            return "You're welcome! Let me know if you have any other questions about Parallel and Distributed Computing. Happy learning! 🚀"
            
        return None

    def benchmark(self, query, num_runs=5, num_workers=None, workload_intensity=25000):
        """Runs the search multiple times to get a reliable performance benchmark."""
        if not self.is_indexed:
            self.build_index_sequential()

        self.get_executor(num_workers)
        self.search_parallel(query, num_workers=num_workers, workload_intensity=0)

        seq_times = []
        for _ in range(num_runs):
            _, t = self.search_sequential(query, workload_intensity=workload_intensity)
            seq_times.append(t)
        avg_seq = sum(seq_times) / num_runs

        par_times = []
        for _ in range(num_runs):
            _, t = self.search_parallel(query, num_workers=num_workers, workload_intensity=workload_intensity)
            par_times.append(t)
        avg_par = sum(par_times) / num_runs

        cores = num_workers or max(1, multiprocessing.cpu_count() - 1)
        speedup = avg_seq / avg_par if avg_par > 0 else 1.0
        efficiency = speedup / cores

        return {
            'sequential_time_ms': avg_seq * 1000,
            'parallel_time_ms': avg_par * 1000,
            'speedup': speedup,
            'efficiency': efficiency,
            'cores_used': cores,
            'workload_intensity': workload_intensity
        }

    def generate_offline_answer(self, query, retrieved_chunks):
        """Generates an extractive response from matching text segments when offline."""
        conv_response = self.check_conversational_query(query)
        if conv_response:
            return conv_response

        if not retrieved_chunks or all(score == 0 for _, score, _ in retrieved_chunks):
            if not self.chunks:
                return (
                    "⚠️ **Error**: The knowledge base is currently empty. Please place markdown (.md) or text (.txt) files "
                    "containing study notes inside the `knowledge_base/` folder and click 'Reload Index' in the sidebar."
                )
            
            return (
                "### 💻 Offline Mode (Fallback Response)\n"
                "I am running in **offline mode** and did not find a strong keyword match in the local notes for your question.\n\n"
                "Here are the core topics I have files for. You can ask me questions about them:\n"
                "1. **Parallel Computing Intro** & Flynn's Taxonomy\n"
                "2. **Performance Laws** (Amdahl's, Gustafson's)\n"
                "3. **Shared Memory Programming** (Threads, OpenMP directives, synchronization)\n"
                "4. **Distributed Memory Programming** (MPI point-to-point and collectives)\n"
                "5. **GPU Acceleration** (CUDA blocks, grids, kernels)\n"
                "6. **Distributed Systems Frameworks** (CAP theorem, MapReduce, HDFS)\n\n"
                "*Tip: Configure a **Gemini API Key** in the settings panel or `.env` file to allow me to answer general questions using AI reasoning!*"
            )

        answer_lines = []
        answer_lines.append("### 💻 Offline Mode (Extracted Course Material)")
        answer_lines.append(f"I found some relevant study sections matching your query *'{query}'*. Here are the excerpts:\n")
        
        for idx, (chunk_id, score, text) in enumerate(retrieved_chunks):
            match = re.match(r'^\[(.*?)\] (.*)', text, re.DOTALL)
            if match:
                topic, body = match.groups()
                header = f"#### {idx+1}. Reference: *{topic}* (Cosine Similarity: {score:.2%})"
            else:
                body = text
                header = f"#### {idx+1}. Reference Section (Cosine Similarity: {score:.2%})"
                
            formatted_text = "\n".join(f"> {line}" for line in body.split("\n"))
            answer_lines.append(header)
            answer_lines.append(formatted_text)
            answer_lines.append("")
            
        answer_lines.append("\n*Tip: Connect your **Gemini API Key** in the settings sidebar or `.env` file to merge these sections into a smart, conversational summary!*")
        return "\n".join(answer_lines)

    def generate_llm_answer(self, query, retrieved_chunks, api_key):
        """Queries Google Gemini API with the query and retrieved context."""
        conv_response = self.check_conversational_query(query)
        if conv_response:
            return conv_response

        if not api_key:
            return self.generate_offline_answer(query, retrieved_chunks)

        has_matches = retrieved_chunks and any(score > 0 for _, score, _ in retrieved_chunks)
        
        if not has_matches:
            context = "No direct matches found in local course notes."
        else:
            context = "\n\n".join([text for _, _, text in retrieved_chunks])

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
        headers = {'Content-Type': 'application/json'}
        
        prompt = (
            "You are an expert academic teaching assistant for a university course on Parallel and Distributed Computing (PDC).\n"
            "Your target audience is student teachers and students who want clear, correct, and simple explanations.\n\n"
            "Here is the local course context retrieved from our notes:\n"
            "---------------------\n"
            f"{context}\n"
            "---------------------\n\n"
            f"Question: {query}\n\n"
            "Instructions:\n"
            "1. Answer the question correctly, clearly, and concisely.\n"
            "2. If the local course context provided above contains the answer, base your response on it. "
            "If the context does not contain the answer, answer the question accurately using general Parallel and Distributed Computing academic knowledge, but clearly state what is from local notes and what is supplementary.\n"
            "3. Use Markdown formatting (bullet points, bold text, code blocks) to make your explanation easy to read.\n"
            "4. Keep the explanation academic but easy for a grading teacher to review."
        )

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ]
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=20)
            if response.status_code == 200:
                res_data = response.json()
                answer = res_data['candidates'][0]['content']['parts'][0]['text']
                return answer
            else:
                error_msg = f"API Error (Status Code {response.status_code}): {response.text}"
                print(error_msg)
                return f"Failed to get response from Gemini API. Error details:\n```\n{error_msg}\n```\n\nReturning offline search results:\n\n" + self.generate_offline_answer(query, retrieved_chunks)
        except Exception as e:
            return f"An exception occurred while contacting the Gemini API:\n`{str(e)}`\n\nReturning offline search results:\n\n" + self.generate_offline_answer(query, retrieved_chunks)

def test_run():
    print("Initializing RAG Engine...")
    engine = RAGEngine(kb_dir='knowledge_base')
    engine.load_documents()
    print(f"Loaded {len(engine.chunks)} chunks.")
    engine.build_index_sequential()
    
    query = "What is Flynn's Taxonomy?"
    print(f"\nRunning performance benchmark for query: '{query}'...")
    bench_low = engine.benchmark(query, workload_intensity=0)
    print("Low Workload Bench:", bench_low)
    
    engine.shutdown_executor()
    print("RAG Engine tests completed successfully.")

if __name__ == '__main__':
    multiprocessing.freeze_support()
    test_run()
