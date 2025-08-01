class AgentConfig {
    constructor() {
        this.form = document.getElementById('configForm');
        this.initializeEventListeners();
        this.loadCurrentConfig();
    }

    initializeEventListeners() {
        this.form.addEventListener('submit', (e) => this.handleSubmit(e));
    }

    async loadCurrentConfig() {
        try {
            const response = await fetch('/config/api/config');
            if (response.ok) {
                const config = await response.json();
                this.populateForm(config);
            } else {
                console.log('Loading default configuration');
                this.loadDefaults();
            }
        } catch (error) {
            console.error('Error loading config:', error);
            this.loadDefaults();
        }
    }

    populateForm(config) {
        // Basic information
        document.getElementById('agentName').value = config.name || 'Anna';
        document.getElementById('agentModel').value = config.model || 'gemini-2.0-flash';
        document.getElementById('agentDescription').value = config.description || '';
        document.getElementById('agentInstructions').value = config.instructions || '';
        
        // Advanced settings
        document.getElementById('temperature').value = config.temperature || 0.7;
        document.getElementById('temperatureValue').textContent = config.temperature || 0.7;
        document.getElementById('maxTokens').value = config.max_tokens || 1000;

        // Tools
        const tools_enabled = config.tools_enabled || {};
        document.getElementById('tool_routines').checked = tools_enabled.routines === true;
        document.getElementById('tool_media').checked = tools_enabled.media === true;
        document.getElementById('tool_memories').checked = tools_enabled.memories === true;
    }

    loadDefaults() {
        const defaultConfig = {
            name: 'Anna',
            model: 'gemini-2.0-flash',
            description: 'Uma criadora de conteúdo brasileira carismática e autêntica que compartilha sua rotina diária.',
            instructions: `Você é Anna, uma criadora de conteúdo brasileira de 24 anos, carismática e autêntica. Você tem uma personalidade vibrante e espontânea, sempre usando emojis e expressões informais típicas do português brasileiro.

PERSONALIDADE:
- Carismática e divertida, sempre com energia positiva
- Usa linguagem informal e expressões brasileiras naturais  
- Inclui emojis relevantes nas suas respostas
- É aberta sobre sua rotina e atividades diárias
- Gosta de interagir e fazer os seguidores se sentirem próximos

COMPORTAMENTO:
- SEMPRE chame as funções de banco de dados antes de responder qualquer pergunta
- Use informações reais do seu banco de dados sobre rotinas, fotos, vídeos e conversas
- Nunca invente informações - apenas use dados reais disponíveis
- Mencione atividades específicas, horários e locais baseados nos seus dados reais
- Referencie fotos e vídeos reais quando disponíveis

ESTILO DE RESPOSTA:
- Respostas conversacionais e naturais
- Use "amor", "gente", "pessoal" para se dirigir aos seguidores
- Inclua detalhes da sua rotina real baseados nos dados do banco
- Seja específica sobre horários, locais e atividades
- Mencione quando tem fotos ou vídeos para compartilhar

IMPORTANTE: Sempre consulte seus dados reais antes de responder. Nunca invente informações sobre sua rotina, atividades ou mídia.`,
            tools_enabled: {
                routines: true,
                media: true,
                memories: true
            },
            temperature: 0.7,
            max_tokens: 1000
        };
        
        this.populateForm(defaultConfig);
    }

    async handleSubmit(e) {
        e.preventDefault();
        
        const formData = new FormData(this.form);
        const config = this.formDataToConfig(formData);
        
        console.log('Saving config:', config);
        
        try {
            const response = await fetch('/config/api/config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(config)
            });
            
            console.log('Response status:', response.status);
            const result = await response.json();
            console.log('Response data:', result);
            
            if (response.ok) {
                this.showAlert('Configuração salva com sucesso! Agente reinicializado.', 'success');
                
                // Update form with saved config if available
                if (result.config) {
                    this.populateForm(result.config);
                }
            } else {
                this.showAlert(result.error || 'Erro ao salvar configuração', 'danger');
                console.error('Save error:', result);
            }
        } catch (error) {
            console.error('Error saving config:', error);
            this.showAlert('Erro ao salvar configuração: ' + error.message, 'danger');
        }
    }

    formDataToConfig(formData) {
        const config = {
            name: formData.get('name') || 'Anna',
            model: formData.get('model') || 'gemini-2.0-flash',
            description: formData.get('description') || '',
            instructions: formData.get('instructions') || '',
            temperature: parseFloat(formData.get('temperature')) || 0.7,
            max_tokens: parseInt(formData.get('max_tokens')) || 1000,
            tools_enabled: {
                routines: document.getElementById('tool_routines').checked,
                media: document.getElementById('tool_media').checked,
                memories: document.getElementById('tool_memories').checked
            }
        };
        
        console.log('Converted form data to config:', config);
        return config;
    }

    showAlert(message, type = 'info') {
        const alertContainer = document.getElementById('alertContainer');
        const alertId = 'alert-' + Date.now();
        
        const alertHtml = `
            <div id="${alertId}" class="alert alert-${type} alert-dismissible fade show" role="alert">
                <i data-feather="${type === 'success' ? 'check-circle' : 'alert-circle'}" class="me-2"></i>
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        alertContainer.innerHTML = alertHtml;
        feather.replace();
        
        // Auto dismiss after 5 seconds
        setTimeout(() => {
            const alert = document.getElementById(alertId);
            if (alert) {
                bootstrap.Alert.getOrCreateInstance(alert).close();
            }
        }, 5000);
    }
}

// Global functions for buttons
function loadDefaults() {
    if (window.agentConfig) {
        window.agentConfig.loadDefaults();
    }
}

function previewConfig() {
    const formData = new FormData(document.getElementById('configForm'));
    const config = window.agentConfig.formDataToConfig(formData);
    
    document.getElementById('previewContent').textContent = JSON.stringify(config, null, 2);
    
    const modal = new bootstrap.Modal(document.getElementById('previewModal'));
    modal.show();
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.agentConfig = new AgentConfig();
});