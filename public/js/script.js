/**
 * UI & Utility Functions for E-Commerce DBMS System
 */

// Format Currency ($ or PKR)
function formatCurrency(val) {
  const num = parseFloat(val) || 0;
  return '$' + num.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

// Format Date nicely
function formatDate(dateStr) {
  if (!dateStr) return 'N/A';
  const d = new Date(dateStr);
  return d.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}

// Toast Notifications
function showToast(message, type = 'success') {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  
  let icon = '✓';
  if (type === 'error') icon = '✕';
  if (type === 'warning') icon = '⚠';

  toast.innerHTML = `<span style="font-weight: bold;">${icon}</span> <span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(100%)';
    toast.style.transition = 'all 0.3s ease-out';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// Modal Controllers
function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.add('active');
  }
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.remove('active');
  }
}

// Authentication & Session Guard
function checkAuth() {
  const path = window.location.pathname;
  const isLoginPage = path.endsWith('login.html') || path === '/login.html' || path === '/login';
  const user = localStorage.getItem('currentUser');
  
  if (!user && !isLoginPage) {
    window.location.href = 'login.html';
    return false;
  }
  
  // Update sidebar user display if logged in
  if (user) {
    try {
      const userData = JSON.parse(user);
      const nameEl = document.querySelector('.user-name');
      const avatarEl = document.querySelector('.user-avatar');
      if (nameEl && userData.username) {
        nameEl.textContent = userData.username.charAt(0).toUpperCase() + userData.username.slice(1);
      }
      if (avatarEl && userData.username) {
        avatarEl.textContent = userData.username.charAt(0).toUpperCase();
      }
    } catch (e) {}
  }
  return true;
}

function logoutUser() {
  localStorage.removeItem('currentUser');
  showToast('Logged out successfully.');
  setTimeout(() => {
    window.location.href = 'login.html';
  }, 400);
}

// Setup active navigation link based on current page
document.addEventListener('DOMContentLoaded', () => {
  // Check auth first
  if (!checkAuth()) return;

  const currentPath = window.location.pathname;
  const links = document.querySelectorAll('.nav-link');
  
  links.forEach(link => {
    const href = link.getAttribute('href');
    if (href && currentPath.endsWith(href)) {
      link.classList.add('active');
    } else if (currentPath === '/' && href === 'index.html') {
      link.classList.add('active');
    }
  });

  // Close modals on clicking backdrop
  document.querySelectorAll('.modal-overlay').forEach(modal => {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        modal.classList.remove('active');
      }
    });
  });

  // Close buttons
  document.querySelectorAll('.modal-close, [data-close-modal]').forEach(btn => {
    btn.addEventListener('click', () => {
      const modal = btn.closest('.modal-overlay');
      if (modal) modal.classList.remove('active');
    });
  });

  // Inject Floating AI Assistant Widget
  initAiAssistantWidget();
});

// ====================================================================
// AI ASSISTANT WIDGET LOGIC
// ====================================================================

function initAiAssistantWidget() {
  if (document.getElementById('ai-trigger-btn')) return;

  // Don't show on login page
  if (window.location.pathname.endsWith('login.html')) return;

  const widgetHtml = `
    <!-- AI FLOATING BUTTON -->
    <button class="ai-trigger-btn" id="ai-trigger-btn" onclick="toggleAiChat()" title="Open DBMS AI Assistant">
      <div class="ai-pulse-dot"></div>
      <i class="fa-solid fa-wand-magic-sparkles"></i>
      <span>AI Assistant</span>
    </button>

    <!-- AI CHAT WINDOW -->
    <div class="ai-chat-card" id="ai-chat-card">
      <div class="ai-chat-header">
        <div class="ai-chat-title-group">
          <div class="ai-chat-icon">
            <i class="fa-solid fa-robot"></i>
          </div>
          <div>
            <div style="font-weight: 700; font-size: 0.95rem; color: var(--text-main);">DBMS AI Assistant</div>
            <div class="ai-chat-status">
              <span style="display:inline-block; width:6px; height:6px; background:var(--teal-primary); border-radius:50%;"></span>
              Online • Live Relational DB
            </div>
          </div>
        </div>
        <button class="modal-close" onclick="toggleAiChat()" style="color:var(--text-muted);">&times;</button>
      </div>

      <!-- QUICK QUERY CHIPS -->
      <div class="ai-chat-quick-chips">
        <button class="ai-chip" onclick="sendQuickAiPrompt('Which products have low stock?')">⚠️ Low Stock</button>
        <button class="ai-chip" onclick="sendQuickAiPrompt('What is our total sales revenue?')">💰 Total Sales</button>
        <button class="ai-chip" onclick="sendQuickAiPrompt('Who are our top customers?')">👥 Top Customers</button>
        <button class="ai-chip" onclick="sendQuickAiPrompt('Explain 3NF Normalization for this project')">📐 3NF Normalization</button>
        <button class="ai-chip" onclick="sendQuickAiPrompt('Explain ER diagram relationships')">🗂️ ER Diagram</button>
        <button class="ai-chip" onclick="sendQuickAiPrompt('How do ACID transactions protect inventory?')">🛡️ ACID Transactions</button>
      </div>

      <!-- MESSAGES DISPLAY -->
      <div class="ai-messages-area" id="ai-messages-area">
        <div class="ai-msg assistant">
          <p><strong>👋 Welcome to E-Commerce DBMS AI!</strong></p>
          <p>I have direct real-time access to your database. Ask me anything about your <strong>inventory</strong>, <strong>sales</strong>, <strong>suppliers</strong>, or <strong>DBMS project architecture</strong>.</p>
        </div>
      </div>

      <!-- INPUT FIELD -->
      <form class="ai-input-form" onsubmit="handleAiChatSubmit(event)">
        <input type="text" id="ai-input-field" class="ai-input-field" placeholder="Ask AI: e.g. check stock or explain 3NF..." autocomplete="off">
        <button type="submit" class="ai-send-btn" id="ai-send-btn">
          <i class="fa-solid fa-paper-plane"></i>
        </button>
      </form>
    </div>
  `;

  document.body.insertAdjacentHTML('beforeend', widgetHtml);
}

function toggleAiChat() {
  const card = document.getElementById('ai-chat-card');
  if (card) {
    card.classList.toggle('active');
    if (card.classList.contains('active')) {
      document.getElementById('ai-input-field').focus();
    }
  }
}

function sendQuickAiPrompt(text) {
  const input = document.getElementById('ai-input-field');
  if (input) {
    input.value = text;
    handleAiChatSubmit();
  }
}

async function handleAiChatSubmit(e) {
  if (e && e.preventDefault) e.preventDefault();
  const input = document.getElementById('ai-input-field');
  const msgArea = document.getElementById('ai-messages-area');
  const sendBtn = document.getElementById('ai-send-btn');
  const userText = input.value.trim();

  if (!userText) return;

  // Add User Message
  const userDiv = document.createElement('div');
  userDiv.className = 'ai-msg user';
  userDiv.textContent = userText;
  msgArea.appendChild(userDiv);

  input.value = '';
  sendBtn.disabled = true;
  sendBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';

  // Add Loading Indicator
  const loadingDiv = document.createElement('div');
  loadingDiv.className = 'ai-msg assistant';
  loadingDiv.id = 'ai-loading-indicator';
  loadingDiv.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> <em>Querying database...</em>';
  msgArea.appendChild(loadingDiv);
  msgArea.scrollTop = msgArea.scrollHeight;

  try {
    const res = await API.sendAiMessage(userText);
    loadingDiv.remove();

    const aiDiv = document.createElement('div');
    aiDiv.className = 'ai-msg assistant';
    aiDiv.innerHTML = formatAiMarkdown(res.reply || 'No response generated.');
    msgArea.appendChild(aiDiv);
  } catch (err) {
    loadingDiv.remove();
    const errDiv = document.createElement('div');
    errDiv.className = 'ai-msg assistant';
    errDiv.style.borderColor = 'var(--red-danger)';
    errDiv.innerHTML = `<span style="color:var(--red-danger);">⚠️ <strong>Error:</strong> ${err.message}</span>`;
    msgArea.appendChild(errDiv);
  } finally {
    sendBtn.disabled = false;
    sendBtn.innerHTML = '<i class="fa-solid fa-paper-plane"></i>';
    msgArea.scrollTop = msgArea.scrollHeight;
  }
}

// Convert basic Markdown (**bold**, bullets, line breaks) to HTML
function formatAiMarkdown(text) {
  let html = text
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`([^`]+)`/g, '<code style="background:rgba(20,184,166,0.15); color:var(--teal-primary); padding:2px 6px; border-radius:4px; font-family:monospace;">$1</code>')
    .replace(/\n\n/g, '</p><p>')
    .replace(/\n• (.*?)(?=\n|$)/g, '<li>$1</li>')
    .replace(/\n- (.*?)(?=\n|$)/g, '<li>$1</li>');

  if (html.includes('<li>')) {
    html = html.replace(/(<li>.*?<\/li>)/gs, '<ul style="margin:8px 0 8px 18px;">$1</ul>');
  }

  return `<p>${html}</p>`;
}
