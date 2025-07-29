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
        setTimeout(() => {
            try {
                this.initializeTabHandlers();
                
                // Check if methods exist before calling
                if (typeof this.initializeActivityTabHandlers === 'function') {
                    this.initializeActivityTabHandlers();
                } else {
                    console.error('initializeActivityTabHandlers method not found, initializing manually');
                    this.manualInitializeActivityTabs();
                }
                
                if (typeof this.loadFilterOptions === 'function') {
                    this.loadFilterOptions();
                }
                
                // Force switch to calendar view first
                if (typeof this.switchActivityTab === 'function') {
                    this.switchActivityTab('calendario');
                }
            } catch (error) {
                console.error('Error during initialization:', error);
            }
        }, 500);
    }

    // Missing method: initializeActivityTabHandlers
    initializeActivityTabHandlers() {
        console.log('Initializing activity tab handlers');
        
        // Initialize activity tab buttons
        document.querySelectorAll('.activity-tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const tabName = e.target.getAttribute('data-activity-tab');
                console.log('Activity tab clicked:', tabName);
                this.switchActivityTab(tabName);
            });
        });

        // Initialize period filter handler
        const periodFilter = document.getElementById('periodFilter');
        if (periodFilter) {
            periodFilter.addEventListener('change', (e) => {
                const customRange = document.getElementById('customDateRange');
                if (customRange) {
                    if (e.target.value === 'custom') {
                        customRange.style.display = 'grid';
                    } else {
                        customRange.style.display = 'none';
                    }
                }
            });
        }
    }

    // Manual initialization for activity tabs
    manualInitializeActivityTabs() {
        console.log('Manually initializing activity tabs');
        
        // Find and initialize tab buttons
        const tabButtons = document.querySelectorAll('[data-activity-tab]');
        if (tabButtons.length > 0) {
            tabButtons.forEach(btn => {
                if (!btn.onclick) { // Avoid duplicate handlers
                    btn.addEventListener('click', (e) => {
                        const tabName = e.target.getAttribute('data-activity-tab');
                        this.switchActivityTab(tabName);
                    });
                }
            });
        }
    }

    // Load filter options from activities data
    loadFilterOptions() {
        console.log('Loading filter options');
        
        // Get current activities to extract filter options
        fetch('/admin/api/activities')
            .then(response => response.json())
            .then(data => {
                const categories = [...new Set(data.map(activity => activity.category))].filter(Boolean);
                const statuses = [...new Set(data.map(activity => activity.status))].filter(Boolean);
                
                this.filterOptions = { categories, statuses };
                this.populateFilterDropdowns();
            })
            .catch(error => {
                console.error('Error loading filter options:', error);
                // Set default options
                this.filterOptions = {
                    categories: ['trabalho', 'fitness', 'pessoal', 'social', 'saude', 'educacao'],
                    statuses: ['upcoming', 'current', 'completed']
                };
                this.populateFilterDropdowns();
            });
    }

    populateFilterDropdowns() {
        // Populate category filter
        const categoryFilter = document.getElementById('categoryFilter');
        if (categoryFilter && this.filterOptions.categories) {
            categoryFilter.innerHTML = '<option value="">Todas as categorias</option>';
            this.filterOptions.categories.forEach(category => {
                const option = document.createElement('option');
                option.value = category;
                option.textContent = this.formatCategoryName(category);
                categoryFilter.appendChild(option);
            });
        }

        // Populate status filter
        const statusFilter = document.getElementById('statusFilter');
        if (statusFilter && this.filterOptions.statuses) {
            statusFilter.innerHTML = '<option value="">Todos os status</option>';
            this.filterOptions.statuses.forEach(status => {
                const option = document.createElement('option');
                option.value = status;
                option.textContent = this.formatStatusName(status);
                statusFilter.appendChild(option);
            });
        }

        // Add event listeners for real-time filtering
        this.setupFilterEventListeners();
    }

    formatCategoryName(category) {
        const names = {
            'trabalho': 'Trabalho',
            'fitness': 'Fitness',
            'pessoal': 'Pessoal',
            'social': 'Social',
            'saude': 'Saúde',
            'educacao': 'Educação'
        };
        return names[category] || category;
    }

    formatStatusName(status) {
        const names = {
            'upcoming': 'Próxima',
            'current': 'Em andamento',
            'completed': 'Concluída'
        };
        return names[status] || status;
    }

    setupFilterEventListeners() {
        // Search filter - real-time filtering
        const searchFilter = document.getElementById('searchFilter');
        if (searchFilter) {
            searchFilter.addEventListener('input', () => {
                clearTimeout(this.searchTimeout);
                this.searchTimeout = setTimeout(() => {
                    this.applyFilters();
                }, 300);
            });
        }

        // Other filters
        ['categoryFilter', 'statusFilter', 'periodFilter', 'dateFromFilter', 'dateToFilter'].forEach(filterId => {
            const filter = document.getElementById(filterId);
            if (filter) {
                filter.addEventListener('change', () => {
                    if (filterId === 'periodFilter') {
                        this.handlePeriodFilterChange();
                    }
                    this.applyFilters();
                });
            }
        });
    }

    handlePeriodFilterChange() {
        const periodFilter = document.getElementById('periodFilter');
        const customRange = document.getElementById('customDateRange');
        
        if (periodFilter && customRange) {
            if (periodFilter.value === 'custom') {
                customRange.style.display = 'grid';
            } else {
                customRange.style.display = 'none';
                // Clear custom date fields
                document.getElementById('dateFromFilter').value = '';
                document.getElementById('dateToFilter').value = '';
            }
        }
    }

    // Missing method: switchActivityTab
    switchActivityTab(tabName) {
        console.log('Switching to tab:', tabName);
        
        // Update tab buttons
        document.querySelectorAll('.activity-tab-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        const activeTab = document.querySelector(`[data-activity-tab="${tabName}"]`);
        if (activeTab) {
            activeTab.classList.add('active');
        }

        // Update panels
        document.querySelectorAll('.activity-sub-panel').forEach(panel => {
            panel.classList.remove('active');
        });
        const activePanel = document.getElementById(`${tabName}-view`);
        if (activePanel) {
            activePanel.classList.add('active');
        }

        // Load content based on the tab
        this.currentActivityView = tabName;
        switch (tabName) {
            case 'calendario':
                if (this.calendar) {
                    setTimeout(() => this.calendar.updateSize(), 100);
                }
                break;
            case 'lista':
                this.loadActivitiesList();
                break;
            case 'hoje':
                this.loadTodayActivities();
                break;
        }
    }

    loadActivitiesList() {
        console.log('Loading activities list');
        
        // Build query parameters from current filters
        let queryParams = new URLSearchParams();
        if (this.currentFilters.category) queryParams.append('category', this.currentFilters.category);
        if (this.currentFilters.status) queryParams.append('status', this.currentFilters.status);
        if (this.currentFilters.dateFrom) queryParams.append('date_from', this.currentFilters.dateFrom);
        if (this.currentFilters.dateTo) queryParams.append('date_to', this.currentFilters.dateTo);
        if (this.currentFilters.search) queryParams.append('search', this.currentFilters.search);
        
        const url = '/admin/api/activities/list' + (queryParams.toString() ? '?' + queryParams.toString() : '');
        
        fetch(url)
            .then(response => response.json())
            .then(data => {
                console.log('Activities list data received:', data);
                this.renderActivitiesList(data);
            })
            .catch(error => {
                console.error('Error loading activities list:', error);
            });
    }

    applyFilters() {
        console.log('Applying filters');
        
        // Get filter values from form
        const categoryFilter = document.getElementById('categoryFilter');
        const statusFilter = document.getElementById('statusFilter');
        const dateFromFilter = document.getElementById('dateFromFilter');
        const dateToFilter = document.getElementById('dateToFilter');
        const searchFilter = document.getElementById('searchFilter');
        
        // Update current filters
        this.currentFilters = {
            category: categoryFilter?.value || '',
            status: statusFilter?.value || '',
            dateFrom: dateFromFilter?.value || '',
            dateTo: dateToFilter?.value || '',
            search: searchFilter?.value || ''
        };
        
        // Reload activities list with filters
        this.loadActivitiesList();
    }

    clearFilters() {
        console.log('Clearing filters');
        
        // Clear current filters
        this.currentFilters = {};
        
        // Clear form values
        const categoryFilter = document.getElementById('categoryFilter');
        const statusFilter = document.getElementById('statusFilter');
        const dateFromFilter = document.getElementById('dateFromFilter');
        const dateToFilter = document.getElementById('dateToFilter');
        const searchFilter = document.getElementById('searchFilter');
        
        if (categoryFilter) categoryFilter.value = '';
        if (statusFilter) statusFilter.value = '';
        if (dateFromFilter) dateFromFilter.value = '';
        if (dateToFilter) dateToFilter.value = '';
        if (searchFilter) searchFilter.value = '';
        
        // Reload activities list without filters
        this.loadActivitiesList();
    }

    renderActivitiesList(activitiesByDate) {
        console.log('Rendering activities list with data:', activitiesByDate);
        const container = document.getElementById('activitiesList');
        if (!container) {
            console.error('activitiesList container not found!');
            return;
        }

        container.innerHTML = '';
        
        // Check if we have data
        if (!activitiesByDate || Object.keys(activitiesByDate).length === 0) {
            container.innerHTML = '<p class="text-muted">Nenhuma atividade encontrada com os filtros selecionados.</p>';
            return;
        }
        
        Object.entries(activitiesByDate).forEach(([date, activities]) => {
            const dateSection = document.createElement('div');
            dateSection.className = 'date-section mb-4';
            
            dateSection.innerHTML = `
                <h5 class="date-header">${this.formatDateForDisplay(date)}</h5>
                <div class="activities-for-date">
                    ${activities.map(activity => this.createActivityCardHTML(activity)).join('')}
                </div>
            `;
            
            container.appendChild(dateSection);
        });
        
        // Initialize activity card interactions
        this.initializeActivityCards();
        
        // Re-initialize Lucide icons for new content
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
        
        console.log('Activities list rendered successfully');
    }

    createActivityCardHTML(activity) {
        const priorityColor = this.getPriorityColor(activity.category);
        const statusBadge = this.getStatusBadge(activity.status);
        
        return `
            <div class="activity-card" data-activity-id="${activity.id}">
                <div class="activity-card-header">
                    <div class="activity-priority-indicator" style="background-color: ${priorityColor}"></div>
                    <div class="activity-card-main">
                        <div class="activity-card-time">
                            <i data-lucide="clock" width="16" height="16"></i>
                            ${activity.time_start.substring(0, 5)}
                        </div>
                        <div class="activity-card-title">${activity.activity}</div>
                        ${activity.location ? `<div class="activity-card-location">${activity.location}</div>` : ''}
                    </div>
                    <div class="activity-card-actions">
                        <div class="activity-dropdown-container">
                            <button class="activity-menu-btn" type="button" onclick="event.stopPropagation(); this.parentElement.classList.toggle('active');">
                                <i data-lucide="more-vertical" width="16" height="16"></i>
                            </button>
                            <div class="activity-dropdown-menu">
                                <button class="activity-dropdown-item" onclick="event.stopPropagation(); window.adminManager.openActivityModal('${activity.id}'); document.querySelector('.activity-dropdown-container.active')?.classList.remove('active');">
                                    <i data-lucide="edit" width="16" height="16"></i> Editar
                                </button>
                                <button class="activity-dropdown-item activity-dropdown-delete" onclick="event.stopPropagation(); window.adminManager.deleteActivity('${activity.id}'); document.querySelector('.activity-dropdown-container.active')?.classList.remove('active');">
                                    <i data-lucide="trash-2" width="16" height="16"></i> Excluir
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
                ${activity.description ? `<div class="activity-card-description">${activity.description}</div>` : ''}
                <div class="activity-card-footer">
                    <span class="activity-category-badge">${activity.category}</span>
                    ${statusBadge}
                    ${activity.has_images ? '<i data-lucide="image" width="14" height="14" class="media-indicator"></i>' : ''}
                    ${activity.has_videos ? '<i data-lucide="video" width="14" height="14" class="media-indicator"></i>' : ''}
                </div>
            </div>
        `;
    }

    getPriorityColor(category) {
        const colors = {
            'trabalho': '#8F5CFF',
            'fitness': '#10B981', 
            'pessoal': '#F59E0B',
            'social': '#EF4444',
            'saude': '#06B6D4',
            'educacao': '#8B5CF6'
        };
        return colors[category] || '#6B7280';
    }

    getStatusBadge(status) {
        const badges = {
            'upcoming': '<span class="status-badge status-upcoming">Próxima</span>',
            'current': '<span class="status-badge status-current">Em andamento</span>',
            'completed': '<span class="status-badge status-completed">Concluída</span>'
        };
        return badges[status] || '<span class="status-badge">' + status + '</span>';
    }

    initializeActivityCards() {
        // Add click handlers to activity cards
        document.querySelectorAll('.activity-card').forEach(card => {
            card.addEventListener('click', (e) => {
                // Don't trigger if clicked on dropdown or its children
                if (!e.target.closest('.activity-dropdown-container') && !e.target.closest('.activity-menu-btn')) {
                    const activityId = card.dataset.activityId;
                    this.openActivityModal(activityId);
                }
            });
        });

        // Close dropdowns when clicking outside
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.activity-dropdown-container')) {
                document.querySelectorAll('.activity-dropdown-container.active').forEach(dropdown => {
                    dropdown.classList.remove('active');
                });
            }
        });
    }

    async deleteActivity(activityId) {
        if (!confirm('Tem certeza que deseja excluir esta atividade? Esta ação não pode ser desfeita.')) {
            return;
        }

        try {
            const response = await fetch(`/admin/api/activities/${activityId}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                this.showAlert('Atividade excluída com sucesso', 'success');
                
                // Reload the activities list to reflect the changes
                this.loadActivitiesList();
                
                // Also reload today's activities if visible
                this.loadTodayActivities();
                
                // Refresh calendar if it's in calendar view
                if (this.currentActivityView === 'calendario' && this.calendar) {
                    this.calendar.refetchEvents();
                }
            } else {
                const error = await response.json();
                this.showAlert(error.error || 'Erro ao excluir atividade', 'danger');
            }
        } catch (error) {
            console.error('Error deleting activity:', error);
            this.showAlert('Erro ao excluir atividade', 'danger');
        }
    }

    showAlert(message, type = 'info') {
        // Create alert element
        const alert = document.createElement('div');
        alert.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        alert.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        // Add to page
        document.body.appendChild(alert);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (alert.parentNode) {
                alert.remove();
            }
        }, 5000);
    }

    formatDateForDisplay(dateString) {
        if (dateString === 'sem-data') return 'Sem Data';
        try {
            const date = new Date(dateString);
            return date.toLocaleDateString('pt-BR');
        } catch (e) {
            return dateString;
        }
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
            
            events: async (info, successCallback, failureCallback) => {
                try {
                    const response = await fetch('/admin/api/activities');
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}`);
                    }
                    const events = await response.json();
                    console.log('Calendar events loaded:', events.length);
                    successCallback(events);
                } catch (error) {
                    console.error('Error loading calendar events:', error);
                    failureCallback(error);
                }
            }
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

    async deleteActivityById(activityId) {
        try {
            const response = await fetch(`/admin/api/activities/${activityId}`, {
                method: 'DELETE'
            });
            
            const result = await response.json();
            
            if (response.ok) {
                this.showAlert('Atividade excluída com sucesso!', 'success');
                if (this.calendar) this.calendar.refetchEvents();
                this.loadTodayActivities();
                this.loadActivitiesList();
            } else {
                this.showAlert('Erro ao excluir atividade: ' + (result.error || 'Erro desconhecido'), 'danger');
            }
        } catch (error) {
            console.error('Error deleting activity:', error);
            this.showAlert('Erro ao excluir atividade: ' + error.message, 'danger');
        }
    }

    async loadTodayActivities() {
        const today = new Date().toISOString().split('T')[0];
        
        try {
            const response = await fetch(`/admin/api/activities/date/${today}`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            const activities = await response.json();
            
            this.renderTodayActivities(activities);
        } catch (error) {
            console.error('Error loading today activities:', error);
            const container = document.getElementById('todayActivities');
            if (container) {
                container.innerHTML = '<p class="text-muted">Erro ao carregar atividades</p>';
            }
        }
    }

    renderTodayActivities(activities) {
        console.log('Rendering today activities:', activities);
        const container = document.getElementById('todayActivities');
        if (!container) {
            console.error('Today activities container not found!');
            return;
        }
        
        if (!activities || activities.length === 0) {
            container.innerHTML = '<p class="text-muted">Nenhuma atividade para hoje</p>';
            return;
        }
        
        container.innerHTML = activities.map(activity => `
            <div class="today-activity" onclick="openActivityModal('${activity.id}')" style="cursor: pointer;">
                <div class="today-activity-title" style="font-size: 16px; font-weight: 600; margin-bottom: 6px;">
                    ${activity.activity || 'Atividade sem nome'}
                </div>
                <div class="today-activity-time" style="font-size: 14px; color: var(--text-secondary); margin-bottom: 8px;">
                    ${this.formatTimeForDisplay(activity.time_start)} - ${this.formatTimeForDisplay(activity.time_end)}
                </div>
                <div style="display: flex; gap: 6px; align-items: center; flex-wrap: wrap;">
                    <span class="badge bg-primary" style="font-size: 11px;">${activity.category || 'Sem categoria'}</span>
                    <span class="badge bg-success" style="font-size: 11px;">${activity.status || 'upcoming'}</span>
                    ${activity.has_images ? '<i data-lucide="image" style="width: 14px; height: 14px;"></i>' : ''}
                    ${activity.has_videos ? '<i data-lucide="video" style="width: 14px; height: 14px;"></i>' : ''}
                </div>
            </div>
        `).join('');
        
        lucide.createIcons();
        console.log('Today activities rendered successfully');
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

    // Error/success message helpers
    showErrorMessage(message) {
        this.showAlert(message, 'danger');
    }

    showSuccessMessage(message) {
        this.showAlert(message, 'success');
    }

    // Error message formatter
    getErrorMessage(error) {
        if (typeof error === 'string') return error;
        if (error.message) return error.message;
        if (error.error) return error.error;
        return 'Erro desconhecido';
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

    loadCalendar() {
        // Switch to calendar view
        this.switchActivityTab('calendario');
    }

    async loadKnowledge() {
        // Knowledge tab implementation - placeholder for now
        const container = document.getElementById('knowledge-list');
        if (container) {
            container.innerHTML = '<p class="text-muted">Funcionalidade em desenvolvimento</p>';
        }
    }
}

// Initialize admin manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.adminManager = new AdminManager();
    window.adminApp = window.adminManager; // Create alias for backward compatibility
    
    // Load current agent configuration
    loadAgentConfig();
    
    // Note: Save agent config button uses onclick handler in HTML
});

// Global functions for HTML onclick handlers
function openActivityModal(activityId = null, selectedDate = null) {
    if (window.adminManager) {
        return window.adminManager.openActivityModal(activityId, selectedDate);
    }
    console.error('AdminManager not initialized');
}

function applyFilters() {
    if (window.adminManager) {
        return window.adminManager.applyFilters();
    }
    console.error('AdminManager not initialized');
}

function clearFilters() {
    if (window.adminManager) {
        return window.adminManager.clearFilters();
    }
    console.error('AdminManager not initialized');
}

function deleteActivityFromList(activityId) {
    if (window.adminManager && confirm('Tem certeza que deseja excluir esta atividade?')) {
        return window.adminManager.deleteActivityById(activityId);
    }
}

// Global function for saving agent configuration
window.saveAgentConfig = async function() {
    try {
        const config = {
            name: document.getElementById('agentName').value || 'Anna',
            model: document.getElementById('agentModel').value || 'gemini-2.0-flash',
            description: document.getElementById('agentDescription').value || '',
            instructions: document.getElementById('agentInstructions').value || '',
            temperature: parseFloat(document.getElementById('agentTemperature').value) || 0.7,
            max_tokens: parseInt(document.getElementById('agentMaxTokens').value) || 1000,
            tools_enabled: {
                routines: document.getElementById('toolRoutines')?.checked ?? true,
                memories: document.getElementById('toolMemories')?.checked ?? true,
                media: document.getElementById('toolMedia')?.checked ?? true
            }
        };

        console.log('Saving agent config:', config);

        const response = await fetch('/config/api/config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(config)
        });

        const result = await response.json();
        
        if (result.success) {
            // Show success message
            showMessage('Configuração salva com sucesso! O agente será reinicializado.', 'success');
            
            // Reload page after 2 seconds to reinitialize agent
            setTimeout(() => {
                window.location.reload();
            }, 2000);
        } else {
            showMessage('Erro ao salvar configuração: ' + (result.error || 'Erro desconhecido'), 'error');
        }
    } catch (error) {
        console.error('Error saving agent config:', error);
        showMessage('Erro ao salvar configuração: ' + error.message, 'error');
    }
};

// Helper function to show messages
function showMessage(message, type = 'info') {
    const alertClass = type === 'success' ? 'alert-success' : 
                      type === 'error' ? 'alert-danger' : 'alert-info';
    
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert ${alertClass}`;
    alertDiv.style.position = 'fixed';
    alertDiv.style.top = '20px';
    alertDiv.style.right = '20px';
    alertDiv.style.zIndex = '9999';
    alertDiv.style.maxWidth = '400px';
    alertDiv.style.padding = '12px 16px';
    alertDiv.style.borderRadius = '8px';
    alertDiv.style.boxShadow = '0 4px 12px rgba(0,0,0,0.1)';
    
    const iconName = type === 'success' ? 'check-circle' : 
                     type === 'error' ? 'alert-circle' : 'info';
    
    alertDiv.innerHTML = `
        <div style="display: flex; align-items: center; gap: 8px;">
            <i data-lucide="${iconName}" width="16" height="16"></i>
            <span>${message}</span>
        </div>
    `;
    
    document.body.appendChild(alertDiv);
    
    // Replace feather icons
    if (typeof feather !== 'undefined') {
        feather.replace();
    }
    
    // Remove after 5 seconds
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

// Function to load current agent configuration
async function loadAgentConfig() {
    try {
        const response = await fetch('/config/api/config');
        if (response.ok) {
            const config = await response.json();
            
            // Populate form fields
            const agentName = document.getElementById('agentName');
            const agentModel = document.getElementById('agentModel');
            const agentDescription = document.getElementById('agentDescription');
            const agentInstructions = document.getElementById('agentInstructions');
            const agentTemperature = document.getElementById('agentTemperature');
            const agentMaxTokens = document.getElementById('agentMaxTokens');
            const toolRoutines = document.getElementById('toolRoutines');
            const toolMemories = document.getElementById('toolMemories');
            const toolMedia = document.getElementById('toolMedia');
            
            if (agentName) agentName.value = config.name || 'Anna';
            if (agentModel) agentModel.value = config.model || 'gemini-2.0-flash';
            if (agentDescription) agentDescription.value = config.description || '';
            if (agentInstructions) agentInstructions.value = config.instructions || '';
            if (agentTemperature) agentTemperature.value = config.temperature || 0.7;
            if (agentMaxTokens) agentMaxTokens.value = config.max_tokens || 1000;
            
            // Handle tools_enabled object
            const toolsEnabled = config.tools_enabled || {};
            if (toolRoutines) toolRoutines.checked = toolsEnabled.routines !== false;
            if (toolMemories) toolMemories.checked = toolsEnabled.memories !== false;
            if (toolMedia) toolMedia.checked = toolsEnabled.media !== false;
            
            console.log('Agent configuration loaded:', config);
        } else {
            console.log('No existing configuration found, using defaults');
        }
    } catch (error) {
        console.error('Error loading agent configuration:', error);
    }
}
