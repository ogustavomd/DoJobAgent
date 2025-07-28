class AdminManager {
    constructor() {
        this.calendar = null;
        this.currentActivity = null;
        this.mediaFiles = [];
        this.existingMedia = [];
        this.currentMemory = null;
        this.currentImage = null;
        this.currentActivityView = 'calendario';
        this.filterOptions = { categories: [], statuses: [] };
        this.currentFilters = {};
        
        this.initializeCalendar();
        this.initializeEventListeners();
        this.loadTodayActivities();
        setTimeout(() => this.initializeTabHandlers(), 100);
        this.initializeActivityTabHandlers();
        this.loadFilterOptions();
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
            <div class="today-activity" onclick="adminManager.openActivityModal('${activity.id}')" style="cursor: pointer;">
                <div class="today-activity-title" style="font-size: 16px; font-weight: 600; margin-bottom: 6px;">
                    ${activity.activity}
                </div>
                <div class="today-activity-time" style="font-size: 14px; color: var(--text-secondary); margin-bottom: 8px;">
                    ${this.formatTimeForDisplay(activity.time_start)} - ${this.formatTimeForDisplay(activity.time_end)}
                </div>
                <div style="display: flex; gap: 6px; align-items: center; flex-wrap: wrap;">
                    <span class="badge bg-${this.getCategoryColor(activity.category)}" style="font-size: 11px;">${activity.category}</span>
                    <span class="badge bg-${this.getStatusColor(activity.status)}" style="font-size: 11px;">${activity.status}</span>
                    ${activity.has_images ? '<i data-feather="image" class="text-success" style="width: 14px; height: 14px;"></i>' : ''}
                    ${activity.has_videos ? '<i data-feather="video" class="text-info" style="width: 14px; height: 14px;"></i>' : ''}
                </div>
            </div>
        `).join('');
        
        feather.replace();
    }

    formatTimeForDisplay(timeString) {
        if (!timeString) return '';
        try {
            const [hours, minutes] = timeString.split(':');
            const hour = parseInt(hours);
            const min = parseInt(minutes);
            return `${hour.toString().padStart(2, '0')}h${min.toString().padStart(2, '0')}`;
        } catch (e) {
            return timeString;
        }
    }

    getCategoryColor(category) {
        const colors = {
            'fitness': 'success',
            'trabalho': 'primary',
            'reuniao': 'warning',
            'social': 'info',
            'pessoal': 'danger',
            'conteudo': 'purple'
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
                // Show message if no images found
                const container = document.getElementById('images-list');
                if (container) {
                    container.innerHTML = '<p class="text-muted">Nenhuma imagem encontrada. Adicione imagens através das atividades.</p>';
                }
            }
        } catch (error) {
            console.error('Error loading images:', error);
            const container = document.getElementById('images-list');
            if (container) {
                container.innerHTML = '<p class="text-danger">Erro ao carregar imagens.</p>';
            }
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

    // AI Suggestions functionality
    async loadRoutineAnalysis() {
        try {
            const response = await fetch('/admin/api/ai/routine-analysis');
            const data = await response.json();
            
            if (data.error) {
                document.getElementById('routine-analysis').innerHTML = `
                    <div style="color: #dc3545; font-size: 14px;">Erro: ${data.error}</div>
                `;
                return;
            }
            
            const analysisHtml = `
                <div style="display: grid; gap: 16px;">
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                        <div style="background: var(--bg-primary); padding: 12px; border-radius: 8px;">
                            <div style="font-size: 24px; font-weight: 600; color: var(--accent-purple);">${data.total_activities}</div>
                            <div style="font-size: 12px; color: var(--text-secondary);">Total de Atividades</div>
                        </div>
                        <div style="background: var(--bg-primary); padding: 12px; border-radius: 8px;">
                            <div style="font-size: 24px; font-weight: 600; color: var(--accent-purple);">${data.categories_covered}</div>
                            <div style="font-size: 12px; color: var(--text-secondary);">Categorias Ativas</div>
                        </div>
                    </div>
                    
                    ${data.gaps_identified.length > 0 ? `
                        <div>
                            <h6 style="color: var(--text-primary); margin-bottom: 8px;">Oportunidades de Melhoria:</h6>
                            ${data.gaps_identified.map(gap => `
                                <div style="background: rgba(255, 193, 7, 0.1); color: #ffc107; padding: 8px; border-radius: 6px; font-size: 12px; margin-bottom: 4px;">
                                    • ${gap}
                                </div>
                            `).join('')}
                        </div>
                    ` : ''}
                    
                    ${data.optimization_opportunities.length > 0 ? `
                        <div>
                            <h6 style="color: var(--text-primary); margin-bottom: 8px;">Otimizações Sugeridas:</h6>
                            ${data.optimization_opportunities.map(opp => `
                                <div style="background: rgba(40, 167, 69, 0.1); color: #28a745; padding: 8px; border-radius: 6px; font-size: 12px; margin-bottom: 4px;">
                                    • ${opp}
                                </div>
                            `).join('')}
                        </div>
                    ` : ''}
                    
                    <button class="btn-outline-modern" onclick="adminManager.loadRoutineAnalysis()" style="margin-top: 8px;">
                        <i data-lucide="refresh-cw" width="14" height="14"></i>
                        Atualizar Análise
                    </button>
                </div>
            `;
            
            document.getElementById('routine-analysis').innerHTML = analysisHtml;
            lucide.createIcons();
        } catch (error) {
            console.error('Error loading routine analysis:', error);
            document.getElementById('routine-analysis').innerHTML = `
                <div style="color: #dc3545; font-size: 14px;">Erro ao carregar análise: ${error.message}</div>
            `;
        }
    }

    async loadAIMetrics() {
        try {
            const response = await fetch('/admin/api/ai/suggestion-metrics');
            const data = await response.json();
            
            if (data.error) {
                document.getElementById('ai-metrics').innerHTML = `
                    <div style="color: #dc3545; font-size: 14px;">Erro: ${data.error}</div>
                `;
                return;
            }
            
            const metricsHtml = `
                <div style="display: grid; gap: 12px;">
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
                        <div style="background: var(--bg-primary); padding: 12px; border-radius: 8px;">
                            <div style="font-size: 20px; font-weight: 600; color: var(--accent-purple);">${data.routine_balance_score || 0}</div>
                            <div style="font-size: 11px; color: var(--text-secondary);">Score de Equilíbrio</div>
                        </div>
                        <div style="background: var(--bg-primary); padding: 12px; border-radius: 8px;">
                            <div style="font-size: 20px; font-weight: 600; color: var(--accent-purple);">${data.optimization_potential || 0}</div>
                            <div style="font-size: 11px; color: var(--text-secondary);">Potencial de Otimização</div>
                        </div>
                    </div>
                    
                    ${data.most_common_category ? `
                        <div style="background: var(--bg-primary); padding: 12px; border-radius: 8px;">
                            <div style="font-size: 14px; color: var(--text-primary);">Categoria Dominante:</div>
                            <div style="font-size: 12px; color: var(--accent-purple); text-transform: capitalize;">${data.most_common_category[0]} (${data.most_common_category[1]} atividades)</div>
                        </div>
                    ` : ''}
                    
                    <button class="btn-outline-modern" onclick="adminManager.loadAIMetrics()" style="margin-top: 8px;">
                        <i data-lucide="bar-chart-3" width="14" height="14"></i>
                        Atualizar Métricas
                    </button>
                </div>
            `;
            
            document.getElementById('ai-metrics').innerHTML = metricsHtml;
            lucide.createIcons();
        } catch (error) {
            console.error('Error loading AI metrics:', error);
            document.getElementById('ai-metrics').innerHTML = `
                <div style="color: #dc3545; font-size: 14px;">Erro ao carregar métricas: ${error.message}</div>
            `;
        }
    }

    async generateWeeklySuggestions() {
        const startDate = document.getElementById('suggestion-start-date').value;
        const fitnessGoals = document.getElementById('fitness-goals').value;
        const socialPriority = document.getElementById('social-priority').value;
        
        if (!startDate) {
            alert('Por favor, selecione uma data de início');
            return;
        }
        
        try {
            // Show loading state
            document.getElementById('weekly-suggestions').style.display = 'block';
            document.getElementById('weekly-suggestions').innerHTML = `
                <div style="text-align: center; padding: 20px; color: var(--text-secondary);">
                    <i data-lucide="loader-2" width="24" height="24" style="animation: spin 1s linear infinite;"></i>
                    <div style="margin-top: 8px;">Gerando sugestões inteligentes...</div>
                </div>
            `;
            lucide.createIcons();
            
            const params = new URLSearchParams({
                start_date: startDate,
                fitness_goals: fitnessGoals,
                social_priority: socialPriority,
                preferred_times: 'morning,afternoon'
            });
            
            const response = await fetch(`/admin/api/ai/suggest-weekly?${params}`);
            const data = await response.json();
            
            if (data.error) {
                document.getElementById('weekly-suggestions').innerHTML = `
                    <div style="color: #dc3545; font-size: 14px;">Erro: ${data.error}</div>
                `;
                return;
            }
            
            this.renderWeeklySuggestions(data.suggestions);
        } catch (error) {
            console.error('Error generating suggestions:', error);
            document.getElementById('weekly-suggestions').innerHTML = `
                <div style="color: #dc3545; font-size: 14px;">Erro ao gerar sugestões: ${error.message}</div>
            `;
        }
    }

    renderWeeklySuggestions(suggestions) {
        if (!suggestions || suggestions.length === 0) {
            document.getElementById('weekly-suggestions').innerHTML = `
                <div style="text-align: center; padding: 20px; color: var(--text-secondary);">
                    Nenhuma sugestão gerada
                </div>
            `;
            return;
        }
        
        // Group suggestions by date
        const groupedSuggestions = suggestions.reduce((acc, suggestion) => {
            const date = suggestion.date;
            if (!acc[date]) acc[date] = [];
            acc[date].push(suggestion);
            return acc;
        }, {});
        
        const suggestionsHtml = `
            <div style="margin-bottom: 16px;">
                <h6 style="color: var(--text-primary); margin-bottom: 12px;">
                    ${suggestions.length} sugestões geradas para a semana
                </h6>
            </div>
            
            <div style="display: grid; gap: 16px;">
                ${Object.entries(groupedSuggestions).map(([date, daySuggestions]) => `
                    <div style="background: var(--bg-primary); border-radius: 8px; padding: 16px;">
                        <h6 style="color: var(--accent-purple); margin-bottom: 12px;">
                            ${new Date(date).toLocaleDateString('pt-BR', { weekday: 'long', day: '2-digit', month: '2-digit' })}
                        </h6>
                        
                        <div style="display: grid; gap: 12px;">
                            ${daySuggestions.map(suggestion => `
                                <div style="background: var(--bg-secondary); border-radius: 6px; padding: 12px; border: 1px solid var(--border-color);">
                                    <div style="display: flex; justify-content: between; align-items: start; margin-bottom: 8px;">
                                        <div style="flex: 1;">
                                            <div style="font-weight: 500; color: var(--text-primary); margin-bottom: 4px;">
                                                ${suggestion.activity}
                                            </div>
                                            <div style="font-size: 12px; color: var(--text-secondary); margin-bottom: 4px;">
                                                ${suggestion.time_start} - ${suggestion.time_end} • ${suggestion.location}
                                            </div>
                                            <div style="font-size: 11px; color: var(--text-secondary);">
                                                ${suggestion.description}
                                            </div>
                                        </div>
                                        <div style="display: flex; gap: 8px; margin-left: 12px;">
                                            <span style="background: var(--accent-purple); color: white; padding: 2px 8px; border-radius: 4px; font-size: 10px; text-transform: uppercase;">
                                                ${suggestion.category}
                                            </span>
                                            <span style="background: rgba(40, 167, 69, 0.2); color: #28a745; padding: 2px 8px; border-radius: 4px; font-size: 10px;">
                                                ${Math.round(suggestion.confidence_score * 100)}% confiança
                                            </span>
                                        </div>
                                    </div>
                                    
                                    <div style="display: flex; justify-content: between; align-items: center;">
                                        <div style="font-size: 11px; color: var(--text-secondary); font-style: italic;">
                                            ${suggestion.reasoning}
                                        </div>
                                        <button class="btn-outline-modern" onclick="adminManager.createSuggestedActivity(${JSON.stringify(suggestion).replace(/"/g, '&quot;')})" 
                                                style="padding: 4px 8px; font-size: 11px; margin-left: 8px;">
                                            <i data-lucide="plus" width="12" height="12"></i>
                                            Criar
                                        </button>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
        
        document.getElementById('weekly-suggestions').innerHTML = suggestionsHtml;
        lucide.createIcons();
    }

    async createSuggestedActivity(suggestion) {
        try {
            const response = await fetch('/admin/api/ai/create-suggested-activity', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(suggestion)
            });
            
            const result = await response.json();
            
            if (result.success) {
                alert('Atividade criada com sucesso!');
                // Refresh calendar if we're on activities tab
                if (this.calendar) {
                    this.calendar.refetchEvents();
                }
            } else {
                alert('Erro ao criar atividade: ' + result.error);
            }
        } catch (error) {
            alert('Erro ao criar atividade: ' + error.message);
        }
    }

    clearSuggestions() {
        document.getElementById('weekly-suggestions').style.display = 'none';
        document.getElementById('weekly-suggestions').innerHTML = '';
    }

    async optimizeActivity() {
        const activityId = document.getElementById('activity-id-input').value.trim();
        
        if (!activityId) {
            alert('Por favor, insira o ID da atividade');
            return;
        }
        
        try {
            const response = await fetch(`/admin/api/ai/optimize-routine/${activityId}`);
            const data = await response.json();
            
            if (data.error) {
                document.getElementById('activity-optimization').innerHTML = `
                    <div style="color: #dc3545; font-size: 14px; padding: 12px; background: rgba(220, 53, 69, 0.1); border-radius: 6px;">
                        ${data.error}
                    </div>
                `;
                document.getElementById('activity-optimization').style.display = 'block';
                return;
            }
            
            const optimizationHtml = `
                <div style="background: var(--bg-primary); border-radius: 8px; padding: 16px;">
                    <h6 style="color: var(--text-primary); margin-bottom: 12px;">
                        Otimizações para Atividade ${activityId}
                    </h6>
                    
                    <div style="margin-bottom: 12px;">
                        <span style="background: var(--accent-purple); color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px;">
                            Score Geral: ${Math.round(data.overall_score * 100)}%
                        </span>
                    </div>
                    
                    ${data.optimizations.length > 0 ? `
                        <div style="display: grid; gap: 8px;">
                            ${data.optimizations.map(opt => `
                                <div style="background: var(--bg-secondary); padding: 12px; border-radius: 6px; border: 1px solid var(--border-color);">
                                    <div style="display: flex; justify-content: between; align-items: center; margin-bottom: 4px;">
                                        <span style="font-weight: 500; color: var(--text-primary); text-transform: capitalize;">
                                            ${opt.type}
                                        </span>
                                        <span style="background: rgba(40, 167, 69, 0.2); color: #28a745; padding: 2px 6px; border-radius: 3px; font-size: 10px;">
                                            ${Math.round(opt.confidence * 100)}% confiança
                                        </span>
                                    </div>
                                    <div style="font-size: 12px; color: var(--text-secondary);">
                                        ${opt.suggestion}
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    ` : `
                        <div style="text-align: center; padding: 20px; color: var(--text-secondary);">
                            <i data-lucide="check-circle" width="24" height="24" style="color: #28a745; margin-bottom: 8px;"></i>
                            <div>Esta atividade já está bem otimizada!</div>
                        </div>
                    `}
                </div>
            `;
            
            document.getElementById('activity-optimization').innerHTML = optimizationHtml;
            document.getElementById('activity-optimization').style.display = 'block';
            lucide.createIcons();
        } catch (error) {
            console.error('Error optimizing activity:', error);
            document.getElementById('activity-optimization').innerHTML = `
                <div style="color: #dc3545; font-size: 14px; padding: 12px; background: rgba(220, 53, 69, 0.1); border-radius: 6px;">
                    Erro ao otimizar atividade: ${error.message}
                </div>
            `;
            document.getElementById('activity-optimization').style.display = 'block';
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

// Global functions for AI suggestions
function loadRoutineAnalysis() {
    if (window.adminManager) {
        window.adminManager.loadRoutineAnalysis();
    }
}

function loadAIMetrics() {
    if (window.adminManager) {
        window.adminManager.loadAIMetrics();
    }
}

function generateWeeklySuggestions() {
    if (window.adminManager) {
        window.adminManager.generateWeeklySuggestions();
    }
}

function clearSuggestions() {
    if (window.adminManager) {
        window.adminManager.clearSuggestions();
    }
}

function optimizeActivity() {
    if (window.adminManager) {
        window.adminManager.optimizeActivity();
    }
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

    // Activity sub-tab handling
    initializeActivityTabHandlers() {
        const activityTabBtns = document.querySelectorAll('.activity-tab-btn');
        activityTabBtns.forEach(btn => {
            btn.addEventListener('click', (e) => {
                const tabName = e.target.closest('button').getAttribute('data-activity-tab');
                this.switchActivityTab(tabName);
            });
        });

        // Initialize period filter handler
        const periodFilter = document.getElementById('periodFilter');
        if (periodFilter) {
            periodFilter.addEventListener('change', (e) => {
                const customRange = document.getElementById('customDateRange');
                if (e.target.value === 'custom') {
                    customRange.style.display = 'grid';
                } else {
                    customRange.style.display = 'none';
                }
            });
        }
    }

    switchActivityTab(tabName) {
        // Update tab buttons
        document.querySelectorAll('.activity-tab-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-activity-tab="${tabName}"]`).classList.add('active');

        // Update panels
        document.querySelectorAll('.activity-sub-panel').forEach(panel => {
            panel.classList.remove('active');
        });
        document.getElementById(`${tabName}-view`).classList.add('active');

        this.currentActivityView = tabName;

        // Load appropriate content
        if (tabName === 'lista') {
            this.loadActivitiesList();
        } else if (tabName === 'calendario') {
            if (this.calendar) {
                this.calendar.render();
            }
        }
    }

    async loadFilterOptions() {
        try {
            const response = await fetch('/admin/api/activities/filters');
            const data = await response.json();
            
            this.filterOptions = data;

            // Populate category filter
            const categoryFilter = document.getElementById('categoryFilter');
            if (categoryFilter && data.categories) {
                categoryFilter.innerHTML = '<option value="">Todas as categorias</option>' +
                    data.categories.map(cat => `<option value="${cat}">${cat}</option>`).join('');
            }

            // Populate status filter
            const statusFilter = document.getElementById('statusFilter');
            if (statusFilter && data.statuses) {
                statusFilter.innerHTML = '<option value="">Todos os status</option>' +
                    data.statuses.map(status => `<option value="${status}">${status}</option>`).join('');
            }
        } catch (error) {
            console.error('Error loading filter options:', error);
        }
    }

    async loadActivitiesList() {
        try {
            const params = new URLSearchParams(this.currentFilters);
            const response = await fetch(`/admin/api/activities/list?${params}`);
            const data = await response.json();

            if (data.error) {
                document.getElementById('activitiesList').innerHTML = `
                    <div style="color: #dc3545; font-size: 14px; text-align: center; padding: 20px;">
                        Erro: ${data.error}
                    </div>
                `;
                return;
            }

            const activitiesListContainer = document.getElementById('activitiesList');
            
            if (Object.keys(data).length === 0) {
                activitiesListContainer.innerHTML = `
                    <div style="text-align: center; padding: 40px; color: var(--text-secondary);">
                        <i data-lucide="calendar-x" width="48" height="48" style="margin-bottom: 16px;"></i>
                        <div>Nenhuma atividade encontrada</div>
                    </div>
                `;
                lucide.createIcons();
                return;
            }

            let html = '';
            
            // Sort dates in descending order
            const sortedDates = Object.keys(data).sort((a, b) => new Date(b) - new Date(a));
            
            for (const date of sortedDates) {
                const activities = data[date];
                const formattedDate = this.formatDateForDisplay(date);
                
                html += `
                    <div class="activity-date-section">
                        <div class="activity-date-title">
                            <i data-lucide="calendar" width="20" height="20"></i>
                            ${formattedDate}
                        </div>
                        ${activities.map(activity => this.renderActivityItem(activity)).join('')}
                    </div>
                `;
            }

            activitiesListContainer.innerHTML = html;
            lucide.createIcons();

        } catch (error) {
            console.error('Error loading activities list:', error);
            document.getElementById('activitiesList').innerHTML = `
                <div style="color: #dc3545; font-size: 14px; text-align: center; padding: 20px;">
                    Erro ao carregar atividades: ${error.message}
                </div>
            `;
        }
    }

    renderActivityItem(activity) {
        const statusClass = `status-${activity.status || 'upcoming'}`;
        const statusText = this.getStatusText(activity.status);
        
        return `
            <div class="activity-item">
                <div class="activity-item-header">
                    <div>
                        <div class="activity-item-title">${activity.activity}</div>
                        <div class="activity-item-time">
                            ${activity.time_start || '00:00'} - ${activity.time_end || '23:59'}
                        </div>
                    </div>
                    <span class="status-badge ${statusClass}">${statusText}</span>
                </div>
                
                <div class="activity-item-details">
                    <div class="activity-item-detail">
                        <i data-lucide="tag" width="14" height="14"></i>
                        ${activity.category || 'Sem categoria'}
                    </div>
                    ${activity.location ? `
                        <div class="activity-item-detail">
                            <i data-lucide="map-pin" width="14" height="14"></i>
                            ${activity.location}
                        </div>
                    ` : ''}
                    ${activity.has_images ? `
                        <div class="activity-item-detail">
                            <i data-lucide="image" width="14" height="14"></i>
                            Com imagens
                        </div>
                    ` : ''}
                    ${activity.has_videos ? `
                        <div class="activity-item-detail">
                            <i data-lucide="video" width="14" height="14"></i>
                            Com vídeos
                        </div>
                    ` : ''}
                </div>
                
                ${activity.description ? `
                    <div style="margin-bottom: 12px; font-size: 14px; color: var(--text-secondary);">
                        ${activity.description}
                    </div>
                ` : ''}
                
                <div class="activity-item-actions">
                    <button class="btn-outline-modern" onclick="adminManager.openActivityModal('${activity.id}')" style="font-size: 12px; padding: 6px 12px;">
                        <i data-lucide="edit" width="14" height="14"></i>
                        Editar
                    </button>
                    <button class="btn-danger-modern" onclick="adminManager.deleteActivity('${activity.id}')" style="font-size: 12px; padding: 6px 12px;">
                        <i data-lucide="trash-2" width="14" height="14"></i>
                        Excluir
                    </button>
                </div>
            </div>
        `;
    }

    formatDateForDisplay(dateStr) {
        if (dateStr === 'sem-data') return 'Sem data definida';
        
        const date = new Date(dateStr + 'T00:00:00');
        const today = new Date();
        const yesterday = new Date(today);
        yesterday.setDate(yesterday.getDate() - 1);
        const tomorrow = new Date(today);
        tomorrow.setDate(tomorrow.getDate() + 1);

        const isToday = date.toDateString() === today.toDateString();
        const isYesterday = date.toDateString() === yesterday.toDateString();
        const isTomorrow = date.toDateString() === tomorrow.toDateString();

        if (isToday) return 'Hoje';
        if (isYesterday) return 'Ontem';
        if (isTomorrow) return 'Amanhã';

        return date.toLocaleDateString('pt-BR', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    }

    getStatusText(status) {
        const statusMap = {
            'upcoming': 'Próxima',
            'current': 'Atual',
            'completed': 'Concluída'
        };
        return statusMap[status] || 'Próxima';
    }

    applyFilters() {
        const filters = {};
        
        const search = document.getElementById('searchFilter').value.trim();
        if (search) filters.search = search;
        
        const category = document.getElementById('categoryFilter').value;
        if (category) filters.category = category;
        
        const status = document.getElementById('statusFilter').value;
        if (status) filters.status = status;
        
        const period = document.getElementById('periodFilter').value;
        if (period) {
            const today = new Date();
            let dateFrom, dateTo;
            
            if (period === 'today') {
                dateFrom = today.toISOString().split('T')[0];
                dateTo = dateFrom;
            } else if (period === 'week') {
                const startOfWeek = new Date(today);
                startOfWeek.setDate(today.getDate() - today.getDay());
                const endOfWeek = new Date(startOfWeek);
                endOfWeek.setDate(startOfWeek.getDate() + 6);
                dateFrom = startOfWeek.toISOString().split('T')[0];
                dateTo = endOfWeek.toISOString().split('T')[0];
            } else if (period === 'month') {
                dateFrom = new Date(today.getFullYear(), today.getMonth(), 1).toISOString().split('T')[0];
                dateTo = new Date(today.getFullYear(), today.getMonth() + 1, 0).toISOString().split('T')[0];
            } else if (period === 'custom') {
                dateFrom = document.getElementById('dateFromFilter').value;
                dateTo = document.getElementById('dateToFilter').value;
            }
            
            if (dateFrom) filters.date_from = dateFrom;
            if (dateTo) filters.date_to = dateTo;
        }
        
        this.currentFilters = filters;
        this.loadActivitiesList();
    }

    clearFilters() {
        document.getElementById('searchFilter').value = '';
        document.getElementById('categoryFilter').value = '';
        document.getElementById('statusFilter').value = '';
        document.getElementById('periodFilter').value = '';
        document.getElementById('dateFromFilter').value = '';
        document.getElementById('dateToFilter').value = '';
        document.getElementById('customDateRange').style.display = 'none';
        
        this.currentFilters = {};
        this.loadActivitiesList();
    }
}

// Global functions for HTML template
let adminManager;

// Initialize admin manager when document loads
document.addEventListener('DOMContentLoaded', function() {
    adminManager = new AdminManager();
    console.log('Admin systems initialized successfully');
});

// Global functions called by HTML elements
function applyFilters() {
    if (adminManager) {
        adminManager.applyFilters();
    }
}

function clearFilters() {
    if (adminManager) {
        adminManager.clearFilters();
    }
}
