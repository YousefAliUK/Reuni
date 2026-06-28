/**
 * Reuni — Partner & Admin Dashboard Helper Script (CSP-safe)
 */

// 1. Toggle Admin Invite Form Panel (defined globally for HTML onClick triggers)
window.toggleInviteForm = function () {
    const panel = document.getElementById('invite-form-panel');
    if (panel) {
        if (panel.style.display === 'none') {
            panel.style.display = 'block';
            const domainInput = document.getElementById('university_domain');
            if (domainInput) domainInput.focus();
        } else {
            panel.style.display = 'none';
        }
    }
};

// 2. Toggle Partner Deactivation Confirmation (defined globally)
window.toggleDeactivateConfirm = function (partnerId, showConfirm) {
    const normalCells = document.querySelectorAll('.normal-cell-' + partnerId);
    const confirmCell = document.querySelector('.confirm-cell-' + partnerId);
    
    if (normalCells.length && confirmCell) {
        if (showConfirm) {
            normalCells.forEach(cell => cell.style.display = 'none');
            confirmCell.style.display = 'table-cell';
        } else {
            normalCells.forEach(cell => cell.style.display = 'table-cell');
            confirmCell.style.display = 'none';
        }
    }
};

// 3. Copy ESG report text to clipboard (defined globally)
window.copyESGText = function () {
    const textEl = document.getElementById('esg-report-text');
    if (!textEl) return;
    const text = textEl.innerText;
    
    navigator.clipboard.writeText(text).then(() => {
        const btn = document.getElementById('copy-esg-btn');
        if (btn) {
            const originalHTML = btn.innerHTML;
            btn.innerHTML = '<span class="material-symbols-outlined" style="font-size: 16px; color: var(--color-success);" aria-hidden="true">check</span><span style="color: var(--color-success); font-weight: 600;">Copied!</span>';
            setTimeout(() => {
                btn.innerHTML = originalHTML;
            }, 2000);
        }
    });
};

document.addEventListener('DOMContentLoaded', function () {
    // ── 4. Last Updated Live Timestamp clock ──
    const timeEl = document.getElementById('last-updated-time');
    if (timeEl) {
        const now = new Date();
        const pad = (n) => n.toString().padStart(2, '0');
        timeEl.textContent = `${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`;
    }
});
