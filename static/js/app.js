document.addEventListener('DOMContentLoaded', () => {
    // UI Elements
    const chatHistory = document.getElementById('chat-history');
    const chatInput = document.getElementById('chat-input');
    const sendBtn = document.getElementById('send-btn');
    const apiKeyInput = document.getElementById('api-key');
    const executionMode = document.getElementById('execution-mode');
    const workerCount = document.getElementById('worker-count');
    const workerCountVal = document.getElementById('worker-count-val');
    const workloadIntensity = document.getElementById('workload-intensity');
    const workloadIntensityVal = document.getElementById('workload-intensity-val');
    const docCountBadge = document.getElementById('doc-count');
    const statusText = document.getElementById('status-text');
    const statusIndicator = document.getElementById('status-indicator');
    const btnReloadKb = document.getElementById('btn-reload-kb');
    const btnRunBench = document.getElementById('btn-run-bench');
    
    // Metrics Elements
    const metricSearchTime = document.getElementById('metric-search-time');
    const metricSpeedup = document.getElementById('metric-speedup');
    const metricEfficiency = document.getElementById('metric-efficiency');
    const metricCoresUsed = document.getElementById('metric-cores-used');
    const coresGrid = document.getElementById('cores-grid');

    // Chart.js instance variable
    let benchmarkChart = null;

    // Load API Key from LocalStorage on load
    if (localStorage.getItem('gemini_api_key')) {
        apiKeyInput.value = localStorage.getItem('gemini_api_key');
    }

    // Save API Key on change
    apiKeyInput.addEventListener('change', () => {
        localStorage.setItem('gemini_api_key', apiKeyInput.value.trim());
    });

    // Update slider value displays
    workerCount.addEventListener('input', () => {
        workerCountVal.textContent = workerCount.value;
        updateCoresVisualizer(workerCount.value, executionMode.value);
    });

    workloadIntensity.addEventListener('input', () => {
        workloadIntensityVal.textContent = parseInt(workloadIntensity.value).toLocaleString();
    });

    executionMode.addEventListener('change', () => {
        updateCoresVisualizer(workerCount.value, executionMode.value);
    });

    // Initialize App
    checkStatus();
    initChart();
    updateCoresVisualizer(workerCount.value, executionMode.value);

    // Event Listeners
    sendBtn.addEventListener('click', sendMessage);
    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    btnReloadKb.addEventListener('click', reloadKnowledgeBase);
    btnRunBench.addEventListener('click', runPerformanceBenchmark);

    // --- Helper Functions ---

    let hasEnvKey = false;

    /**
     * Checks server status and loaded documents.
     */
    async function checkStatus() {
        try {
            const res = await fetch('/api/status');
            const data = await res.json();
            if (data.status === 'success') {
                docCountBadge.textContent = `${data.document_count} chunks loaded`;
                hasEnvKey = data.has_env_key;
                
                if (apiKeyInput.value.trim() || hasEnvKey) {
                    statusText.textContent = apiKeyInput.value.trim() ? "Online (User Key)" : "Online (.env Key)";
                    statusIndicator.className = "status-badge";
                } else {
                    statusText.textContent = "Offline (Extractive)";
                    statusIndicator.className = "status-badge offline";
                }
            }
        } catch (err) {
            console.error("Failed to connect to Flask backend:", err);
            docCountBadge.textContent = "Offline";
            statusText.textContent = "Disconnected";
            statusIndicator.className = "status-badge offline";
        }
    }

    /**
     * Reloads documents in knowledge base and triggers rebuild.
     */
    async function reloadKnowledgeBase() {
        btnReloadKb.disabled = true;
        btnReloadKb.innerHTML = `<i class="spinner"></i> Indexing...`;
        try {
            const res = await fetch('/api/reload', { method: 'POST' });
            const data = await res.json();
            if (data.status === 'success') {
                showToast('Success', 'Knowledge base reindexed successfully.');
                checkStatus();
            } else {
                showToast('Error', data.message);
            }
        } catch (err) {
            showToast('Error', 'Failed to connect to backend.');
        } finally {
            btnReloadKb.disabled = false;
            btnReloadKb.textContent = 'Reload Index';
        }
    }

    /**
     * Sends the chat query to the backend and adds response bubbles.
     */
    async function sendMessage() {
        const query = chatInput.value.trim();
        if (!query) return;

        // Clear input
        chatInput.value = '';

        // Add user message to history
        appendMessage('user', query);

        // Add typing indicator
        const typingId = appendTypingIndicator();
        chatHistory.scrollTop = chatHistory.scrollHeight;

        // Prepare request
        const apiKey = apiKeyInput.value.trim();
        const mode = executionMode.value;
        const numWorkers = parseInt(workerCount.value);
        const intensity = parseInt(workloadIntensity.value);

        // Update status indicator check in case key was updated
        const isOnline = apiKey || hasEnvKey;
        statusText.textContent = isOnline ? (apiKey ? "Online (User Key)" : "Online (.env Key)") : "Offline (Extractive)";
        statusIndicator.className = isOnline ? "status-badge" : "status-badge offline";

        try {
            const response = await fetch('/api/query', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    query: query,
                    api_key: apiKey,
                    num_workers: numWorkers,
                    workload_intensity: intensity,
                    mode: mode
                })
            });

            const data = await response.json();
            removeElement(typingId);

            if (data.status === 'success') {
                appendMessage('bot', data.answer, data.is_offline);
                
                // Update metrics
                metricSearchTime.textContent = `${data.search_time_ms.toFixed(1)} ms`;
                metricCoresUsed.textContent = mode === 'parallel' ? data.cores_used : '1';
                
                // Animate cores based on search execution
                animateCoresActive(mode === 'parallel' ? data.cores_used : 1, data.search_time_ms);
            } else {
                appendMessage('bot', `⚠️ **Error from server:** ${data.message}`);
            }
        } catch (err) {
            removeElement(typingId);
            appendMessage('bot', '⚠️ **Connection Error:** Could not contact the backend Flask server.');
        }

        chatHistory.scrollTop = chatHistory.scrollHeight;
    }

    /**
     * Formats query search benchmark.
     */
    async function runPerformanceBenchmark() {
        btnRunBench.disabled = true;
        btnRunBench.textContent = 'Running Benchmark...';
        
        const numWorkers = parseInt(workerCount.value);
        const intensity = parseInt(workloadIntensity.value);
        
        try {
            const response = await fetch('/api/benchmark', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    num_workers: numWorkers,
                    workload_intensity: intensity,
                    num_runs: 4
                })
            });

            const data = await response.json();
            if (data.status === 'success') {
                const results = data.benchmark;
                
                // Update UI metric labels
                metricSearchTime.textContent = `${results.parallel_time_ms.toFixed(1)} ms`;
                metricSpeedup.textContent = `${results.speedup.toFixed(2)}x`;
                metricEfficiency.textContent = `${(results.efficiency * 100).toFixed(1)}%`;
                metricCoresUsed.textContent = results.cores_used;
                
                // Animate cores during visualization
                animateCoresActive(results.cores_used, results.parallel_time_ms);
                
                // Update chart
                updateChartData(results.sequential_time_ms, results.parallel_time_ms, results.cores_used);
                
                showToast('Benchmark Complete', `Speedup of ${results.speedup.toFixed(2)}x achieved using ${results.cores_used} parallel workers.`);
            } else {
                showToast('Error', data.message);
            }
        } catch (err) {
            console.error(err);
            showToast('Error', 'Benchmark connection failed.');
        } finally {
            btnRunBench.disabled = false;
            btnRunBench.textContent = 'Run Performance Benchmark';
        }
    }

    // --- DOM UI Render Helpers ---

    /**
     * Appends a message bubble.
     */
    function appendMessage(sender, text, isOffline = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${sender}`;
        
        const bubble = document.createElement('div');
        bubble.className = 'message-bubble';
        
        // Simple Markdown parsing
        bubble.innerHTML = parseMarkdown(text);
        
        const meta = document.createElement('div');
        meta.className = 'message-meta';
        const timeStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        if (sender === 'bot') {
            meta.innerHTML = `<span>🤖 Chatbot</span><span>•</span><span>${timeStr}</span>` + 
                             (isOffline ? `<span>•</span><span style="color:var(--accent-orange)">Offline Context</span>` : '');
        } else {
            meta.innerHTML = `<span>👤 You</span><span>•</span><span>${timeStr}</span>`;
        }

        messageDiv.appendChild(bubble);
        messageDiv.appendChild(meta);
        chatHistory.appendChild(messageDiv);
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }

    /**
     * Appends the typing indicator.
     */
    function appendTypingIndicator() {
        const id = 'typing-' + Date.now();
        const indicatorDiv = document.createElement('div');
        indicatorDiv.className = 'chat-message bot';
        indicatorDiv.id = id;
        
        const bubble = document.createElement('div');
        bubble.className = 'message-bubble';
        
        const typing = document.createElement('div');
        typing.className = 'typing-indicator';
        typing.innerHTML = `
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        `;
        
        bubble.appendChild(typing);
        indicatorDiv.appendChild(bubble);
        chatHistory.appendChild(indicatorDiv);
        return id;
    }

    function removeElement(id) {
        const el = document.getElementById(id);
        if (el) el.remove();
    }

    /**
     * Updates static display of the CPU grid.
     */
    function updateCoresVisualizer(cores, mode) {
        coresGrid.innerHTML = '';
        
        // Add Master CPU node
        const masterNode = document.createElement('div');
        masterNode.className = 'core-node master';
        masterNode.innerHTML = `
            <span class="core-name">CPU Master</span>
            <span class="core-status">COORDINATOR</span>
        `;
        coresGrid.appendChild(masterNode);

        const totalCores = 7; // Max visualizer cores
        const activeCount = mode === 'parallel' ? parseInt(cores) : 0;
        
        for (let i = 1; i <= totalCores; i++) {
            const node = document.createElement('div');
            const isActive = i <= activeCount;
            node.className = `core-node ${isActive ? 'active' : ''}`;
            node.id = `core-visual-${i}`;
            node.innerHTML = `
                <span class="core-name">Core #${i}</span>
                <span class="core-status">${isActive ? 'ACTIVE' : 'IDLE'}</span>
            `;
            coresGrid.appendChild(node);
        }
    }

    /**
     * Animates CPU active status during operations.
     */
    function animateCoresActive(coresCount, durationMs) {
        const activeNodes = document.querySelectorAll('.core-node.active');
        activeNodes.forEach(node => {
            node.style.border = '1px solid #60a5fa';
            node.style.boxShadow = '0 0 15px rgba(96, 165, 250, 0.4)';
            node.querySelector('.core-status').textContent = 'COMPUTING';
            node.querySelector('.core-status').style.color = '#60a5fa';
        });

        setTimeout(() => {
            activeNodes.forEach(node => {
                node.style.border = '';
                node.style.boxShadow = '';
                node.querySelector('.core-status').textContent = 'ACTIVE';
                node.querySelector('.core-status').style.color = '';
            });
        }, Math.max(500, durationMs));
    }

    // --- Chart.js Integration ---

    function initChart() {
        const ctx = document.getElementById('benchmark-chart').getContext('2d');
        benchmarkChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Sequential Search', 'Parallel Search'],
                datasets: [{
                    label: 'Search Execution Latency (ms)',
                    data: [0, 0],
                    backgroundColor: [
                        'rgba(245, 158, 11, 0.3)', // sequential orange
                        'rgba(59, 130, 246, 0.3)'   // parallel blue
                    ],
                    borderColor: [
                        '#f59e0b',
                        '#3b82f6'
                    ],
                    borderWidth: 1.5,
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { color: 'rgba(255, 255, 255, 0.05)' },
                        ticks: { color: '#9ca3af' }
                    },
                    x: {
                        grid: { display: false },
                        ticks: { color: '#9ca3af' }
                    }
                }
            }
        });
    }

    function updateChartData(seqMs, parMs, workers) {
        if (!benchmarkChart) return;
        benchmarkChart.data.datasets[0].data = [seqMs, parMs];
        benchmarkChart.data.datasets[0].label = `Latency on ${workers} Cores (ms)`;
        benchmarkChart.update();
    }

    // --- Basic Regex Markdown Parser ---

    function parseMarkdown(text) {
        // Safe HTML escape
        let html = text
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;");

        // Code blocks: ```code```
        html = html.replace(/```([\s\S]*?)```/g, (match, p1) => {
            return `<pre><code>${p1.trim()}</code></pre>`;
        });

        // Inline code: `code`
        html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

        // Headings
        html = html.replace(/^#### (.*$)/gim, '<h4>$1</h4>');
        html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
        html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>');
        html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>');

        // Bold text
        html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');

        // Italics
        html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');

        // Blockquotes
        html = html.replace(/^\s*&gt;\s+(.*$)/gim, '<blockquote>$1</blockquote>');

        // Bullet lists
        html = html.replace(/^\s*-\s+(.*$)/gim, '<li>$1</li>');
        // Group lists if consecutive
        html = html.replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>');

        // Line breaks (convert double newlines to paragraphs)
        html = html.split('\n\n').map(p => {
            if (p.trim().startsWith('<h') || p.trim().startsWith('<pre') || p.trim().startsWith('<ul') || p.trim().startsWith('<block')) {
                return p;
            }
            return `<p>${p.replace(/\n/g, '<br>')}</p>`;
        }).join('');

        return html;
    }

    // --- Toast / Notification ---
    
    function showToast(title, msg) {
        // Append absolute styled overlay toast
        const toast = document.createElement('div');
        toast.style.position = 'fixed';
        toast.style.bottom = '24px';
        toast.style.right = '24px';
        toast.style.background = 'rgba(18, 22, 33, 0.9)';
        toast.style.border = '1px solid var(--border-hover)';
        toast.style.backdropFilter = 'blur(10px)';
        toast.style.padding = '16px 20px';
        toast.style.borderRadius = '12px';
        toast.style.zIndex = '9999';
        toast.style.boxShadow = '0 10px 30px rgba(0,0,0,0.5)';
        toast.style.animation = 'fadeInUp 0.3s forwards';
        toast.style.maxWidth = '300px';

        toast.innerHTML = `
            <div style="font-weight:700; font-family:'Outfit'; font-size:14px; margin-bottom:4px; color:white;">${title}</div>
            <div style="font-size:12.5px; color:var(--text-secondary); line-height:1.4;">${msg}</div>
        `;
        
        document.body.appendChild(toast);
        setTimeout(() => {
            toast.style.animation = 'fadeOutDown 0.3s forwards';
            setTimeout(() => toast.remove(), 300);
        }, 4000);
    }
});
