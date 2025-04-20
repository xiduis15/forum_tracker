document.addEventListener('DOMContentLoaded', function() {
    // DOM elements
    const performersTable = document.getElementById('performers-table').querySelector('tbody');
    const threadsTable = document.getElementById('threads-table').querySelector('tbody');
    const statusMessage = document.getElementById('status-message');
    const resultsContainer = document.getElementById('results-container');
    const performersPagination = document.getElementById('performers-pagination');
    const performersPerPage = document.getElementById('performers-per-page');
    
    // Buttons
    const savePerformerBtn = document.getElementById('savePerformerBtn');
    const saveThreadBtn = document.getElementById('saveThreadBtn');
    const checkAllBtn = document.getElementById('checkAllBtn');
    const testScraperBtn = document.getElementById('testScraperBtn');
    const checkPerformerThreadsBtn = document.getElementById('checkPerformerThreadsBtn');
    const addThreadModalBtn = document.getElementById('addThreadModalBtn');
    
    // Modals
    const addPerformerModal = new bootstrap.Modal(document.getElementById('addPerformerModal'));
    const addThreadModal = new bootstrap.Modal(document.getElementById('addThreadModal'));
    const viewThreadsModal = new bootstrap.Modal(document.getElementById('viewThreadsModal'));
    
    // State variables
    let currentPerformerId = null;
    let currentPerformerName = null;
    let allPerformers = [];
    
    // Pagination state
    const paginationState = {
        currentPage: 1,
        itemsPerPage: parseInt(performersPerPage.value) || 10
    };
    
    // Load performers when page loads
    loadPerformers();
    
    // Event Listeners
    
    // Pagination items per page change
    performersPerPage.addEventListener('change', function() {
        paginationState.itemsPerPage = parseInt(this.value) || 10;
        paginationState.currentPage = 1; // Reset to first page
        renderPerformers(allPerformers);
    });
    
    // Add Performer
    savePerformerBtn.addEventListener('click', function() {
        const name = document.getElementById('performerName').value.trim();
        const isActive = document.getElementById('isActive').checked;
        
        if (!name) {
            alert('Name is required');
            return;
        }
        
        addPerformer(name, isActive);
    });
    
    // Add Thread
    saveThreadBtn.addEventListener('click', function() {
        const url = document.getElementById('threadUrl').value.trim();
        const performerId = document.getElementById('threadPerformerId').value;
        
        if (!url) {
            alert('URL is required');
            return;
        }
        
        addThread(performerId, url);
    });
    
    // Check All Threads
    checkAllBtn.addEventListener('click', function() {
        checkAllThreads();
    });
    
    // Test Scraper
    testScraperBtn.addEventListener('click', function() {
        testScraper();
    });
    
    // Check Performer Threads
    checkPerformerThreadsBtn.addEventListener('click', function() {
        checkPerformerThreads(currentPerformerId);
    });
    
    // Add Thread Modal Button
    addThreadModalBtn.addEventListener('click', function() {
        document.getElementById('threadPerformerId').value = currentPerformerId;
        addThreadModal.show();
    });
    
    // Helper Functions
    
    // Load performers from API
    function loadPerformers() {
        setStatus('Loading performers...', 'info');
        
        fetch('/api/performers')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    allPerformers = data.performers;
                    renderPerformers(allPerformers);
                    setStatus('Performers loaded successfully', 'success');
                } else {
                    setStatus('Failed to load performers: ' + data.error, 'danger');
                }
            })
            .catch(error => {
                setStatus('Error loading performers: ' + error.message, 'danger');
            });
    }
    
    // Render performers table
    function renderPerformers(performers) {
        performersTable.innerHTML = '';
        
        if (performers.length === 0) {
            const row = document.createElement('tr');
            row.innerHTML = '<td colspan="5" class="text-center">No performers found</td>';
            performersTable.appendChild(row);
            
            // Clear pagination
            renderPagination(0, 1);
            return;
        }
        
        // Calculate pagination
        const totalPages = Math.ceil(performers.length / paginationState.itemsPerPage);
        if (paginationState.currentPage > totalPages) {
            paginationState.currentPage = totalPages;
        }
        
        // Get current page data
        const startIndex = (paginationState.currentPage - 1) * paginationState.itemsPerPage;
        const endIndex = Math.min(startIndex + paginationState.itemsPerPage, performers.length);
        const currentPageData = performers.slice(startIndex, endIndex);
        
        // Render table rows
        currentPageData.forEach(performer => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${performer.id}</td>
                <td>${performer.name}</td>
                <td>
                    <div class="form-check form-switch">
                        <input class="form-check-input performer-active-toggle" type="checkbox" 
                            data-id="${performer.id}" ${performer.is_active ? 'checked' : ''}>
                    </div>
                </td>
                <td>
                    <button class="btn btn-sm btn-info view-threads-btn" data-id="${performer.id}" data-name="${performer.name}">
                        View Threads (${performer.threads.length})
                    </button>
                </td>
                <td>
                    <button class="btn btn-sm btn-danger delete-performer-btn" data-id="${performer.id}">
                        Delete
                    </button>
                </td>
            `;
            performersTable.appendChild(row);
        });
        
        // Render pagination
        renderPagination(performers.length, paginationState.currentPage);
        
        // Add event listeners to buttons
        document.querySelectorAll('.performer-active-toggle').forEach(toggle => {
            toggle.addEventListener('change', function() {
                const performerId = this.dataset.id;
                const isActive = this.checked;
                updatePerformerStatus(performerId, isActive);
            });
        });
        
        document.querySelectorAll('.view-threads-btn').forEach(button => {
            button.addEventListener('click', function() {
                const performerId = this.dataset.id;
                const performerName = this.dataset.name;
                viewPerformerThreads(performerId, performerName);
            });
        });
        
        document.querySelectorAll('.delete-performer-btn').forEach(button => {
            button.addEventListener('click', function() {
                const performerId = this.dataset.id;
                if (confirm('Are you sure you want to delete this performer? This will also delete all associated threads.')) {
                    deletePerformer(performerId);
                }
            });
        });
    }
    
    // Render pagination
    function renderPagination(totalItems, currentPage) {
        performersPagination.innerHTML = '';
        
        const totalPages = Math.ceil(totalItems / paginationState.itemsPerPage);
        
        if (totalPages <= 1) {
            return;
        }
        
        // Previous button
        const prevLi = document.createElement('li');
        prevLi.className = `page-item ${currentPage === 1 ? 'disabled' : ''}`;
        prevLi.innerHTML = `
            <a class="page-link" href="#" aria-label="Previous" data-page="${currentPage - 1}">
                <span aria-hidden="true">&laquo;</span>
            </a>
        `;
        performersPagination.appendChild(prevLi);
        
        // Page numbers
        let startPage = Math.max(1, currentPage - 2);
        let endPage = Math.min(totalPages, startPage + 4);
        
        // Adjust if we're near the end
        if (endPage - startPage < 4) {
            startPage = Math.max(1, endPage - 4);
        }
        
        for (let i = startPage; i <= endPage; i++) {
            const pageLi = document.createElement('li');
            pageLi.className = `page-item ${i === currentPage ? 'active' : ''}`;
            pageLi.innerHTML = `
                <a class="page-link" href="#" data-page="${i}">${i}</a>
            `;
            performersPagination.appendChild(pageLi);
        }
        
        // Next button
        const nextLi = document.createElement('li');
        nextLi.className = `page-item ${currentPage === totalPages ? 'disabled' : ''}`;
        nextLi.innerHTML = `
            <a class="page-link" href="#" aria-label="Next" data-page="${currentPage + 1}">
                <span aria-hidden="true">&raquo;</span>
            </a>
        `;
        performersPagination.appendChild(nextLi);
        
        // Remove any existing event listeners (important!)
        document.querySelectorAll('#performers-pagination .page-link').forEach(link => {
            const newLink = link.cloneNode(true);
            link.parentNode.replaceChild(newLink, link);
        });
        
        // Add event listeners to pagination links
        document.querySelectorAll('#performers-pagination .page-link').forEach(link => {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                const page = parseInt(this.dataset.page);
                if (page && page > 0 && page <= totalPages) {
                    console.log(`Changing page to ${page}`); // Debug log
                    paginationState.currentPage = page;
                    renderPerformers(allPerformers);
                }
            });
        });
    }
    
    // Add new performer
    function addPerformer(name, isActive) {
        setStatus('Adding performer...', 'info');
        
        fetch('/api/performers', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name: name,
                is_active: isActive
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                setStatus('Performer added successfully', 'success');
                addPerformerModal.hide();
                document.getElementById('performerName').value = '';
                document.getElementById('isActive').checked = true;
                loadPerformers();
            } else {
                setStatus('Failed to add performer: ' + data.error, 'danger');
            }
        })
        .catch(error => {
            setStatus('Error adding performer: ' + error.message, 'danger');
        });
    }
    
    // Update performer active status
    function updatePerformerStatus(performerId, isActive) {
        setStatus('Updating performer...', 'info');
        
        fetch(`/api/performers/${performerId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                is_active: isActive
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                setStatus('Performer updated successfully', 'success');
            } else {
                setStatus('Failed to update performer: ' + data.error, 'danger');
                loadPerformers(); // Reload to reset the toggle
            }
        })
        .catch(error => {
            setStatus('Error updating performer: ' + error.message, 'danger');
            loadPerformers(); // Reload to reset the toggle
        });
    }
    
    // Delete performer
    function deletePerformer(performerId) {
        setStatus('Deleting performer...', 'info');
        
        fetch(`/api/performers/${performerId}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                setStatus('Performer deleted successfully', 'success');
                loadPerformers();
            } else {
                setStatus('Failed to delete performer: ' + data.error, 'danger');
            }
        })
        .catch(error => {
            setStatus('Error deleting performer: ' + error.message, 'danger');
        });
    }
    
    // View performer threads
    function viewPerformerThreads(performerId, performerName) {
        setStatus('Loading threads...', 'info');
        currentPerformerId = performerId;
        currentPerformerName = performerName;
        
        document.getElementById('threadsModalPerformerName').textContent = performerName;
        
        fetch(`/api/performers/${performerId}/threads`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    renderThreads(data.threads);
                    viewThreadsModal.show();
                    setStatus('Threads loaded successfully', 'success');
                } else {
                    setStatus('Failed to load threads: ' + data.error, 'danger');
                }
            })
            .catch(error => {
                setStatus('Error loading threads: ' + error.message, 'danger');
            });
    }
    
    // Render threads in modal
    function renderThreads(threads) {
        threadsTable.innerHTML = '';
        
        if (threads.length === 0) {
            const row = document.createElement('tr');
            row.innerHTML = '<td colspan="5" class="text-center">No threads found</td>';
            threadsTable.appendChild(row);
            return;
        }
        
        threads.forEach(thread => {
            const lastCheck = thread.last_check ? new Date(thread.last_check).toLocaleString() : 'Never';
            
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${thread.id}</td>
                <td>
                    <a href="${thread.url}" target="_blank" class="thread-url" title="${thread.url}">
                        ${thread.url}
                    </a>
                </td>
                <td>${thread.forum_type}</td>
                <td>${lastCheck}</td>
                <td>
                    <button class="btn btn-sm btn-primary check-thread-btn" data-id="${thread.id}">
                        Check
                    </button>
                    <button class="btn btn-sm btn-danger delete-thread-btn" data-id="${thread.id}">
                        Delete
                    </button>
                </td>
            `;
            threadsTable.appendChild(row);
        });
        
        // Add event listeners to buttons
        document.querySelectorAll('.check-thread-btn').forEach(button => {
            button.addEventListener('click', function() {
                const threadId = this.dataset.id;
                checkThread(threadId);
            });
        });
        
        document.querySelectorAll('.delete-thread-btn').forEach(button => {
            button.addEventListener('click', function() {
                const threadId = this.dataset.id;
                if (confirm('Are you sure you want to delete this thread?')) {
                    deleteThread(threadId);
                }
            });
        });
    }
    
    // Add new thread
    function addThread(performerId, url) {
        setStatus('Adding thread...', 'info');
        
        fetch(`/api/performers/${performerId}/threads`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                url: url
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                setStatus('Thread added successfully', 'success');
                addThreadModal.hide();
                document.getElementById('threadUrl').value = '';
                viewPerformerThreads(performerId, currentPerformerName);
            } else {
                setStatus('Failed to add thread: ' + data.error, 'danger');
            }
        })
        .catch(error => {
            setStatus('Error adding thread: ' + error.message, 'danger');
        });
    }
    
    // Delete thread
    function deleteThread(threadId) {
        setStatus('Deleting thread...', 'info');
        
        fetch(`/api/threads/${threadId}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                setStatus('Thread deleted successfully', 'success');
                viewPerformerThreads(currentPerformerId, currentPerformerName);
            } else {
                setStatus('Failed to delete thread: ' + data.error, 'danger');
            }
        })
        .catch(error => {
            setStatus('Error deleting thread: ' + error.message, 'danger');
        });
    }
    
    // Check thread for new posts
    function checkThread(threadId) {
        setStatus('Checking thread...', 'info');
        resultsContainer.innerHTML = '<p class="text-center">Checking thread for new posts...</p>';
        
        fetch(`/api/check/thread/${threadId}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    if (data.new_posts && data.new_posts.length > 0) {
                        setStatus(`Check completed: Found ${data.new_posts.length} new posts`, 'success');
                    displayResults(data.new_posts);
                } else {
                        setStatus('Check completed: No new posts found', 'info');
                        resultsContainer.innerHTML = '<p class="text-muted">No new posts found.</p>';
                    }
                } else {
                    setStatus('Failed to check thread: ' + data.error, 'danger');
                    resultsContainer.innerHTML = '<p class="text-danger">Error: ' + data.error + '</p>';
                }
            })
            .catch(error => {
                setStatus('Error checking thread: ' + error.message, 'danger');
                resultsContainer.innerHTML = '<p class="text-danger">Error: ' + error.message + '</p>';
                console.error('Error checking thread:', error);
            });
    }
    
    // Check all threads of a performer
    function checkPerformerThreads(performerId) {
        setStatus('Checking performer threads...', 'info');
        resultsContainer.innerHTML = '<p class="text-center">Checking all threads for new posts...</p>';
        
        fetch(`/api/check/performer/${performerId}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    if (data.new_posts && data.new_posts.length > 0) {
                        setStatus(`Check completed: Found ${data.new_posts.length} new posts`, 'success');
                    displayResults(data.new_posts);
                } else {
                        setStatus('Check completed: No new posts found', 'info');
                        resultsContainer.innerHTML = '<p class="text-muted">No new posts found.</p>';
                    }
                } else {
                    setStatus('Failed to check performer threads: ' + data.error, 'danger');
                    resultsContainer.innerHTML = '<p class="text-danger">Error: ' + data.error + '</p>';
                }
            })
            .catch(error => {
                setStatus('Error checking performer threads: ' + error.message, 'danger');
                resultsContainer.innerHTML = '<p class="text-danger">Error: ' + error.message + '</p>';
                console.error('Error checking performer threads:', error);
            });
    }
    
    // Check all threads
    function checkAllThreads() {
        setStatus('Checking all threads...', 'info');
        resultsContainer.innerHTML = '<p class="text-center">Checking all threads for new posts...</p>';
        
        fetch('/api/check/all')
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Server responded with status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log('Check all response:', data); // Debug log
                
                if (data.success) {
                    if (data.new_posts && Array.isArray(data.new_posts) && data.new_posts.length > 0) {
                        console.log(`Found ${data.new_posts.length} new posts. First post:`, data.new_posts[0]); // Debug log
                        setStatus(`Check completed: Found ${data.new_posts.length} new posts`, 'success');
                    displayResults(data.new_posts);
                } else {
                        console.log('No new posts found in response:', data); // Debug log
                        setStatus('Check completed: No new posts found', 'info');
                        resultsContainer.innerHTML = '<p class="text-muted">No new posts found.</p>';
                    }
                } else {
                    console.error('API reported failure:', data.error); // Debug log
                    setStatus('Failed to check threads: ' + (data.error || 'Unknown error'), 'danger');
                    resultsContainer.innerHTML = '<p class="text-danger">Error: ' + (data.error || 'Unknown error') + '</p>';
                }
            })
            .catch(error => {
                console.error('Error checking all threads:', error); // Debug log
                setStatus('Error checking threads: ' + error.message, 'danger');
                resultsContainer.innerHTML = '<p class="text-danger">Error: ' + error.message + '</p>';
            });
    }
    
    // Test PlanetSuzy scraper with example HTML
    function testScraper() {
        setStatus('Testing scraper...', 'info');
        resultsContainer.innerHTML = '<p class="text-center">Testing PlanetSuzy scraper with example HTML...</p>';
        
        fetch('/api/test/planetsuzy')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    setStatus(`Test successful, found ${data.post_count} posts`, 'success');
                    displayResults(data.posts);
                } else {
                    setStatus('Test failed: ' + data.error, 'danger');
                }
            })
            .catch(error => {
                setStatus('Error testing scraper: ' + error.message, 'danger');
            });
    }
    
    // Display results
    function displayResults(posts) {
        console.debug('Displaying results:', posts);
        resultsContainer.innerHTML = '';
        
        if (!posts || posts.length === 0) {
            resultsContainer.innerHTML = '<p class="text-muted">No new posts found.</p>';
            return;
        }
        
        // Add a header with the total number of posts
        const header = document.createElement('div');
        header.className = 'alert alert-info mb-3';
        header.innerHTML = `<strong>Found ${posts.length} new posts</strong>`;
        resultsContainer.appendChild(header);
        
        posts.forEach((post, index) => {
            const postElement = document.createElement('div');
            postElement.className = 'result-item';
            
            let postDate = 'Unknown date';
            if (post.date) {
                try {
                    postDate = new Date(post.date).toLocaleString();
                } catch (e) {
                    // Keep default
                }
            }
            
            let downloadLinksHtml = '';
            if (post.download_links && post.download_links.length > 0) {
                downloadLinksHtml = '<h6>Download Links:</h6><div>';
                post.download_links.forEach(link => {
                    downloadLinksHtml += `<a href="${link}" target="_blank" class="download-link">${link}</a>`;
                });
                downloadLinksHtml += '</div>';
            } else {
                downloadLinksHtml = '<p class="text-muted small">No download links found in this post.</p>';
            }
            
            let imagesHtml = '';
            if (post.images && post.images.length > 0) {
                imagesHtml = '<h6>Images:</h6><div class="row">';
                post.images.forEach(image => {
                    imagesHtml += `
                        <div class="col-md-3 col-sm-4 col-6 mb-2">
                            <a href="${image}" target="_blank">
                                <img src="${image}" class="img-thumbnail" alt="Post image" style="max-height: 100px; width: auto;">
                            </a>
                        </div>
                    `;
                });
                imagesHtml += '</div>';
            }
            
            postElement.innerHTML = `
                <div class="card mb-3">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <h5 class="mb-0">Post #${post.post_id} by ${post.author}</h5>
                    <span class="text-muted">${postDate}</span>
                </div>
                    <div class="card-body">
                        <div class="post-content mb-3">
                            <p>${post.content.substring(0, 300)}${post.content.length > 300 ? '...' : ''}</p>
                </div>
                ${downloadLinksHtml}
                ${imagesHtml}
                    </div>
                </div>
            `;
            
            resultsContainer.appendChild(postElement);
            
            // Add a divider except for the last item
            if (index < posts.length - 1) {
                const divider = document.createElement('hr');
                resultsContainer.appendChild(divider);
            }
        });
    }
    
    // Set status message
    function setStatus(message, type = 'info') {
        statusMessage.className = `alert alert-${type}`;
        statusMessage.textContent = message;
    }
});