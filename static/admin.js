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
        // Media upload area - check if elements exist first
        const uploadArea = document.getElementById('mediaUploadArea');
        const fileInput = document.getElementById('mediaFiles');
        
        if (uploadArea && fileInput) {
            uploadArea.addEventListener('click', () => fileInput.click());
            uploadArea.addEventListener('dragover', this.handleDragOver.bind(this));
            uploadArea.addEventListener('drop', this.handleDrop.bind(this));
            
            fileInput.addEventListener('change', (e) => {
                this.handleFileSelect(e.target.files);
            });
        }
        
        // Form submission - check if elements exist
        const saveActivityBtn = document.getElementById('saveActivity');
        const deleteActivityBtn = document.getElementById('deleteActivity');
        const activityModal = document.getElementById('activityModal');
        
        if (saveActivityBtn) {
            saveActivityBtn.addEventListener('click', this.saveActivity.bind(this));
        }
        
        if (deleteActivityBtn) {
            deleteActivityBtn.addEventListener('click', this.deleteActivity.bind(this));
        }
        
        if (activityModal) {
            activityModal.addEventListener('hidden.bs.modal', this.resetModal.bind(this));
        }
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
        const saveBtn = document.getElementById('saveActivityBtn');
        const originalText = saveBtn.innerHTML;
        
        try {
            // Show loading state
            saveBtn.disabled = true;
            saveBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status"></span>Salvando...';
            
            if (!document.getElementById('activityName').value) {
                this.showErrorMessage('Nome da atividade é obrigatório');
                return;
            }

            if (!document.getElementById('activityDate').value) {
                this.showErrorMessage('Data é obrigatória');
                return;
            }
            
            if (!document.getElementById('activityCategory').value) {
                this.showErrorMessage('Categoria é obrigatória');
                return;
            }

            // Handle file uploads first if any
            const fileInput = document.getElementById('activityMediaUpload');
            const mediaUrls = [];
            
            // Process uploaded files from new input
            if (fileInput && fileInput.files.length > 0) {
                for (const file of fileInput.files) {
                    const formData = new FormData();
                    formData.append('file', file);

                    const uploadResponse = await fetch('/admin/api/upload-media', {
                        method: 'POST',
                        body: formData
                    });

                    if (uploadResponse.ok) {
                        const uploadResult = await uploadResponse.json();
                        mediaUrls.push(uploadResult.url);
                    } else {
                        console.error('Failed to upload file:', file.name);
                    }
                }
            }
            
            // Also process existing media files from old system
            if (this.mediaFiles && this.mediaFiles.length > 0) {
                for (const file of this.mediaFiles) {
                    const formData = new FormData();
                    formData.append('file', file);

                    const uploadResponse = await fetch('/admin/api/upload-media', {
                        method: 'POST',
                        body: formData
                    });

                    if (uploadResponse.ok) {
                        const uploadResult = await uploadResponse.json();
                        mediaUrls.push(uploadResult.url);
                    } else {
                        console.error('Failed to upload file:', file.name);
                    }
                }
            }
            
            // Process URLs from textarea
            const urlInputElement = document.getElementById('activityMediaUrls');
            if (urlInputElement) {
                const urlsText = urlInputElement.value.trim();
                if (urlsText) {
                    const urls = urlsText.split('\n').map(url => url.trim()).filter(url => url);
                    mediaUrls.push(...urls);
                }
            }

            const activityData = {
                activity: document.getElementById('activityName').value,
                date: document.getElementById('activityDate').value,
                time_start: document.getElementById('activityStartTime').value || '09:00',
                time_end: document.getElementById('activityEndTime').value || '10:00',
                description: document.getElementById('activityDescription').value,
                location: document.getElementById('activityLocation').value,
                category: document.getElementById('activityCategory').value,
                media_urls: mediaUrls,
                status: 'upcoming'
            };

            console.log('Sending activity data:', activityData);

            const response = await fetch('/admin/api/activities/create', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(activityData)
            });

            const result = await response.json();
            
            if (response.ok) {
                this.showSuccessMessage('Atividade criada com sucesso!');
                bootstrap.Modal.getInstance(document.getElementById('activityModal')).hide();
                if (this.calendar) this.calendar.refetchEvents();
                if (this.loadTodayActivities) this.loadTodayActivities();
            } else {
                console.error('Server response:', response.status, result);
                this.showErrorMessage(this.getErrorMessage(result.error || 'Erro desconhecido'));
            }
        } catch (error) {
            console.error('Error saving activity:', error);
            this.showErrorMessage('Erro ao salvar atividade: ' + error.message);
        } finally {
            // Reset button state
            saveBtn.disabled = false;
            saveBtn.innerHTML = originalText;
        }
    }
    
    showErrorMessage(message) {
        // Create or update error alert
        let alertDiv = document.getElementById('errorAlert');
        if (!alertDiv) {
            alertDiv = document.createElement('div');
            alertDiv.id = 'errorAlert';
            alertDiv.className = 'alert alert-danger';
            alertDiv.style.position = 'fixed';
            alertDiv.style.top = '20px';
            alertDiv.style.right = '20px';
            alertDiv.style.zIndex = '9999';
            alertDiv.style.minWidth = '300px';
            document.body.appendChild(alertDiv);
        }
        alertDiv.innerHTML = `<strong>Erro:</strong> ${message}`;
        alertDiv.style.display = 'block';
        setTimeout(() => alertDiv.style.display = 'none', 5000);
    }
    
    showSuccessMessage(message) {
        // Create or update success alert
        let alertDiv = document.getElementById('successAlert');
        if (!alertDiv) {
            alertDiv = document.createElement('div');
            alertDiv.id = 'successAlert';
            alertDiv.className = 'alert alert-success';
            alertDiv.style.position = 'fixed';
            alertDiv.style.top = '20px';
            alertDiv.style.right = '20px';
            alertDiv.style.zIndex = '9999';
            alertDiv.style.minWidth = '300px';
            document.body.appendChild(alertDiv);
        }
        alertDiv.innerHTML = `<strong>Sucesso:</strong> ${message}`;
        alertDiv.style.display = 'block';
        setTimeout(() => alertDiv.style.display = 'none', 3000);
    }
    
    getErrorMessage(error) {
        if (typeof error === 'string') {
            if (error.includes('category_check')) {
                return 'Categoria inválida. Use: trabalho, social, pessoal, conteudo ou outros';
            }
            if (error.includes('Campo obrigatório')) {
                return error;
            }
        }
        return 'Erro desconhecido ao salvar atividade';
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

    // Agent configuration methods
    async loadAgentConfig() {
        try {
            const response = await fetch('/config/api/config');
            if (response.ok) {
                const config = await response.json();
                document.getElementById('agentName').value = config.name || 'Anna';
                document.getElementById('agentModel').value = config.model || 'gemini-2.0-flash';
                document.getElementById('agentDescription').value = config.description || '';
                document.getElementById('agentInstructions').value = config.instructions || '';
                document.getElementById('agentTemperature').value = config.temperature || 0.7;
                document.getElementById('agentMaxTokens').value = config.max_tokens || 1000;
                
                // Set tool checkboxes
                const tools = config.tools || [];
                document.getElementById('toolRoutines').checked = tools.includes('get_anna_routines');
                document.getElementById('toolMemories').checked = tools.includes('search_memories');
                document.getElementById('toolMedia').checked = tools.includes('get_anna_routine_media');
            }
        } catch (error) {
            console.error('Error loading agent config:', error);
        }
    }

    async saveAgentConfig() {
        const saveBtn = document.getElementById('saveAgentConfigBtn');
        const originalText = saveBtn.innerHTML;
        
        try {
            // Show loading state
            saveBtn.disabled = true;
            saveBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status"></span>Salvando...';
            
            const tools = [];
            if (document.getElementById('toolRoutines').checked) tools.push('get_anna_routines');
            if (document.getElementById('toolMemories').checked) tools.push('search_memories');
            if (document.getElementById('toolMedia').checked) tools.push('get_anna_routine_media');
            tools.push('get_recent_conversations', 'search_content', 'save_conversation_memory');

            const config = {
                name: document.getElementById('agentName').value,
                model: document.getElementById('agentModel').value,
                description: document.getElementById('agentDescription').value,
                instructions: document.getElementById('agentInstructions').value,
                temperature: parseFloat(document.getElementById('agentTemperature').value),
                max_tokens: parseInt(document.getElementById('agentMaxTokens').value),
                tools: tools
            };

            console.log('Salvando configuração:', config);

            const response = await fetch('/config/api/config', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(config)
            });

            const result = await response.json();

            if (response.ok) {
                this.showGlobalSuccessMessage('Configuração salva com sucesso!');
            } else {
                this.showGlobalErrorMessage('Erro ao salvar: ' + (result.error || 'Erro desconhecido'));
            }
        } catch (error) {
            console.error('Error saving config:', error);
            this.showGlobalErrorMessage('Erro ao salvar configuração: ' + error.message);
        } finally {
            // Reset button state
            saveBtn.disabled = false;
            saveBtn.innerHTML = originalText;
        }
    }
    
    showGlobalErrorMessage(message) {
        // Create or update error alert
        let alertDiv = document.getElementById('globalErrorAlert');
        if (!alertDiv) {
            alertDiv = document.createElement('div');
            alertDiv.id = 'globalErrorAlert';
            alertDiv.className = 'alert alert-danger';
            alertDiv.style.position = 'fixed';
            alertDiv.style.top = '20px';
            alertDiv.style.right = '20px';
            alertDiv.style.zIndex = '9999';
            alertDiv.style.minWidth = '300px';
            document.body.appendChild(alertDiv);
        }
        alertDiv.innerHTML = `<strong>Erro:</strong> ${message}`;
        alertDiv.style.display = 'block';
        setTimeout(() => alertDiv.style.display = 'none', 5000);
    }

    showGlobalSuccessMessage(message) {
        // Create or update success alert
        let alertDiv = document.getElementById('globalSuccessAlert');
        if (!alertDiv) {
            alertDiv = document.createElement('div');
            alertDiv.id = 'globalSuccessAlert';
            alertDiv.className = 'alert alert-success';
            alertDiv.style.position = 'fixed';
            alertDiv.style.top = '20px';
            alertDiv.style.right = '20px';
            alertDiv.style.zIndex = '9999';
            alertDiv.style.minWidth = '300px';
            document.body.appendChild(alertDiv);
        }
        alertDiv.innerHTML = `<strong>Sucesso:</strong> ${message}`;
        alertDiv.style.display = 'block';
        setTimeout(() => alertDiv.style.display = 'none', 3000);
    }

    // Image upload functionality
    async uploadImage() {
        const fileInput = document.getElementById('imageUpload');
        const file = fileInput.files[0];
        
        if (!file) return;

        try {
            const formData = new FormData();
            formData.append('file', file);

            const response = await fetch('/admin/api/upload-image', {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                const result = await response.json();
                alert('Imagem enviada com sucesso!');
                this.loadImages(); // Reload images list
                fileInput.value = ''; // Clear file input
            } else {
                throw new Error('Erro no upload da imagem');
            }
        } catch (error) {
            alert('Erro ao enviar imagem: ' + error.message);
        }
    }

    // Enhanced image loading with grid display
    async loadImages() {
        try {
            const response = await fetch('/admin/api/images');
            if (response.ok) {
                const data = await response.json();
                const imagesList = document.getElementById('images-list');
                
                if (data.success && data.images.length > 0) {
                    imagesList.innerHTML = data.images.map(image => `
                        <div class="col-md-4 mb-3">
                            <div class="card">
                                <img src="${image.image_url}" class="card-img-top" style="height: 200px; object-fit: cover;" 
                                     alt="${image.name}" onerror="this.src='/static/placeholder.jpg'">
                                <div class="card-body">
                                    <h6 class="card-title">${image.name}</h6>
                                    <p class="card-text text-muted small">${image.description || ''}</p>
                                    <div class="d-flex justify-content-between">
                                        <button class="btn btn-sm btn-outline-primary" 
                                                onclick="openImageModal(${image.id})">
                                            <i data-feather="edit" class="me-1"></i>Editar
                                        </button>
                                        <button class="btn btn-sm btn-outline-danger" 
                                                onclick="adminApp.deleteImage(${image.id})">
                                            <i data-feather="trash-2" class="me-1"></i>Excluir
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `).join('');
                    feather.replace();
                } else {
                    imagesList.innerHTML = '<div class="col-12"><div class="alert alert-info">Nenhuma imagem encontrada.</div></div>';
                }
            }
        } catch (error) {
            console.error('Error loading images:', error);
            document.getElementById('images-list').innerHTML = '<div class="col-12"><div class="alert alert-danger">Erro ao carregar imagens.</div></div>';
        }
    }
}

// Global functions for modals
function openKnowledgeModal() {
    // Placeholder for knowledge modal
    alert('Funcionalidade do Banco de Conhecimento em desenvolvimento');
}

// Global agent config function
function saveAgentConfig() {
    if (window.adminApp) {
        window.adminApp.saveAgentConfig();
    }
}

// Global image upload function
function uploadImage() {
    if (window.adminApp) {
        window.adminApp.uploadImage();
    }
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
        const saveMemoryBtn = document.getElementById('saveMemory');
        if (saveMemoryBtn) {
            saveMemoryBtn.addEventListener('click', () => {
                if (window.adminManager) {
                    window.adminManager.saveMemory();
                }
            });
        }
        
        const saveImageBtn = document.getElementById('saveImage');
        if (saveImageBtn) {
            saveImageBtn.addEventListener('click', () => {
                if (window.adminManager) {
                    window.adminManager.saveImage();
                }
            });
        }
        
        const deleteMemoryBtn = document.getElementById('deleteMemory');
        if (deleteMemoryBtn) {
            deleteMemoryBtn.addEventListener('click', () => {
                if (window.adminManager && window.adminManager.currentMemory) {
                    window.adminManager.deleteMemoryConfirm(window.adminManager.currentMemory.id);
                }
            });
        }
        
        const deleteImageBtn = document.getElementById('deleteImage');
        if (deleteImageBtn) {
            deleteImageBtn.addEventListener('click', () => {
                if (window.adminManager && window.adminManager.currentImage) {
                    window.adminManager.deleteImageConfirm(window.adminManager.currentImage.id);
                }
            });
        }
    }, 100);
});

// AdminApp class for tab functionality
class AdminApp {
    constructor() {
        // Initialize admin functionality
        setTimeout(() => {
            this.loadAgentConfig(); 
            this.loadImages();
            this.loadMemories();
        }, 500);
    }

    // Add saveActivity method to AdminApp as well for compatibility
    async saveActivity() {
        if (window.adminManager) {
            return window.adminManager.saveActivity();
        }
    }

    // Agent configuration methods
    async loadAgentConfig() {
        try {
            const response = await fetch('/config/api/config');
            if (response.ok) {
                const config = await response.json();
                const elements = {
                    agentName: document.getElementById('agentName'),
                    agentModel: document.getElementById('agentModel'),
                    agentDescription: document.getElementById('agentDescription'),
                    agentInstructions: document.getElementById('agentInstructions'),
                    agentTemperature: document.getElementById('agentTemperature'),
                    agentMaxTokens: document.getElementById('agentMaxTokens'),
                    toolRoutines: document.getElementById('toolRoutines'),
                    toolMemories: document.getElementById('toolMemories'),
                    toolMedia: document.getElementById('toolMedia')
                };
                
                if (elements.agentName) {
                    elements.agentName.value = config.name || 'Anna';
                    elements.agentModel.value = config.model || 'gemini-2.0-flash';
                    elements.agentDescription.value = config.description || '';
                    elements.agentInstructions.value = config.instructions || '';
                    elements.agentTemperature.value = config.temperature || 0.7;
                    elements.agentMaxTokens.value = config.max_tokens || 1000;
                    
                    // Set tool checkboxes
                    const tools = config.tools || [];
                    elements.toolRoutines.checked = tools.includes('get_anna_routines');
                    elements.toolMemories.checked = tools.includes('search_memories');
                    elements.toolMedia.checked = tools.includes('get_anna_routine_media');
                }
            }
        } catch (error) {
            console.error('Error loading agent config:', error);
        }
    }

    async saveAgentConfig() {
        try {
            const tools = [];
            const toolRoutines = document.getElementById('toolRoutines');
            const toolMemories = document.getElementById('toolMemories');
            const toolMedia = document.getElementById('toolMedia');
            
            if (toolRoutines && toolRoutines.checked) tools.push('get_anna_routines');
            if (toolMemories && toolMemories.checked) tools.push('search_memories');
            if (toolMedia && toolMedia.checked) tools.push('get_anna_routine_media');
            tools.push('get_recent_conversations', 'search_content', 'save_conversation_memory');

            const agentName = document.getElementById('agentName');
            const agentModel = document.getElementById('agentModel');
            const agentDescription = document.getElementById('agentDescription');
            const agentInstructions = document.getElementById('agentInstructions');
            const agentTemperature = document.getElementById('agentTemperature');
            const agentMaxTokens = document.getElementById('agentMaxTokens');

            if (!agentName || !agentModel) {
                alert('Elementos de configuração não encontrados na página');
                return;
            }

            const config = {
                name: agentName.value || 'Anna',
                model: agentModel.value || 'gemini-2.0-flash',
                description: agentDescription ? agentDescription.value : '',
                instructions: agentInstructions ? agentInstructions.value : '',
                temperature: agentTemperature ? parseFloat(agentTemperature.value) : 0.7,
                max_tokens: agentMaxTokens ? parseInt(agentMaxTokens.value) : 1000,
                tools: tools
            };

            console.log('Salvando configuração:', config);

            const response = await fetch('/config/api/config', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(config)
            });

            if (response.ok) {
                const result = await response.json();
                alert('Configuração salva com sucesso!');
            } else {
                const error = await response.text();
                console.error('Erro do servidor:', error);
                throw new Error('Erro ao salvar configuração');
            }
        } catch (error) {
            console.error('Erro ao salvar configuração:', error);
            alert('Erro ao salvar configuração: ' + error.message);
        }
    }

    // Image upload functionality
    async uploadImage() {
        const fileInput = document.getElementById('imageUpload');
        const file = fileInput.files[0];
        
        if (!file) return;

        try {
            const formData = new FormData();
            formData.append('file', file);

            const response = await fetch('/admin/api/upload-image', {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                const result = await response.json();
                alert('Imagem enviada com sucesso!');
                this.loadImages();
                fileInput.value = '';
            } else {
                throw new Error('Erro no upload da imagem');
            }
        } catch (error) {
            alert('Erro ao enviar imagem: ' + error.message);
        }
    }

    async loadImages() {
        try {
            const response = await fetch('/admin/api/images');
            if (response.ok) {
                const data = await response.json();
                const imagesList = document.getElementById('images-list');
                
                if (imagesList && data.success && data.images.length > 0) {
                    imagesList.innerHTML = data.images.map(image => `
                        <div class="image-card">
                            <img src="${image.image_url}" alt="${image.name}" 
                                 onerror="this.src='https://via.placeholder.com/400x300/333/fff?text=Erro'">
                            <div class="image-card-body">
                                <div class="image-card-title">${image.name}</div>
                                <div class="image-card-text">${image.description || ''}</div>
                                <div class="image-card-actions">
                                    <button class="btn-outline-modern btn-sm-modern" 
                                            onclick="openImageModal(${image.id})">
                                        <i data-lucide="edit" width="12" height="12"></i>Editar
                                    </button>
                                    <button class="btn-danger-modern btn-sm-modern" 
                                            onclick="adminApp.deleteImage(${image.id})">
                                        <i data-lucide="trash-2" width="12" height="12"></i>Excluir
                                    </button>
                                </div>
                            </div>
                        </div>
                    `).join('');
                    lucide.createIcons();
                } else if (imagesList) {
                    imagesList.innerHTML = '<div style="grid-column: 1 / -1;"><div class="alert-modern">Nenhuma imagem encontrada. Use o botão "Nova Imagem" para adicionar imagens.</div></div>';
                }
            }
        } catch (error) {
            console.error('Error loading images:', error);
            const imagesList = document.getElementById('images-list');
            if (imagesList) {
                imagesList.innerHTML = '<div style="grid-column: 1 / -1;"><div class="alert-modern" style="background: rgba(220, 53, 69, 0.1); border-color: rgba(220, 53, 69, 0.3);">Erro ao carregar imagens.</div></div>';
            }
        }
    }

    async loadMemories() {
        try {
            const response = await fetch('/admin/api/memories');
            if (response.ok) {
                const data = await response.json();
                const memoriesList = document.getElementById('memories-list');
                
                if (memoriesList && data.success && data.memories.length > 0) {
                    memoriesList.innerHTML = data.memories.map(memory => `
                        <div class="memory-card">
                            <div class="memory-card-title">${memory.name}</div>
                            <div class="memory-card-text">${memory.description || ''}</div>
                            <div class="memory-card-text" style="font-size: 12px; font-style: italic;">
                                Quando usar: ${memory.when_to_use || 'Não especificado'}
                            </div>
                            <div class="memory-card-actions">
                                <button class="btn-outline-modern btn-sm-modern" 
                                        onclick="openMemoryModal(${memory.id})">
                                    <i data-lucide="edit" width="12" height="12"></i>Editar
                                </button>
                                <button class="btn-danger-modern btn-sm-modern" 
                                        onclick="adminApp.deleteMemory(${memory.id})">
                                    <i data-lucide="trash-2" width="12" height="12"></i>Excluir
                                </button>
                            </div>
                        </div>
                    `).join('');
                    lucide.createIcons();
                } else if (memoriesList) {
                    memoriesList.innerHTML = '<div class="alert-modern">Nenhuma memória encontrada. Use o botão "Nova Memória" para adicionar memórias.</div>';
                }
            }
        } catch (error) {
            console.error('Error loading memories:', error);
            const memoriesList = document.getElementById('memories-list');
            if (memoriesList) {
                memoriesList.innerHTML = '<div class="alert-modern" style="background: rgba(220, 53, 69, 0.1); border-color: rgba(220, 53, 69, 0.3);">Erro ao carregar memórias.</div>';
            }
        }
    }

    async loadActivities() {
        try {
            const response = await fetch('/admin/api/activities');
            if (response.ok) {
                const data = await response.json();
                this.renderCalendar(data.activities || []);
                this.loadTodayActivities(data.activities || []);
            }
        } catch (error) {
            console.error('Error loading activities:', error);
        }
    }

    // Alias for compatibility
    loadCalendar() {
        return this.loadActivities();
    }

    renderCalendar(activities) {
        const calendarEl = document.getElementById('calendar');
        if (!calendarEl) return;

        // Initialize calendar if not already done
        if (!this.calendar) {
            this.calendar = new FullCalendar.Calendar(calendarEl, {
                height: 'auto',
                aspectRatio: 1.35,
                initialView: 'dayGridMonth',
                headerToolbar: {
                    left: 'prev,next today',
                    center: 'title',
                    right: 'dayGridMonth,timeGridWeek,timeGridDay'
                },
                locale: 'pt-br',
                selectable: true,
                selectMirror: true,
                dayMaxEvents: true,
                weekends: true,
                eventClick: (info) => {
                    this.openActivityModal(info.event.id);
                }
            });
            this.calendar.render();
        } else {
            // Update existing calendar
            this.calendar.removeAllEvents();
            this.calendar.addEventSource(activities);
        }
        
        // Refresh calendar with activities
        this.calendar.removeAllEvents();
        this.calendar.addEventSource(activities);
    }

    loadTodayActivities(activities) {
        const today = new Date().toISOString().split('T')[0];
        const todayActivities = activities.filter(activity => activity.date === today);
        
        const todayContainer = document.getElementById('todayActivities');
        if (todayContainer) {
            if (todayActivities.length > 0) {
                todayContainer.innerHTML = todayActivities.map(activity => `
                    <div class="today-activity">
                        <div class="today-activity-title">${activity.name}</div>
                        <div class="today-activity-time">${activity.time_start || 'Horário livre'}</div>
                    </div>
                `).join('');
            } else {
                todayContainer.innerHTML = '<div style="color: var(--text-secondary); font-size: 14px;">Nenhuma atividade para hoje</div>';
            }
        }
    }

    async saveMemory() {
        try {
            const memoryData = {
                name: document.getElementById('memoryName').value,
                description: document.getElementById('memoryDescription').value,
                when_to_use: document.getElementById('memoryWhenToUse').value,
                content: document.getElementById('memoryContent').value,
                keywords: document.getElementById('memoryKeywords').value.split(',').map(k => k.trim()),
                is_active: true
            };

            const memoryId = document.getElementById('memoryId').value;
            const url = memoryId ? `/admin/api/memories/${memoryId}` : '/admin/api/memories';
            const method = memoryId ? 'PUT' : 'POST';

            const response = await fetch(url, {
                method: method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(memoryData)
            });

            if (response.ok) {
                alert('Memória salva com sucesso!');
                bootstrap.Modal.getInstance(document.getElementById('memoryModal')).hide();
                this.loadMemories();
            } else {
                throw new Error('Erro ao salvar memória');
            }
        } catch (error) {
            alert('Erro ao salvar memória: ' + error.message);
        }
    }

    async saveImage() {
        try {
            if (!document.getElementById('imageName').value) {
                alert('Nome da imagem é obrigatório');
                return;
            }

            const imageUrl = document.getElementById('imageUrl').value;
            const fileInput = document.getElementById('imageUpload');
            
            if (!imageUrl && !fileInput.files[0]) {
                alert('URL da imagem ou arquivo é obrigatório');
                return;
            }

            let finalImageUrl = imageUrl;
            
            // If file upload, handle file first
            if (fileInput.files[0] && !imageUrl) {
                const formData = new FormData();
                formData.append('file', fileInput.files[0]);

                const uploadResponse = await fetch('/admin/api/upload-image', {
                    method: 'POST',
                    body: formData
                });

                if (uploadResponse.ok) {
                    const uploadResult = await uploadResponse.json();
                    finalImageUrl = uploadResult.url;
                } else {
                    throw new Error('Erro ao fazer upload do arquivo');
                }
            }

            const imageData = {
                name: document.getElementById('imageName').value,
                description: document.getElementById('imageDescription').value,
                when_to_use: document.getElementById('imageWhenToUse').value,
                image_url: finalImageUrl,
                keywords: document.getElementById('imageKeywords').value.split(',').map(k => k.trim()),
                is_active: true
            };

            const imageId = document.getElementById('imageId').value;
            const url = imageId ? `/admin/api/images/${imageId}` : '/admin/api/images';
            const method = imageId ? 'PUT' : 'POST';

            const response = await fetch(url, {
                method: method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(imageData)
            });

            if (response.ok) {
                alert('Imagem salva com sucesso!');
                bootstrap.Modal.getInstance(document.getElementById('imageModal')).hide();
                this.loadImages();
            } else {
                throw new Error('Erro ao salvar imagem');
            }
        } catch (error) {
            alert('Erro ao salvar imagem: ' + error.message);
        }
    }

    async deleteImage(imageId) {
        if (confirm('Tem certeza que deseja excluir esta imagem?')) {
            try {
                const response = await fetch(`/admin/api/images/${imageId}`, {
                    method: 'DELETE'
                });

                if (response.ok) {
                    alert('Imagem excluída com sucesso!');
                    this.loadImages();
                } else {
                    throw new Error('Erro ao excluir imagem');
                }
            } catch (error) {
                alert('Erro ao excluir imagem: ' + error.message);
            }
        }
    }

    async deleteMemory(memoryId) {
        if (confirm('Tem certeza que deseja excluir esta memória?')) {
            try {
                const response = await fetch(`/admin/api/memories/${memoryId}`, {
                    method: 'DELETE'
                });

                if (response.ok) {
                    alert('Memória excluída com sucesso!');
                    this.loadMemories();
                } else {
                    throw new Error('Erro ao excluir memória');
                }
            } catch (error) {
                alert('Erro ao excluir memória: ' + error.message);
            }
        }
    }
}
