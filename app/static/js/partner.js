/**
 * Reuni — Partner & Admin Dashboard Helper Script (CSP-safe)
 */

function toggleInviteForm() {
    const panel = document.getElementById('invite-form-panel');
    if (panel) {
        const isHidden = panel.hidden || window.getComputedStyle(panel).display === 'none';
        if (isHidden) {
            panel.hidden = false;
            panel.style.display = 'block';
            const domainInput = document.getElementById('university_domain');
            if (domainInput) domainInput.focus();
        } else {
            panel.hidden = true;
            panel.style.display = 'none';
        }
    }
}

function toggleDeactivateConfirm(partnerId, showConfirm) {
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
}

function copyESGText() {
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
}

document.addEventListener('DOMContentLoaded', function () {
    // ── 1. Last Updated Live Timestamp clock ──
    const timeEl = document.getElementById('last-updated-time');
    if (timeEl) {
        const now = new Date();
        const pad = (n) => n.toString().padStart(2, '0');
        timeEl.textContent = `${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`;
    }

    // ── 2. Click delegation for dashboard actions (CSP-safe) ──
    document.addEventListener('click', (event) => {
        const inviteToggle = event.target.closest('[data-action="toggle-invite-form"]');
        if (inviteToggle) {
            event.preventDefault();
            toggleInviteForm();
            return;
        }

        const deactivateToggle = event.target.closest('[data-action="toggle-deactivate-confirm"]');
        if (deactivateToggle) {
            event.preventDefault();
            toggleDeactivateConfirm(
                deactivateToggle.dataset.partnerId,
                deactivateToggle.dataset.showConfirm === 'true'
            );
            return;
        }

        const copyButton = event.target.closest('[data-action="copy-esg-text"]');
        if (copyButton) {
            event.preventDefault();
            copyESGText();
            return;
        }

        const printButton = event.target.closest('[data-action="print-report"]');
        if (printButton) {
            event.preventDefault();
            window.print();
        }
    });

    // ── 3. Image fallbacks programmatically ──
    document.querySelectorAll('.partner-avatar-img').forEach(img => {
        img.addEventListener('error', function() {
            this.style.display = 'none';
            const placeholder = this.nextElementSibling;
            if (placeholder && placeholder.classList.contains('partner-avatar-placeholder')) {
                placeholder.style.display = 'flex';
            }
        });
    });
});
