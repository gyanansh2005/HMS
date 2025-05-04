function showToast(message, type) {
    const toast = document.getElementById('apiToast');
    toast.querySelector('.toast-body').textContent = message;
    toast.className = `toast bg-${type} text-white`;
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
}

// Sidebar toggle for mobile
document.addEventListener('DOMContentLoaded', () => {
    const sidebar = document.getElementById('sidebar');
    const toggler = document.querySelector('.navbar-toggler');
    toggler.addEventListener('click', () => {
        sidebar.classList.toggle('collapsed');
    });
});