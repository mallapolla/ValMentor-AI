// Global App Controls
document.addEventListener("DOMContentLoaded", () => {
    // Mobile Sidebar Toggles
    const toggleBtn = document.getElementById("sidebar-toggle-btn");
    const closeBtn = document.getElementById("sidebar-close-btn");
    const sidebar = document.getElementById("sidebar-panel");

    if (toggleBtn && sidebar) {
        toggleBtn.addEventListener("click", () => {
            sidebar.classList.remove("-translate-x-full");
        });
    }

    if (closeBtn && sidebar) {
        closeBtn.addEventListener("click", () => {
            sidebar.classList.add("-translate-x-full");
        });
    }
});

// Toast controller
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `p-4 rounded-xl border border-slate-700 bg-slate-900/90 text-slate-100 flex items-center justify-between shadow-2xl glass-card transition-all duration-300 transform translate-y-2 opacity-0`;
    
    let emoji = 'ℹ️';
    if (type === 'success') emoji = '🟢';
    if (type === 'error') emoji = '🔴';

    toast.innerHTML = `
        <span class="text-sm font-semibold mr-4">${emoji} ${message}</span>
        <button class="text-slate-400 hover:text-slate-200" onclick="this.parentElement.remove()">
            <svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
        </button>
    `;

    container.appendChild(toast);
    
    // Animate in
    setTimeout(() => {
        toast.classList.remove('translate-y-2', 'opacity-0');
    }, 10);

    // Auto close
    setTimeout(() => {
        toast.classList.add('opacity-0');
        setTimeout(() => toast.remove(), 300);
    }, 5000);
}
