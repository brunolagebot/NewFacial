// NewFacial - Interface JavaScript

class NewFacialApp {
    constructor() {
        this.init();
    }

    init() {
        this.loadStats();
        this.loadPersons();
        this.loadStreams();
        this.loadLogs();
        this.setupEventListeners();
        
        // Atualizar estatísticas a cada 30 segundos
        setInterval(() => this.loadStats(), 30000);
        setInterval(() => this.loadStreams(), 10000);
        setInterval(() => this.loadLogs(), 30000);
    }

    setupEventListeners() {
        // Formulário de pessoa
        document.getElementById('person-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.addPerson();
        });

        // Upload de imagens
        document.getElementById('image-files').addEventListener('change', (e) => {
            const files = e.target.files;
            const uploadBtn = document.getElementById('upload-btn');
            const selectPerson = document.getElementById('select-person');
            
            uploadBtn.disabled = !(files.length > 0 && selectPerson.value);
        });

        document.getElementById('select-person').addEventListener('change', (e) => {
            const files = document.getElementById('image-files').files;
            const uploadBtn = document.getElementById('upload-btn');
            
            uploadBtn.disabled = !(files.length > 0 && e.target.value);
        });

        document.getElementById('upload-btn').addEventListener('click', () => {
            this.uploadImages();
        });

        // Reconhecimento de imagem
        document.getElementById('recognition-file').addEventListener('change', (e) => {
            const file = e.target.files[0];
            const recognizeBtn = document.getElementById('recognize-btn');
            
            recognizeBtn.disabled = !file;
        });

        document.getElementById('recognize-btn').addEventListener('click', () => {
            this.recognizeImage();
        });

        // RTSP
        document.getElementById('rtsp-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.addRTSPStream();
        });
    }

    async loadStats() {
        try {
            const response = await fetch('/api/stats');
            const stats = await response.json();
            
            document.getElementById('total-persons').textContent = stats.total_persons;
            document.getElementById('total-embeddings').textContent = stats.total_embeddings;
            document.getElementById('total-detections').textContent = stats.total_detections;
            document.getElementById('active-streams').textContent = stats.active_streams;
        } catch (error) {
            console.error('Erro ao carregar estatísticas:', error);
        }
    }

    async loadPersons() {
        try {
            const response = await fetch('/api/persons/');
            const persons = await response.json();
            
            const personsList = document.getElementById('persons-list');
            const selectPerson = document.getElementById('select-person');
            
            // Atualizar lista de pessoas
            personsList.innerHTML = '';
            selectPerson.innerHTML = '<option value="">Selecione uma pessoa...</option>';
            
            persons.forEach(person => {
                // Lista de pessoas
                const personDiv = document.createElement('div');
                personDiv.className = 'alert alert-light d-flex justify-content-between align-items-center';
                personDiv.innerHTML = `
                    <div>
                        <strong>${person.name}</strong>
                        ${person.description ? `<br><small class="text-muted">${person.description}</small>` : ''}
                    </div>
                    <button class="btn btn-sm btn-outline-danger" onclick="app.deletePerson(${person.id})">
                        <i class="fas fa-trash"></i>
                    </button>
                `;
                personsList.appendChild(personDiv);
                
                // Select de pessoas
                const option = document.createElement('option');
                option.value = person.id;
                option.textContent = person.name;
                selectPerson.appendChild(option);
            });
        } catch (error) {
            console.error('Erro ao carregar pessoas:', error);
        }
    }

    async addPerson() {
        const name = document.getElementById('person-name').value;
        const description = document.getElementById('person-description').value;
        
        try {
            const response = await fetch('/api/persons/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, description })
            });
            
            if (response.ok) {
                document.getElementById('person-form').reset();
                this.loadPersons();
                this.loadStats();
                this.showAlert('Pessoa adicionada com sucesso!', 'success');
            } else {
                const error = await response.json();
                this.showAlert(error.detail || 'Erro ao adicionar pessoa', 'danger');
            }
        } catch (error) {
            console.error('Erro ao adicionar pessoa:', error);
            this.showAlert('Erro ao adicionar pessoa', 'danger');
        }
    }

    async deletePerson(personId) {
        if (!confirm('Tem certeza que deseja remover esta pessoa?')) return;
        
        try {
            const response = await fetch(`/api/persons/${personId}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                this.loadPersons();
                this.loadStats();
                this.showAlert('Pessoa removida com sucesso!', 'success');
            } else {
                this.showAlert('Erro ao remover pessoa', 'danger');
            }
        } catch (error) {
            console.error('Erro ao remover pessoa:', error);
            this.showAlert('Erro ao remover pessoa', 'danger');
        }
    }

    async uploadImages() {
        const personId = document.getElementById('select-person').value;
        const files = document.getElementById('image-files').files;
        
        if (!personId || !files.length) return;
        
        const formData = new FormData();
        Array.from(files).forEach(file => {
            formData.append('files', file);
        });
        
        try {
            const response = await fetch(`/api/persons/${personId}/upload-images`, {
                method: 'POST',
                body: formData
            });
            
            if (response.ok) {
                const result = await response.json();
                document.getElementById('image-files').value = '';
                document.getElementById('upload-btn').disabled = true;
                this.loadStats();
                this.showAlert(result.message, 'success');
            } else {
                const error = await response.json();
                this.showAlert(error.detail || 'Erro no upload', 'danger');
            }
        } catch (error) {
            console.error('Erro no upload:', error);
            this.showAlert('Erro no upload das imagens', 'danger');
        }
    }

    async recognizeImage() {
        const file = document.getElementById('recognition-file').files[0];
        if (!file) return;
        
        const formData = new FormData();
        formData.append('file', file);
        
        try {
            const response = await fetch('/api/recognition/recognize-image', {
                method: 'POST',
                body: formData
            });
            
            if (response.ok) {
                const result = await response.json();
                this.displayRecognitionResults(result);
                this.loadStats();
            } else {
                const error = await response.json();
                this.showAlert(error.detail || 'Erro no reconhecimento', 'danger');
            }
        } catch (error) {
            console.error('Erro no reconhecimento:', error);
            this.showAlert('Erro no reconhecimento da imagem', 'danger');
        }
    }

    displayRecognitionResults(result) {
        const resultsDiv = document.getElementById('recognition-results');
        
        if (result.faces_detected === 0) {
            resultsDiv.innerHTML = '<div class="alert alert-info">Nenhuma face detectada na imagem.</div>';
            return;
        }
        
        let html = `<div class="alert alert-success">${result.faces_detected} face(s) detectada(s):</div>`;
        
        result.recognitions.forEach((recognition, index) => {
            const alertClass = recognition.person_id ? 'alert-success' : 'alert-warning';
            html += `
                <div class="alert ${alertClass}">
                    <strong>Face ${index + 1}:</strong> ${recognition.person_name}
                    <br><small>Confiança: ${(recognition.confidence * 100).toFixed(1)}%</small>
                </div>
            `;
        });
        
        resultsDiv.innerHTML = html;
    }

    async loadStreams() {
        try {
            const response = await fetch('/api/rtsp/streams');
            const streams = await response.json();
            
            const streamsList = document.getElementById('streams-list');
            streamsList.innerHTML = '';
            
            if (streams.length === 0) {
                streamsList.innerHTML = '<p class="text-muted">Nenhum stream ativo</p>';
                return;
            }
            
            streams.forEach(stream => {
                const streamDiv = document.createElement('div');
                streamDiv.className = 'alert alert-light d-flex justify-content-between align-items-center';
                streamDiv.innerHTML = `
                    <div>
                        <strong>${stream.stream_id}</strong>
                        <br><small class="text-muted">FPS: ${stream.fps.toFixed(1)} | Frames: ${stream.frame_count}</small>
                    </div>
                    <div>
                        <button class="btn btn-sm btn-primary me-2" onclick="app.viewStream('${stream.stream_id}')">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button class="btn btn-sm btn-danger" onclick="app.removeStream('${stream.stream_id}')">
                            <i class="fas fa-stop"></i>
                        </button>
                    </div>
                `;
                streamsList.appendChild(streamDiv);
            });
        } catch (error) {
            console.error('Erro ao carregar streams:', error);
        }
    }

    async addRTSPStream() {
        const streamId = document.getElementById('stream-id').value;
        const rtspUrl = document.getElementById('rtsp-url').value;
        
        try {
            const response = await fetch('/api/rtsp/streams', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ stream_id: streamId, rtsp_url: rtspUrl })
            });
            
            if (response.ok) {
                document.getElementById('rtsp-form').reset();
                this.loadStreams();
                this.loadStats();
                this.showAlert('Stream adicionado com sucesso!', 'success');
            } else {
                const error = await response.json();
                this.showAlert(error.detail || 'Erro ao adicionar stream', 'danger');
            }
        } catch (error) {
            console.error('Erro ao adicionar stream:', error);
            this.showAlert('Erro ao adicionar stream', 'danger');
        }
    }

    async removeStream(streamId) {
        if (!confirm('Tem certeza que deseja parar este stream?')) return;
        
        try {
            const response = await fetch(`/api/rtsp/streams/${streamId}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                this.loadStreams();
                this.loadStats();
                this.showAlert('Stream removido com sucesso!', 'success');
            } else {
                this.showAlert('Erro ao remover stream', 'danger');
            }
        } catch (error) {
            console.error('Erro ao remover stream:', error);
            this.showAlert('Erro ao remover stream', 'danger');
        }
    }

    viewStream(streamId) {
        window.open(`/api/rtsp/streams/${streamId}/mjpeg`, '_blank');
    }

    async loadLogs() {
        try {
            const response = await fetch('/api/logs?limit=10');
            const data = await response.json();
            
            const logsTable = document.getElementById('logs-table');
            logsTable.innerHTML = '';
            
            if (data.logs.length === 0) {
                logsTable.innerHTML = '<tr><td colspan="5" class="text-center text-muted">Nenhum log encontrado</td></tr>';
                return;
            }
            
            data.logs.forEach(log => {
                const row = document.createElement('tr');
                const date = new Date(log.detected_at).toLocaleString('pt-BR');
                const confidence = (log.confidence * 100).toFixed(1);
                
                row.innerHTML = `
                    <td>${date}</td>
                    <td>${log.person_name}</td>
                    <td>${confidence}%</td>
                    <td>${log.source}</td>
                    <td>${log.source_info || '-'}</td>
                `;
                logsTable.appendChild(row);
            });
        } catch (error) {
            console.error('Erro ao carregar logs:', error);
        }
    }

    showAlert(message, type) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; max-width: 300px;';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(alertDiv);
        
        // Remover automaticamente após 5 segundos
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.parentNode.removeChild(alertDiv);
            }
        }, 5000);
    }
}

// Inicializar aplicação
const app = new NewFacialApp(); 