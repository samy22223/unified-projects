// Task Manager Firefox Extension - Popup Script

document.addEventListener('DOMContentLoaded', function() {
  const form = document.getElementById('taskForm');
  const submitBtn = document.getElementById('submitBtn');
  const statusDiv = document.getElementById('status');
  const openAppLink = document.getElementById('openApp');

  // Load saved settings
  loadSettings();

  // Handle form submission
  form.addEventListener('submit', async function(e) {
    e.preventDefault();

    const title = document.getElementById('title').value.trim();
    const description = document.getElementById('description').value.trim();
    const priority = document.getElementById('priority').value;
    const dueDate = document.getElementById('dueDate').value;
    const includeUrl = document.getElementById('includeUrl').checked;

    if (!title) {
      showStatus('Please enter a task title', 'error');
      return;
    }

    submitBtn.disabled = true;
    submitBtn.textContent = 'Adding...';

    try {
      // Get current tab information if URL should be included
      let currentTab = null;
      if (includeUrl) {
        const tabs = await browser.tabs.query({ active: true, currentWindow: true });
        currentTab = tabs[0];
      }

      // Prepare task data
      const taskData = {
        title: title,
        description: description,
        priority: priority,
        status: 'Pending'
      };

      if (dueDate) {
        taskData.dueDate = dueDate;
      }

      if (includeUrl && currentTab) {
        taskData.description += (taskData.description ? '\n\n' : '') +
          `Source: ${currentTab.title}\n${currentTab.url}`;
      }

      // Send task to API
      await addTask(taskData);

      showStatus('Task added successfully!', 'success');

      // Clear form
      form.reset();

      // Close popup after short delay
      setTimeout(() => {
        window.close();
      }, 1500);

    } catch (error) {
      console.error('Error adding task:', error);
      showStatus('Failed to add task. Please check your settings.', 'error');
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = 'Add Task';
    }
  });

  // Handle open app link
  openAppLink.addEventListener('click', function(e) {
    e.preventDefault();
    browser.tabs.create({ url: getApiBaseUrl().replace('/api', '') });
  });

  // Auto-fill title from selected text
  browser.tabs.executeScript({
    code: 'window.getSelection().toString();'
  }).then(results => {
    if (results && results[0] && results[0].trim()) {
      document.getElementById('title').value = results[0].trim().substring(0, 100);
    }
  }).catch(() => {
    // Ignore errors - selected text is optional
  });
});

async function addTask(taskData) {
  const settings = await getSettings();
  const apiUrl = settings.apiUrl || 'http://localhost:5000';
  const token = settings.token;

  if (!token) {
    throw new Error('No authentication token found. Please configure the extension.');
  }

  const response = await fetch(`${apiUrl}/api/tasks`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify(taskData)
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.message || 'Failed to add task');
  }

  return await response.json();
}

function showStatus(message, type) {
  const statusDiv = document.getElementById('status');
  statusDiv.textContent = message;
  statusDiv.className = `status ${type}`;
  statusDiv.classList.remove('hidden');

  setTimeout(() => {
    statusDiv.classList.add('hidden');
  }, 3000);
}

async function loadSettings() {
  const settings = await getSettings();
  // Settings are loaded, but we don't need to display them in popup
}

async function getSettings() {
  const result = await browser.storage.local.get(['apiUrl', 'token']);
  return {
    apiUrl: result.apiUrl || 'http://localhost:5000',
    token: result.token || ''
  };
}

function getApiBaseUrl() {
  // This would be configurable in a real implementation
  return 'http://localhost:5000/api';
}