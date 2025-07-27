class AdminManager {
    constructor() {
        this.calendar = null;
        this.currentActivity = null;
        this.mediaFiles = [];
        this.existingMedia = [];
        this.currentMemory = null;
        this.currentImage = null;
        
        this.initializeCalendar();
        this.initializeEventListeners();
        this.loadTodayActivities();
        setTimeout(() => this.initializeTabHandlers(), 100);
    }

    initializeCalendar() {
        const calendarEl = document.getElementById('calendar');
        
        this.calendar = new FullCalendar.Calendar(calendarEl, {
            initialView: 'dayGridMonth',
            headerToolbar: {
                left: 'prev,next today',
                center: 'title',
                right: 'dayGridMonth,dayGridWeek'
            },
            locale: 'pt-br',
            selectable: true,
            selectMirror: true,
            dayMaxEvents: true,
            weekends: true,
            
            select: (selectInfo) => {
                this.openActivityModal(null, selectInfo.startStr);
            },
            
            eventClick: (clickInfo) => {
                this.openActivityModal(clickInfo.event.id);
            },
            
            events: '/admin/api/activities'
        });
        
        this.calendar.render();
    }

    initializeEventListeners() {
        // Media upload area
        const uploadArea = document.getElementById('mediaUploadArea');
        const fileInput = document.getElementById('mediaFiles');
        
        uploadArea.addEventListener('click', () => fileInput.click());
        uploadArea.addEventListener('dragover', this.handleDragOver.bind(this));
        uploadArea.addEventListener('drop', this.handleDrop.bind(this));
        
        fileInput.addEventListener('change', (e) => {
            this.handleFileSelect(e.target.files);
        });
        
        // Form submission
        document.getElementById('saveActivity').addEventListener('click', this.saveActivity.bind(this));
        document.getElementById('deleteActivity').addEventListener('click', this.deleteActivity.bind(this));
        
        // Modal reset
        document.getElementById('activityModal').addEventListener('hidden.bs.modal', this.resetModal.bind(this));
    }

    handleDragOver(e) {
        e.preventDefault();
        e.target.closest('.media-upload-area').classList.add('dragover');
    }

    handleDrop(e) {
        e.preventDefault();
        e.target.closest('.media-upload-area').classList.remove('dragover');
        this.handleFileSelect(e.dataTransfer.files);
    }

    handleFileSelect(files) {
        for (let file of files) {
            if (this.isValidMediaFile(file)) {
                this.mediaFiles.push(file);
                this.createMediaPreview(file);
            }
        }
    }

    isValidMediaFile(file) {
        const validTypes = ['image/jpeg', 'image/png', 'image/gif', 'video/mp4', 'video/mov', 'video/quicktime'];
        return validTypes.includes(file.type) && file.size <= 50 * 1024 * 1024; // 50MB limit
    }

    createMediaPreview(file) {
        const previewContainer = document.getElementById('mediaPreview');
        const mediaItem = document.createElement('div');
        mediaItem.className = 'media-item';
        
        const isVideo = file.type.startsWith('video/');
        const mediaElement = document.createElement(isVideo ? 'video' : 'img');
        mediaElement.className = 'media-preview';
        
        if (isVideo) {
            mediaElement.controls = true;
        }
        
        mediaElement.src = URL.createObjectURL(file);
        
        const removeBtn = document.createElement('button');
        removeBtn.className = 'media-remove';
        removeBtn.innerHTML = '×';
        removeBtn.onclick = () => {
            const index = this.mediaFiles.indexOf(file);
            if (index > -1) {
                this.mediaFiles.splice(index, 1);
            }
            mediaItem.remove();
            URL.revokeObjectURL(mediaElement.src);
        };
        
        mediaItem.appendChild(mediaElement);
        mediaItem.appendChild(removeBtn);
        previewContainer.appendChild(mediaItem);
    }

    async openActivityModal(activityId = null, selectedDate = null) {
        const modal = new bootstrap.Modal(document.getElementById('activityModal'));
        const form = document.getElementById('activityForm');
        
        this.resetModal();
        
        if (activityId) {
            // Edit existing activity
            try {
                const response = await fetch(`/admin/api/activities/${activityId}`);
                const activity = await response.json();
                this.populateForm(activity);
                this.currentActivity = activity;
                document.getElementById('modalTitle').textContent = 'Editar Atividade';
                document.getElementById('deleteActivity').style.display = 'inline-block';
            } catch (error) {
                console.error('Error loading activity:', error);
                this.showAlert('Erro ao carregar atividade', 'danger');
                return;
            }
        } else {
            // New activity
            document.getElementById('modalTitle').textContent = 'Nova Atividade';
            document.getElementById('deleteActivity').style.display = 'none';
            
            if (selectedDate) {
                document.getElementById('activityDate').value = selectedDate;
            }
        }
        
        modal.show();
    }

    populateForm(activity) {
        document.getElementById('activityId').value = activity.id;
        document.getElementById('activityDate').value = activity.date;
        document.getElementById('activityTimeStart').value = activity.time_start.substring(0, 5);
        document.getElementById('activityTimeEnd').value = activity.time_end.substring(0, 5);
        document.getElementById('activityName').value = activity.activity;
        document.getElementById('activityCategory').value = activity.category;
        document.getElementById('activityLocation').value = activity.location || '';
        document.getElementById('activityDescription').value = activity.description || '';

        
        // Load existing media
        this.loadExistingMedia(activity.id);
    }

    async loadExistingMedia(activityId) {
        try {
            const response = await fetch(`/admin/api/activities/${activityId}/media`);
            const mediaItems = await response.json();
            
            this.existingMedia = mediaItems;
            const previewContainer = document.getElementById('mediaPreview');
            
            mediaItems.forEach(media => {
                this.createExistingMediaPreview(media, previewContainer);
            });
        } catch (error) {
            console.error('Error loading media:', error);
        }
    }

    createExistingMediaPreview(media, container) {
        const mediaItem = document.createElement('div');
        mediaItem.className = 'media-item';
        mediaItem.dataset.mediaId = media.id;
        
        const isVideo = media.media_type === 'video';
        const mediaElement = document.createElement(isVideo ? 'video' : 'img');
        mediaElement.className = 'media-preview';
        
        if (isVideo) {
            mediaElement.controls = true;
        }
        
        mediaElement.src = media.media_url;
        
        const removeBtn = document.createElement('button');
        removeBtn.className = 'media-remove';
        removeBtn.innerHTML = '×';
        removeBtn.onclick = () => {
            if (confirm('Tem certeza que deseja excluir esta mídia?')) {
                this.deleteMedia(media.id, mediaItem);
            }
        };
        
        mediaItem.appendChild(mediaElement);
        mediaItem.appendChild(removeBtn);
        container.appendChild(mediaItem);
    }

    async deleteMedia(mediaId, mediaElement) {
        try {
            const response = await fetch(`/admin/api/media/${mediaId}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                mediaElement.remove();
                this.showAlert('Mídia excluída com sucesso', 'success');
            }
        } catch (error) {
            console.error('Error deleting media:', error);
            this.showAlert('Erro ao excluir mídia', 'danger');
        }
    }

    async saveActivity() {
        const form = document.getElementById('activityForm');
        const formData = new FormData(form);
        
        // Add media files
        console.log('Media files to upload:', this.mediaFiles.length);
        this.mediaFiles.forEach((file, index) => {
            console.log(`Adding file ${index}:`, file.name, file.type, file.size);
            formData.append('media_files', file);
        });
        
        const isEdit = document.getElementById('activityId').value !== '';
        const url = isEdit ? '/admin/api/activities/update' : '/admin/api/activities/create';
        
        console.log('Submitting to:', url);
        console.log('Form data entries:');
        for (let [key, value] of formData.entries()) {
            console.log(key, ':', value);
        }
        
        try {
            const response = await fetch(url, {
                method: 'POST',
                body: formData
            });
            
            console.log('Response status:', response.status);
            const result = await response.json();
            console.log('Response data:', result);
            
            if (response.ok) {
                this.showAlert(isEdit ? 'Atividade atualizada com sucesso' : 'Atividade criada com sucesso', 'success');
                bootstrap.Modal.getInstance(document.getElementById('activityModal')).hide();
                this.calendar.refetchEvents();
                this.loadTodayActivities();
            } else {
                this.showAlert(result.error || 'Erro ao salvar atividade', 'danger');
            }
        } catch (error) {
            console.error('Error saving activity:', error);
            this.showAlert('Erro ao salvar atividade: ' + error.message, 'danger');
        }
    }

    async deleteActivity() {
        if (!this.currentActivity || !confirm('Tem certeza que deseja excluir esta atividade?')) {
            return;
        }
        
        try {
            const response = await fetch(`/admin/api/activities/${this.currentActivity.id}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                this.showAlert('Atividade excluída com sucesso', 'success');
                bootstrap.Modal.getInstance(document.getElementById('activityModal')).hide();
                this.calendar.refetchEvents();
                this.loadTodayActivities();
            }
        } catch (error) {
            console.error('Error deleting activity:', error);
            this.showAlert('Erro ao excluir atividade', 'danger');
        }
    }

    async loadTodayActivities() {
        const today = new Date().toISOString().split('T')[0];
        
        try {
            const response = await fetch(`/admin/api/activities/date/${today}`);
            const activities = await response.json();
            
            this.renderTodayActivities(activities);
        } catch (error) {
            console.error('Error loading today activities:', error);
        }
    }

    renderTodayActivities(activities) {
        const container = document.getElementById('todayActivities');
        
        if (activities.length === 0) {
            container.innerHTML = '<p class="text-muted">Nenhuma atividade para hoje</p>';
            return;
        }
        
        container.innerHTML = activities.map(activity => `
            <div class="activity-card p-3 mb-2" onclick="adminManager.openActivityModal('${activity.id}')">
                <div class="d-flex justify-content-between align-items-start">
                    <div>
                        <h6 class="mb-1">${activity.activity}</h6>
                        <small class="text-muted">${activity.time_start} - ${activity.time_end}</small>
                        <br>
                        <span class="badge bg-${this.getCategoryColor(activity.category)} status-badge">${activity.category}</span>
                        <span class="badge bg-${this.getStatusColor(activity.status)} status-badge">${activity.status}</span>
                    </div>
                    <div class="text-end">
                        ${activity.has_images ? '<i data-feather="image" class="text-success me-1"></i>' : ''}
                        ${activity.has_videos ? '<i data-feather="video" class="text-info"></i>' : ''}
                    </div>
                </div>
            </div>
        `).join('');
        
        feather.replace();
    }

    getCategoryColor(category) {
        const colors = {
            'fitness': 'success',
            'trabalho': 'primary',
            'reuniao': 'warning',
            'social': 'info',
            'pessoal': 'danger'
        };
        return colors[category] || 'secondary';
    }

    getStatusColor(status) {
        const colors = {
            'upcoming': 'warning',
            'current': 'info',
            'completed': 'success'
        };
        return colors[status] || 'secondary';
    }

    resetModal() {
        const form = document.getElementById('activityForm');
        form.reset();
        
        document.getElementById('mediaPreview').innerHTML = '';
        this.mediaFiles = [];
        this.existingMedia = [];
        this.currentActivity = null;
        

    }

    showAlert(message, type = 'info') {
        // Create alert element
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(alertDiv);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }

    // Tab handling methods
    initializeTabHandlers() {
        const memoriesTab = document.getElementById('memories-tab');
        const imagesTab = document.getElementById('images-tab');
        const knowledgeTab = document.getElementById('knowledge-tab');
        const activitiesTab = document.getElementById('activities-tab');
        const actionType = document.getElementById('actionType');
        const imageUrl = document.getElementById('imageUrl');
        
        if (memoriesTab) {
            memoriesTab.addEventListener('click', () => {
                this.loadMemories();
            });
        }
        
        if (imagesTab) {
            imagesTab.addEventListener('click', () => {
                this.loadImages();
            });
        }
        
        if (knowledgeTab) {
            knowledgeTab.addEventListener('click', () => {
                this.loadKnowledge();
            });
        }
        
        if (activitiesTab) {
            activitiesTab.addEventListener('click', () => {
                this.loadCalendar();
            });
        }
        
        // Action type handler for routines
        if (actionType) {
            actionType.addEventListener('change', (e) => {
                const envioFields = document.getElementById('envioFields');
                if (envioFields) {
                    if (e.target.value === 'envio') {
                        envioFields.style.display = 'block';
                        this.loadImagesForSelect();
                    } else {
                        envioFields.style.display = 'none';
                    }
                }
            });
        }
        
        // Image URL preview
        if (imageUrl) {
            imageUrl.addEventListener('input', (e) => {
                this.updateImagePreview(e.target.value);
            });
        }
    }

    // Memory management methods
    async loadMemories() {
        try {
            const response = await fetch('/admin/api/memories');
            const data = await response.json();
            
            if (data.success) {
                this.renderMemories(data.memories);
            } else {
                console.error('Error loading memories:', data.error);
            }
        } catch (error) {
            console.error('Error loading memories:', error);
        }
    }

    renderMemories(memories) {
        const container = document.getElementById('memories-list');
        container.innerHTML = '';
        
        memories.forEach(memory => {
            const memoryCard = document.createElement('div');
            memoryCard.className = 'card mb-3';
            memoryCard.innerHTML = `
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-start">
                        <div>
                            <h6 class="card-title">${memory.name}</h6>
                            <p class="card-text text-muted">${memory.description}</p>
                            <small class="text-muted">Quando usar: ${memory.when_to_use || 'Não especificado'}</small>
                        </div>
                        <div class="btn-group btn-group-sm">
                            <button class="btn btn-outline-primary" onclick="adminManager.editMemory(${memory.id})">
                                <i data-feather="edit-2"></i>
                            </button>
                            <button class="btn btn-outline-danger" onclick="adminManager.deleteMemoryConfirm(${memory.id})">
                                <i data-feather="trash-2"></i>
                            </button>
                        </div>
                    </div>
                    ${memory.keywords && memory.keywords.length > 0 ? `
                        <div class="mt-2">
                            ${memory.keywords.map(keyword => `<span class="badge bg-secondary me-1">${keyword}</span>`).join('')}
                        </div>
                    ` : ''}
                </div>
            `;
            container.appendChild(memoryCard);
        });
        
        // Re-initialize feather icons
        feather.replace();
    }

    editMemory(memoryId) {
        // Load memory data and open modal
        fetch(`/admin/api/memories`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const memory = data.memories.find(m => m.id === memoryId);
                    if (memory) {
                        this.openMemoryModal(memory);
                    }
                }
            });
    }

    openMemoryModal(memory = null) {
        this.currentMemory = memory;
        const modal = new bootstrap.Modal(document.getElementById('memoryModal'));
        
        if (memory) {
            document.getElementById('memoryModalTitle').textContent = 'Editar Memória';
            document.getElementById('memoryId').value = memory.id;
            document.getElementById('memoryName').value = memory.name;
            document.getElementById('memoryDescription').value = memory.description;
            document.getElementById('memoryWhenToUse').value = memory.when_to_use || '';
            document.getElementById('memoryContent').value = memory.content || '';
            document.getElementById('memoryKeywords').value = memory.keywords ? memory.keywords.join(', ') : '';
            document.getElementById('deleteMemory').style.display = 'inline-block';
        } else {
            document.getElementById('memoryModalTitle').textContent = 'Nova Memória';
            document.getElementById('memoryForm').reset();
            document.getElementById('deleteMemory').style.display = 'none';
        }
        
        modal.show();
    }

    async saveMemory() {
        const form = document.getElementById('memoryForm');
        const formData = new FormData(form);
        
        const memoryData = {
            name: formData.get('name'),
            description: formData.get('description'),
            when_to_use: formData.get('when_to_use'),
            content: formData.get('content'),
            keywords: formData.get('keywords').split(',').map(k => k.trim()).filter(k => k)
        };
        
        try {
            const memoryId = formData.get('id');
            const url = memoryId ? `/admin/api/memories/${memoryId}` : '/admin/api/memories';
            const method = memoryId ? 'PUT' : 'POST';
            
            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(memoryData)
            });
            
            const result = await response.json();
            
            if (result.success) {
                bootstrap.Modal.getInstance(document.getElementById('memoryModal')).hide();
                this.loadMemories();
            } else {
                alert('Erro ao salvar memória: ' + result.error);
            }
        } catch (error) {
            alert('Erro ao salvar memória: ' + error.message);
        }
    }

    // Image management methods
    async loadImages() {
        try {
            const response = await fetch('/admin/api/images');
            const data = await response.json();
            
            if (data.success) {
                this.renderImages(data.images);
            } else {
                console.error('Error loading images:', data.error);
            }
        } catch (error) {
            console.error('Error loading images:', error);
        }
    }

    renderImages(images) {
        const container = document.getElementById('images-list');
        container.innerHTML = '';
        
        const row = document.createElement('div');
        row.className = 'row';
        
        images.forEach(image => {
            const imageCard = document.createElement('div');
            imageCard.className = 'col-md-6 col-lg-4 mb-4';
            imageCard.innerHTML = `
                <div class="card">
                    <img src="${image.image_url}" class="card-img-top" style="height: 200px; object-fit: cover;" alt="${image.name}">
                    <div class="card-body">
                        <h6 class="card-title">${image.name}</h6>
                        <p class="card-text text-muted small">${image.description}</p>
                        ${image.keywords && image.keywords.length > 0 ? `
                            <div class="mb-2">
                                ${image.keywords.map(keyword => `<span class="badge bg-secondary me-1">${keyword}</span>`).join('')}
                            </div>
                        ` : ''}
                        <div class="btn-group btn-group-sm w-100">
                            <button class="btn btn-outline-primary" onclick="adminManager.editImage(${image.id})">
                                <i data-feather="edit-2"></i>
                            </button>
                            <button class="btn btn-outline-danger" onclick="adminManager.deleteImageConfirm(${image.id})">
                                <i data-feather="trash-2"></i>
                            </button>
                        </div>
                    </div>
                </div>
            `;
            row.appendChild(imageCard);
        });
        
        container.appendChild(row);
        feather.replace();
    }

    editImage(imageId) {
        fetch(`/admin/api/images`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const image = data.images.find(i => i.id === imageId);
                    if (image) {
                        this.openImageModal(image);
                    }
                }
            });
    }

    openImageModal(image = null) {
        this.currentImage = image;
        const modal = new bootstrap.Modal(document.getElementById('imageModal'));
        
        if (image) {
            document.getElementById('imageModalTitle').textContent = 'Editar Imagem';
            document.getElementById('imageId').value = image.id;
            document.getElementById('imageName').value = image.name;
            document.getElementById('imageUrl').value = image.image_url;
            document.getElementById('imageDescription').value = image.description;
            document.getElementById('imageWhenToUse').value = image.when_to_use || '';
            document.getElementById('imageKeywords').value = image.keywords ? image.keywords.join(', ') : '';
            document.getElementById('deleteImage').style.display = 'inline-block';
            this.updateImagePreview(image.image_url);
        } else {
            document.getElementById('imageModalTitle').textContent = 'Nova Imagem';
            document.getElementById('imageForm').reset();
            document.getElementById('deleteImage').style.display = 'none';
            this.updateImagePreview('');
        }
        
        modal.show();
    }

    updateImagePreview(url) {
        const preview = document.getElementById('previewImg');
        const placeholder = document.querySelector('#imagePreview .text-muted');
        
        if (url) {
            preview.src = url;
            preview.style.display = 'block';
            placeholder.style.display = 'none';
        } else {
            preview.style.display = 'none';
            placeholder.style.display = 'block';
        }
    }

    async saveImage() {
        const form = document.getElementById('imageForm');
        const formData = new FormData(form);
        
        const imageData = {
            name: formData.get('name'),
            image_url: formData.get('image_url'),
            description: formData.get('description'),
            when_to_use: formData.get('when_to_use'),
            keywords: formData.get('keywords').split(',').map(k => k.trim()).filter(k => k)
        };
        
        try {
            const imageId = formData.get('id');
            const url = imageId ? `/admin/api/images/${imageId}` : '/admin/api/images';
            const method = imageId ? 'PUT' : 'POST';
            
            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(imageData)
            });
            
            const result = await response.json();
            
            if (result.success) {
                bootstrap.Modal.getInstance(document.getElementById('imageModal')).hide();
                this.loadImages();
            } else {
                alert('Erro ao salvar imagem: ' + result.error);
            }
        } catch (error) {
            alert('Erro ao salvar imagem: ' + error.message);
        }
    }

    async loadImagesForSelect() {
        try {
            const response = await fetch('/admin/api/images');
            const data = await response.json();
            
            if (data.success) {
                const select = document.getElementById('envioImage');
                select.innerHTML = '<option value="">Selecione uma imagem...</option>';
                
                data.images.forEach(image => {
                    const option = document.createElement('option');
                    option.value = image.id;
                    option.textContent = image.name;
                    select.appendChild(option);
                });
            }
        } catch (error) {
            console.error('Error loading images for select:', error);
        }
    }

    deleteMemoryConfirm(memoryId) {
        if (confirm('Tem certeza que deseja excluir esta memória?')) {
            this.deleteMemory(memoryId);
        }
    }

    async deleteMemory(memoryId) {
        try {
            const response = await fetch(`/admin/api/memories/${memoryId}`, {
                method: 'DELETE'
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.loadMemories();
            } else {
                alert('Erro ao excluir memória: ' + result.error);
            }
        } catch (error) {
            alert('Erro ao excluir memória: ' + error.message);
        }
    }

    deleteImageConfirm(imageId) {
        if (confirm('Tem certeza que deseja excluir esta imagem?')) {
            this.deleteImage(imageId);
        }
    }

    async deleteImage(imageId) {
        try {
            const response = await fetch(`/admin/api/images/${imageId}`, {
                method: 'DELETE'
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.loadImages();
            } else {
                alert('Erro ao excluir imagem: ' + result.error);
            }
        } catch (error) {
            alert('Erro ao excluir imagem: ' + error.message);
        }
    }

    // Knowledge management methods
    loadKnowledge() {
        console.log('Loading knowledge bank...');
        const knowledgeList = document.getElementById('knowledge-list');
        if (!knowledgeList) return;

        // For now, show placeholder for knowledge bank
        knowledgeList.innerHTML = `
            <div class="alert alert-info">
                <h6>Banco de Conhecimento</h6>
                <p>Aqui serão armazenados artigos, documentos e conteúdo educacional da Anna.</p>
                <p class="mb-0"><em>Funcionalidade em desenvolvimento...</em></p>
            </div>
        `;
    }

    loadCalendar() {
        console.log('Loading calendar for activities...');
        // The calendar is already initialized, just ensure it's visible
        const calendar = document.getElementById('calendar');
        if (calendar && this.calendar) {
            this.calendar.render();
        }
    }
}

// Global functions for modals
function openKnowledgeModal() {
    // Placeholder for knowledge modal
    alert('Funcionalidade do Banco de Conhecimento em desenvolvimento');
}

// Global functions for modal handling
function openMemoryModal() {
    window.adminManager.openMemoryModal();
}

function openImageModal() {
    window.adminManager.openImageModal();
}

// Add event listeners for save buttons when DOM loads
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(() => {
        if (document.getElementById('saveMemory')) {
            document.getElementById('saveMemory').addEventListener('click', () => {
                window.adminManager.saveMemory();
            });
        }
        
        if (document.getElementById('saveImage')) {
            document.getElementById('saveImage').addEventListener('click', () => {
                window.adminManager.saveImage();
            });
        }
        
        if (document.getElementById('deleteMemory')) {
            document.getElementById('deleteMemory').addEventListener('click', () => {
                if (window.adminManager.currentMemory) {
                    window.adminManager.deleteMemoryConfirm(window.adminManager.currentMemory.id);
                }
            });
        }
        
        if (document.getElementById('deleteImage')) {
            document.getElementById('deleteImage').addEventListener('click', () => {
                if (window.adminManager.currentImage) {
                    window.adminManager.deleteImageConfirm(window.adminManager.currentImage.id);
                }
            });
        }
    }, 100);
});