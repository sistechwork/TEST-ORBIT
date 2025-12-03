function showNotification(message, type = 'info') {
    const container = document.getElementById('notification-container');
    if (!container) return;
    
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    
    const icon = getIconForType(type);
    
    notification.innerHTML = `
        <div class="notification-icon">${icon}</div>
        <div class="notification-message">${message}</div>
        <button class="notification-close" onclick="closeNotification(this)">&times;</button>
    `;
    
    container.appendChild(notification);
    
    setTimeout(() => {
        notification.classList.add('show');
    }, 10);
    
    setTimeout(() => {
        closeNotification(notification.querySelector('.notification-close'));
    }, 5000);
}

function getIconForType(type) {
    const icons = {
        'success': '✓',
        'error': '✕',
        'warning': '⚠',
        'info': 'ℹ'
    };
    return icons[type] || icons['info'];
}

function closeNotification(button) {
    const notification = button.parentElement || button;
    notification.classList.remove('show');
    notification.classList.add('hide');
    
    setTimeout(() => {
        notification.remove();
    }, 300);
}

function showFlashMessages() {
    const flashContainer = document.querySelector('.flash-messages');
    if (!flashContainer) return;
    
    const flashes = flashContainer.querySelectorAll('.flash');
    flashes.forEach(flash => {
        const message = flash.textContent.trim();
        const type = flash.classList.contains('error') ? 'error' : 'success';
        showNotification(message, type);
    });
    
    flashContainer.style.display = 'none';
}

document.addEventListener('DOMContentLoaded', showFlashMessages);
