class AdminManager {
    constructor() {
        this.calendar = null;
        this.currentActivity = null;
        this.mediaFiles = [];
        this.existingMedia = [];
        
        this.initializeCalendar();
        this.initializeEventListeners();
        this.loadTodayActivities();
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
}