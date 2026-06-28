/**
 * Reuni — Auth Flow JS Helper (CSP-safe, reusable visibility & validations)
 */

// 1. Password visibility toggle (defined globally for inline HTML click handlers)
function togglePasswordVisibilityByInput(input) {
    if (!input) return;
    const triggerBtn = input.nextElementSibling;
    if (!triggerBtn) return;
    const icon = triggerBtn.querySelector('.material-symbols-outlined');
    if (!icon) return;

    if (input.type === 'password') {
        input.type = 'text';
        icon.textContent = 'visibility_off';
        triggerBtn.setAttribute('aria-label', 'Hide password');
        triggerBtn.setAttribute('aria-pressed', 'true');
    } else {
        input.type = 'password';
        icon.textContent = 'visibility';
        triggerBtn.setAttribute('aria-label', 'Show password');
        triggerBtn.setAttribute('aria-pressed', 'false');
    }
}

document.addEventListener('DOMContentLoaded', function () {
    // 1. Password visibility toggle (replace inline onclick)
    document.addEventListener('click', function (e) {
        const toggleBtn = e.target.closest('[data-toggle-password]');
        if (toggleBtn) {
            const input = document.getElementById(toggleBtn.dataset.togglePassword);
            togglePasswordVisibilityByInput(input);
        }
    });

    // 2. Email Validation Hint ──
    const emailInput = document.getElementById('email');
    const validationHint = document.getElementById('email-validation-hint');

    if (emailInput && validationHint) {
        emailInput.addEventListener('blur', function () {
            const email = emailInput.value.trim().toLowerCase();
            if (!email) {
                validationHint.style.display = 'none';
                return;
            }

            if (email.endsWith('@brookes.ac.uk') || (email.includes('@') && email.split('@')[1].endsWith('.ac.uk'))) {
                validationHint.textContent = '✓ University email detected';
                validationHint.style.color = 'var(--color-success)';
                validationHint.style.display = 'block';
            } else {
                validationHint.textContent = '✗ Must be a valid university email';
                validationHint.style.color = 'var(--color-danger)';
                validationHint.style.display = 'block';
            }
        });
    }

    // ── 3. Real-time Password Match Validation ──
    const passwordInput = document.getElementById('password');
    const confirmInput = document.getElementById('confirm_password');
    const newPasswordInput = document.getElementById('new_password'); // settings/reset flow
    
    const activePassInput = passwordInput || newPasswordInput;

    if (activePassInput && confirmInput) {
        function checkPasswordMatch() {
            if (confirmInput.value && confirmInput.value !== activePassInput.value) {
                confirmInput.setCustomValidity('Passwords do not match');
            } else {
                confirmInput.setCustomValidity('');
            }
        }
        confirmInput.addEventListener('input', checkPasswordMatch);
        activePassInput.addEventListener('input', function () {
            if (confirmInput.value) checkPasswordMatch();
        });
    }

    // ── 4. Password Strength Indicator ──
    if (activePassInput) {
        activePassInput.addEventListener('input', function () {
            const val = activePassInput.value;
            let score = 0;
            if (val.length >= 8) score++;
            if (/[A-Z]/.test(val) && /[a-z]/.test(val)) score++;
            if (/[0-9]/.test(val)) score++;
            
            const bar1 = document.getElementById('strength-bar-1');
            const bar2 = document.getElementById('strength-bar-2');
            const bar3 = document.getElementById('strength-bar-3');
            const label = document.getElementById('strength-label');
            
            if (bar1 && bar2 && bar3 && label) {
                bar1.style.background = 'var(--color-surface-raised)';
                bar2.style.background = 'var(--color-surface-raised)';
                bar3.style.background = 'var(--color-surface-raised)';
                
                if (val.length < 8) {
                    label.textContent = 'Strength: too short';
                } else if (score === 1) {
                    bar1.style.background = 'var(--color-danger)';
                    label.textContent = 'Strength: weak';
                } else if (score === 2) {
                    bar1.style.background = 'var(--color-warning)';
                    bar2.style.background = 'var(--color-warning)';
                    label.textContent = 'Strength: medium';
                } else if (score === 3) {
                    bar1.style.background = 'var(--color-success)';
                    bar2.style.background = 'var(--color-success)';
                    bar3.style.background = 'var(--color-success)';
                    label.textContent = 'Strength: strong';
                }
            }
        });
    }

    // ── 5. OTP / Email Verification Auto-Advance ──
    const otpForm = document.getElementById('otp-form');
    const otpInputs = document.querySelectorAll('.otp-digit');
    const fullCodeInput = document.getElementById('full-code-input');
    const confirmBtn = document.getElementById('confirm-btn');

    if (otpInputs.length && fullCodeInput) {
        otpInputs.forEach((input, index) => {
            input.addEventListener('blur', function() {
                if (this.value.length === 1) {
                    this.classList.add('otp-digit-box--success');
                } else {
                    this.classList.remove('otp-digit-box--success');
                }
            });

            input.addEventListener('input', function () {
                this.value = this.value.replace(/[^0-9]/g, '');
                
                if (this.value.length === 1) {
                    this.classList.add('otp-digit-box--success');
                    if (index < otpInputs.length - 1) {
                        otpInputs[index + 1].focus();
                    }
                } else {
                    this.classList.remove('otp-digit-box--success');
                }
                syncCodeValue();
            });

            input.addEventListener('keydown', function (e) {
                if (e.key === 'Backspace' && this.value.length === 0) {
                    if (index > 0) {
                        otpInputs[index - 1].focus();
                        otpInputs[index - 1].value = '';
                        otpInputs[index - 1].classList.remove('otp-digit-box--success');
                        syncCodeValue();
                    }
                }
            });
        });

        function syncCodeValue() {
            let currentVal = '';
            otpInputs.forEach(input => {
                currentVal += input.value;
            });
            fullCodeInput.value = currentVal;
            
            if (currentVal.length === 6) {
                if (confirmBtn) confirmBtn.disabled = false;
                if (otpForm) otpForm.submit();
            } else {
                if (confirmBtn) confirmBtn.disabled = true;
            }
        }
    }

    // ── 6. Account Deletion Modal (Danger Zone) ──
    const btnShowDelete = document.getElementById('btn-show-delete-confirm');
    const btnCancelDelete = document.getElementById('btn-cancel-delete');
    const deleteModal = document.getElementById('delete-modal');
    const deleteInput = document.getElementById('delete_confirm_text');
    const deleteSubmit = document.getElementById('btn-delete-submit');
    
    if (btnShowDelete && deleteModal) {
        btnShowDelete.addEventListener('click', function() {
            deleteModal.classList.add('modal-overlay--open');
            if (deleteInput) deleteInput.focus();
        });
    }
    if (btnCancelDelete && deleteModal) {
        btnCancelDelete.addEventListener('click', function() {
            deleteModal.classList.remove('modal-overlay--open');
            if (deleteInput) deleteInput.value = '';
            if (deleteSubmit) deleteSubmit.disabled = true;
        });
    }

    if (deleteModal) {
        deleteModal.addEventListener('click', function(e) {
            if (e.target === deleteModal) {
                deleteModal.classList.remove('modal-overlay--open');
                if (deleteInput) deleteInput.value = '';
                if (deleteSubmit) deleteSubmit.disabled = true;
            }
        });
    }

    if (deleteInput && deleteSubmit) {
        deleteInput.addEventListener('input', function() {
            if (deleteInput.value.trim() === 'DELETE') {
                deleteSubmit.disabled = false;
            } else {
                deleteSubmit.disabled = true;
            }
        });
    }
    const deleteForm = document.getElementById('delete-form');
    if (deleteForm) {
        deleteForm.addEventListener('submit', function (e) {
            const deleteInput = document.getElementById('delete_confirm_text');
            const val = deleteInput ? deleteInput.value.trim() : '';
            if (val !== 'DELETE') {
                e.preventDefault();
                alert('Please type DELETE exactly to confirm.');
            }
        });
    }
});
