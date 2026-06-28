/**
 * Reuni — Chat & Handshake Exchange Logic (CSP-safe)
 */

document.addEventListener('DOMContentLoaded', function () {
    // localStorage helper with graceful fallback
    function lsGet(key, fallback) {
        try { return localStorage.getItem(key); } catch(e) { return fallback; }
    }
    function lsSet(key, value) {
        try { localStorage.setItem(key, value); } catch(e) { /* restricted */ }
    }

    // Helper to get CSRF token from meta tags
    function getCsrfToken() {
        const meta = document.querySelector('meta[name="csrf-token"]');
        return meta ? meta.getAttribute('content') : '';
    }

    // ── 1. Exchange Instructions Accordion State Persistence ──
    const detailsEl = document.getElementById('exchange-instructions-details') || document.getElementById('safe-exchange-details');
    if (detailsEl) {
        if (detailsEl.id === 'exchange-instructions-details') {
            // Read persistence
            const state = lsGet('exchange_guide_open');
            if (state !== null) {
                if (state === 'true') {
                    detailsEl.setAttribute('open', '');
                } else {
                    detailsEl.removeAttribute('open');
                }
            } else {
                detailsEl.setAttribute('open', ''); // default open
            }

            // Toggle listener
            detailsEl.addEventListener('toggle', () => {
                lsSet('exchange_guide_open', detailsEl.hasAttribute('open') ? 'true' : 'false');
            });
        } else {
            // safe-exchange-details behavior (desktop defaults open, mobile has first-time auto-open)
            if (window.innerWidth >= 1024) {
                detailsEl.setAttribute('open', '');
                detailsEl.addEventListener('click', (e) => {
                    if (window.innerWidth >= 1024) {
                        e.preventDefault();
                    }
                });
            } else {
                try {
                    const guideSeen = localStorage.getItem('pin_guide_seen');
                    if (!guideSeen) {
                        detailsEl.setAttribute('open', '');
                        localStorage.setItem('pin_guide_seen', 'true');
                    } else {
                        detailsEl.removeAttribute('open');
                    }
                } catch (e) {
                    detailsEl.setAttribute('open', '');
                }
            }
        }
    }

    // ── 1b. PIN Holder Expiry Countdown ──
    const countdownEl = document.getElementById('expiry-countdown');
    if (countdownEl && countdownEl.dataset.expires) {
        const expiresTime = new Date(countdownEl.dataset.expires).getTime();
        let expiryTimerId = null;
        let hasReloadedAfterExpiry = false;
        
        function updateTimer() {
            const now = new Date().getTime();
            const diff = expiresTime - now;
            
            if (diff <= 0) {
                countdownEl.textContent = "Expired";
                if (expiryTimerId) {
                    clearInterval(expiryTimerId);
                    expiryTimerId = null;
                }
                if (!hasReloadedAfterExpiry) {
                    hasReloadedAfterExpiry = true;
                    location.reload();
                }
                return;
            }
            
            const hours = Math.floor(diff / (1000 * 60 * 60));
            const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
            const seconds = Math.floor((diff % (1000 * 60)) / 1000);
            
            const pad = (n) => n.toString().padStart(2, '0');
            countdownEl.textContent = `Expires in ${pad(hours)}:${pad(minutes)}:${pad(seconds)}`;
            
            if (diff < 30 * 60 * 1000) {
                countdownEl.style.color = 'var(--color-danger)';
                countdownEl.classList.add('warning-pulse');
            } else if (diff < 2 * 60 * 60 * 1000) {
                countdownEl.style.color = 'var(--color-warning)';
                countdownEl.classList.remove('warning-pulse');
            } else {
                countdownEl.style.color = 'var(--color-ink-secondary)';
                countdownEl.classList.remove('warning-pulse');
            }
        }
        
        updateTimer();
        expiryTimerId = setInterval(updateTimer, 1000);
    }

    // ── 1c. PIN Enterer Focus-Advancing & AJAX Submit ──
    const otpForm = document.getElementById('otp-form');
    const otpInputs = document.querySelectorAll('.otp-input');
    const fullPinInput = document.getElementById('full-pin-input');
    const confirmBtn = document.getElementById('confirm-btn');

    if (otpInputs.length && fullPinInput) {
        otpInputs.forEach((input, index) => {
            input.addEventListener('input', function () {
                this.value = this.value.replace(/[^0-9]/g, '');
                if (this.value.length === 1) {
                    if (index < otpInputs.length - 1) {
                        otpInputs[index + 1].focus();
                    }
                }
                syncPinValue();
            });

            input.addEventListener('keydown', function (e) {
                if (e.key === 'Backspace' && this.value.length === 0) {
                    if (index > 0) {
                        otpInputs[index - 1].focus();
                        otpInputs[index - 1].value = '';
                        syncPinValue();
                    }
                }
            });
        });

        function syncPinValue() {
            let currentVal = '';
            otpInputs.forEach(input => {
                currentVal += input.value;
            });
            fullPinInput.value = currentVal;
            
            if (currentVal.length === 4) {
                if (confirmBtn) confirmBtn.disabled = false;
                if (otpForm && !isPinSubmitting) {
                    otpForm.dispatchEvent(new Event('submit', { cancelable: true }));
                }
            } else {
                if (confirmBtn) confirmBtn.disabled = true;
            }
        }

        function countUp(el, target, duration) {
            const start = 0;
            const startTime = performance.now();
            function animate(currentTime) {
                const elapsed = currentTime - startTime;
                const progress = Math.min(elapsed / duration, 1);
                
                const ease = progress === 1 ? 1 : 1 - Math.pow(2, -10 * progress);
                const currentVal = start + (target - start) * ease;
                
                el.textContent = `${currentVal.toFixed(1)} kg`;
                if (progress < 1) {
                    requestAnimationFrame(animate);
                }
            }
            requestAnimationFrame(animate);
        }

        if (window.visualViewport) {
            window.visualViewport.addEventListener('resize', () => {
                if (document.activeElement && document.activeElement.classList.contains('otp-input')) {
                    if (window.visualViewport.height < window.innerHeight * 0.8) {
                        document.activeElement.scrollIntoView({ block: 'center', behavior: 'smooth' });
                    }
                }
            });
        }

        let isPinSubmitting = false;

        if (otpForm) {
            otpForm.addEventListener('submit', function (e) {
                e.preventDefault();
                if (isPinSubmitting) return;
                isPinSubmitting = true;

                if (confirmBtn) {
                    confirmBtn.disabled = true;
                    confirmBtn.innerHTML = '<span>Confirming</span><span class="warning-pulse">…</span>';
                }

                const formData = new FormData(otpForm);

                fetch(otpForm.action, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                })
                .then(response => {
                    const contentType = response.headers.get('Content-Type') || '';
                    if (contentType.includes('application/json')) {
                        return response.json().then(data => {
                            if (!response.ok) return Promise.reject(data);
                            return data;
                        });
                    } else {
                        return Promise.reject({ error: 'A network or system error occurred.' });
                    }
                })
                .then(data => {
                    const card = document.getElementById('pin-interaction-card');
                    if (card) {
                        card.innerHTML = `
                            <div style="text-align: center; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: var(--space-4) 0;" id="success-celebration">
                                <span class="material-symbols-outlined check-circle-animated" style="font-size: 64px; color: var(--color-success); margin-bottom: var(--space-4);">check_circle</span>
                                <h2 style="font-size: 24px; font-weight: 700; color: var(--color-ink-primary); margin: 0; margin-bottom: var(--space-4);">Exchange complete!</h2>
                                
                                <div style="background: var(--color-success-muted); border-radius: var(--radius-xl); padding: 24px; width: 100%; box-sizing: border-box; margin-bottom: var(--space-6);">
                                    <div id="celebration-kg" style="font-family: var(--font-mono); font-size: 40px; font-weight: 800; color: var(--color-success); line-height: 1.2;">0.0 kg</div>
                                    <div style="font-size: 14px; color: var(--color-success); font-weight: 600; margin-top: 4px;">saved from landfill</div>
                                    <div id="celebration-total" style="font-size: 12px; color: var(--color-ink-secondary); font-family: var(--font-mono); margin-top: 8px;"></div>
                                </div>
                                
                                <a id="celebration-redirect" href="#" class="btn btn--primary" style="height: 48px; width: 100%; border-radius: var(--radius-md); font-weight: 600; text-decoration: none; display: flex; align-items: center; justify-content: center; gap: 8px;">
                                    Back to Marketplace
                                    <span class="material-symbols-outlined">arrow_forward</span>
                                </a>
                            </div>
                        `;
                        const totalKg = Number(data.total_kg);
                        const kgSaved = Number(data.kg_saved);
                        const redirectUrl = new URL(data.redirect_url || '/', window.location.origin);

                        if (Number.isFinite(totalKg) && Number.isFinite(kgSaved) && redirectUrl.origin === window.location.origin) {
                            const totalEl = document.getElementById('celebration-total');
                            if (totalEl) totalEl.textContent = `Added to your total: ${totalKg.toFixed(1)} kg overall`;
                            
                            const redirectBtn = document.getElementById('celebration-redirect');
                            if (redirectBtn) redirectBtn.setAttribute('href', `${redirectUrl.pathname}${redirectUrl.search}${redirectUrl.hash}`);

                            const kgEl = document.getElementById('celebration-kg');
                            if (kgEl) {
                                countUp(kgEl, kgSaved, 1000);
                            }
                        }
                    }
                })
                    isPinSubmitting = false;
                    let errorAlert = document.getElementById('pin-error-alert');
                    if (!errorAlert) {
                        errorAlert = document.createElement('div');
                        errorAlert.id = 'pin-error-alert';
                        errorAlert.style.cssText = 'background: var(--color-danger-muted); border: 1px solid var(--color-danger); color: var(--color-danger); border-radius: var(--radius-md); padding: 12px; margin-bottom: var(--space-4); font-size: 13px; font-weight: 500; text-align: center;';
                        otpForm.parentNode.insertBefore(errorAlert, otpForm);
                    }
                    errorAlert.textContent = error.error || 'Incorrect PIN. Please try again.';

                    otpInputs.forEach(input => input.value = '');
                    fullPinInput.value = '';
                    if (confirmBtn) {
                        confirmBtn.disabled = true;
                        confirmBtn.innerHTML = 'Confirm Exchange';
                    }
                    otpInputs[0].focus();

                    if (error.remaining_attempts !== undefined) {
                        const attemptsEl = document.getElementById('attempts-remaining-text');
                        if (attemptsEl) {
                            attemptsEl.textContent = `${error.remaining_attempts} attempt${error.remaining_attempts !== 1 ? 's' : ''} remaining`;
                            attemptsEl.parentNode.style.color = error.remaining_attempts === 1 ? 'var(--color-danger)' : 'var(--color-warning)';
                        }
                    }
                });
            });
        }
    }

    // ── 2. Cancellation Banner Timer ──
    const bannerEl = document.getElementById('cancellation-banner');
    const claimedStr = bannerEl ? bannerEl.dataset.claimed : null;
    if (claimedStr && bannerEl) {
        const claimedTime = new Date(claimedStr).getTime();
        
        function updateCancellationBanner() {
            const now = Date.now();
            const elapsedMs = now - claimedTime;
            const twentyFourHoursMs = 24 * 60 * 60 * 1000;
            
            if (elapsedMs < twentyFourHoursMs) {
                // State A: within 24h
                const remainingMs = twentyFourHoursMs - elapsedMs;
                const hours = Math.floor(remainingMs / (1000 * 60 * 60));
                const minutes = Math.floor((remainingMs % (1000 * 60 * 60)) / (1000 * 60));
                
                bannerEl.style.background = 'var(--color-success-muted)';
                bannerEl.style.border = '1px solid var(--color-success)';
                bannerEl.style.color = 'var(--color-success)';
                bannerEl.innerHTML = `
                    <span class="material-symbols-outlined" style="font-size: 16px;">check_circle</span>
                    <span>Free cancellation — <span style="font-family: var(--font-mono); font-weight: 700;">${hours}h ${minutes}m</span> left to cancel without penalty</span>
                `;
            } else {
                // State B: after 24h
                bannerEl.style.background = 'var(--color-warning-muted)';
                bannerEl.style.border = '1px solid var(--color-warning)';
                bannerEl.style.color = 'var(--color-warning)';
                bannerEl.innerHTML = `
                    <span class="material-symbols-outlined" style="font-size: 16px;">warning</span>
                    <span>Late cancellation — cancelling now will result in a small trust adjustment</span>
                `;
            }
        }
        
        updateCancellationBanner();
        setInterval(updateCancellationBanner, 60000);
    }

    // ── 3. Cancellation Confirm Block Toggles ──
    const cancelTrigger = document.getElementById('cancel-trigger-btn');
    const cancelConfirmBlock = document.getElementById('cancel-confirm-block');
    const cancelActionBlock = document.getElementById('cancel-action-block');
    const cancelAbort = document.getElementById('cancel-abort-btn');

    if (cancelTrigger && cancelConfirmBlock && cancelActionBlock && cancelAbort) {
        cancelTrigger.addEventListener('click', () => {
            cancelActionBlock.style.display = 'none';
            cancelConfirmBlock.style.display = 'flex';
        });
        cancelAbort.addEventListener('click', () => {
            cancelConfirmBlock.style.display = 'none';
            cancelActionBlock.style.display = 'block';
        });
    }

    // ── 4. In-App Chat Polling & Send Logic ──
    const chatThread = document.getElementById('chat-thread');
    const chatMessages = document.getElementById('chat-messages');
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');
    const chatSendBtn = document.getElementById('chat-send-btn');
    const chatCharCounter = document.getElementById('chat-char-counter');
    const chatErrorMsg = document.getElementById('chat-error-message');
    const chatInputContainer = document.getElementById('chat-input-container');
    const wrapper = document.getElementById('pin-page-wrapper');

    if (chatThread && chatMessages && wrapper) {
        const itemId = parseInt(wrapper.dataset.itemId);
        const currentUserId = parseInt(wrapper.dataset.currentUserId);
        const partnerName = wrapper.dataset.partnerName;
        
        let pollInterval = null;
        let lastMessageId = 0;
        let isPolling = false;
        let lastActivityTime = Date.now();
        let isIdle = false;
        let chatPausedBanner = null;

        // Get initial lastMessageId from existing message elements
        const existingRows = chatMessages.querySelectorAll('.chat-message-row');
        existingRows.forEach(row => {
            const id = parseInt(row.dataset.messageId);
            if (id > lastMessageId) lastMessageId = id;
        });

        // Auto scroll to bottom
        function scrollToBottom() {
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
        scrollToBottom();

        // Format ISO time to HH:MM
        function formatTime(isoString) {
            try {
                const date = new Date(isoString);
                return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false });
            } catch (e) {
                return '';
            }
        }

        // Render message row
        function createMessageElement(msg, partnerName) {
            const row = document.createElement('div');
            row.className = `chat-message-row ${msg.is_mine ? 'chat-message-row--mine' : 'chat-message-row--theirs'}`;
            row.dataset.messageId = msg.id;

            if (!msg.is_mine) {
                const avatar = document.createElement('span');
                avatar.className = 'chat-avatar chat-avatar--small';
                avatar.setAttribute('aria-hidden', 'true');
                avatar.textContent = partnerName[0].toUpperCase();
                row.appendChild(avatar);
            }

            const bubble = document.createElement('div');
            bubble.className = `chat-bubble ${msg.is_mine ? 'chat-bubble--mine' : 'chat-bubble--theirs'}`;

            const textDiv = document.createElement('div');
            textDiv.className = 'chat-bubble-text';
            textDiv.textContent = msg.content; // Strict XSS protection
            bubble.appendChild(textDiv);

            const metaDiv = document.createElement('div');
            metaDiv.className = 'chat-bubble-meta';

            const timestamp = document.createElement('span');
            timestamp.className = 'chat-timestamp';
            timestamp.textContent = formatTime(msg.created_at);
            metaDiv.appendChild(timestamp);

            if (msg.is_mine) {
                const seenStatus = document.createElement('span');
                seenStatus.className = 'chat-seen-status';
                seenStatus.id = `seen-${msg.id}`;
                if (msg.is_read) {
                    seenStatus.textContent = 'Seen';
                }
                metaDiv.appendChild(seenStatus);
            }

            bubble.appendChild(metaDiv);
            row.appendChild(bubble);
            return row;
        }

        // Fetch and update messages
        async function fetchMessages() {
            if (isPolling) return;
            isPolling = true;

            try {
                const response = await fetch(`/api/messages/${itemId}?since_id=${lastMessageId}`, {
                    headers: { 'X-Requested-With': 'XMLHttpRequest' }
                });
                if (response.ok) {
                    const data = await response.json();
                    
                    // Check thread status
                    if (data.thread_status !== 'active') {
                        stopPolling();
                        if (chatInputContainer) {
                            if (data.thread_status === 'sold') {
                                chatInputContainer.innerHTML = `
                                    <div class="chat-terminal-banner">
                                        <span class="material-symbols-outlined" aria-hidden="true" style="font-size: 18px;">lock</span>
                                        <span>This transaction has been completed. Chat is now read-only.</span>
                                    </div>
                                `;
                            } else {
                                chatInputContainer.innerHTML = `
                                    <div class="chat-terminal-banner">
                                        <span class="material-symbols-outlined" aria-hidden="true" style="font-size: 18px;">lock</span>
                                        <span>This claim has been cancelled. Chat is read-only.</span>
                                    </div>
                                `;
                            }
                        }
                    }

                    // Determine if scroll is near bottom before update
                    const isNearBottom = chatMessages.scrollHeight - chatMessages.clientHeight - chatMessages.scrollTop < 60;

                    // Append new messages
                    if (data.messages && data.messages.length > 0) {
                        data.messages.forEach(msg => {
                            if (!chatMessages.querySelector(`[data-message-id="${msg.id}"]`)) {
                                chatMessages.appendChild(createMessageElement(msg, partnerName));
                            }
                            if (msg.id > lastMessageId) lastMessageId = msg.id;
                        });
                        if (isNearBottom) {
                            scrollToBottom();
                        }
                    }

                    // Update read receipts
                    if (data.seen_ids) {
                        data.seen_ids.forEach(id => {
                            const seenEl = document.getElementById(`seen-${id}`);
                            if (seenEl) {
                                seenEl.textContent = 'Seen';
                            }
                        });
                    }
                }
            } catch (e) {
                console.error('Chat poll error:', e);
            } finally {
                isPolling = false;
            }
        }

        // Start Polling
        function startPolling() {
            if (pollInterval) clearInterval(pollInterval);
            if (chatPausedBanner) {
                chatPausedBanner.remove();
                chatPausedBanner = null;
            }
            isIdle = false;
            fetchMessages();
            pollInterval = setInterval(fetchMessages, 4000);
        }

        // Stop Polling
        function stopPolling() {
            if (pollInterval) {
                clearInterval(pollInterval);
                pollInterval = null;
            }
        }

        // Handle Send Message
        if (chatForm && chatInput) {
            chatInput.addEventListener('input', () => {
                const len = chatInput.value.length;
                if (chatCharCounter) chatCharCounter.textContent = `${len}/1000`;
                
                if (len > 1000) {
                    if (chatCharCounter) chatCharCounter.style.color = 'var(--color-danger)';
                    if (chatSendBtn) chatSendBtn.disabled = true;
                } else {
                    if (chatCharCounter) chatCharCounter.style.color = 'var(--color-ink-tertiary)';
                    if (chatSendBtn) chatSendBtn.disabled = (len === 0);
                }

                // Auto resize height
                chatInput.style.height = '48px';
                const scrollHeight = chatInput.scrollHeight;
                chatInput.style.height = scrollHeight + 'px';
                if (scrollHeight > 120) {
                    chatInput.style.overflowY = 'auto';
                } else {
                    chatInput.style.overflowY = 'hidden';
                }
            });

            // Enter key mapping
            chatInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    if (window.matchMedia('(hover: hover)').matches) {
                        e.preventDefault();
                        chatForm.requestSubmit();
                    }
                }
            });

            chatForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                const content = chatInput.value.trim();
                if (!content) return;

                if (chatSendBtn) chatSendBtn.disabled = true;
                if (chatErrorMsg) chatErrorMsg.style.display = 'none';

                try {
                    const csrfToken = getCsrfToken();
                    const response = await fetch(`/api/messages/${itemId}/send`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': csrfToken,
                            'X-Requested-With': 'XMLHttpRequest'
                        },
                        body: JSON.stringify({ content: content })
                    });

                    const contentType = response.headers.get('Content-Type') || '';
                    if (!contentType.includes('application/json')) {
                        throw new Error('A network or system error occurred.');
                    }
                    const data = await response.json();
                    if (response.ok) {
                        const messageId = String(data.message.id);
                        const alreadyRendered = !!chatMessages.querySelector(`[data-message-id="${messageId}"]`);
                        if (!alreadyRendered) {
                            chatMessages.appendChild(createMessageElement(data.message, partnerName));
                        }
                        if (data.message.id > lastMessageId) lastMessageId = data.message.id;
                        chatInput.value = '';
                        chatInput.style.height = '48px';
                        chatInput.style.overflowY = 'hidden';
                        if (chatCharCounter) chatCharCounter.textContent = '0/1000';
                        scrollToBottom();
                        lastActivityTime = Date.now();
                    } else {
                        if (chatErrorMsg) {
                            chatErrorMsg.textContent = data.error || 'Failed to send message.';
                            chatErrorMsg.style.display = 'block';
                        }
                        if (chatSendBtn) chatSendBtn.disabled = false;
                    }
                } catch (err) {
                    console.error('Send error:', err);
                    if (chatErrorMsg) {
                        chatErrorMsg.textContent = 'A network error occurred. Please try again.';
                        chatErrorMsg.style.display = 'block';
                    }
                    if (chatSendBtn) chatSendBtn.disabled = false;
                }
            });
        }

        // Visibility API triggers
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                stopPolling();
            } else if (!isIdle) {
                startPolling();
            }
        });

        // Reset inactivity timer on events
        function resetActivity() {
            lastActivityTime = Date.now();
            if (isIdle) {
                isIdle = false;
                if (chatPausedBanner) {
                    chatPausedBanner.remove();
                    chatPausedBanner = null;
                }
                startPolling();
            }
        }

        window.addEventListener('mousemove', resetActivity);
        window.addEventListener('keydown', resetActivity);
        window.addEventListener('scroll', resetActivity);
        window.addEventListener('click', resetActivity);

        // Idle Loop
        setInterval(() => {
            const idleLimit = 2 * 60 * 1000; // 2 minutes
            if (Date.now() - lastActivityTime > idleLimit && !isIdle && pollInterval) {
                isIdle = true;
                stopPolling();
                
                chatPausedBanner = document.createElement('div');
                chatPausedBanner.className = 'chat-paused-banner';
                chatPausedBanner.innerHTML = `
                    <span class="material-symbols-outlined" style="font-size: 14px;">pause_circle</span>
                    <span>Chat paused due to inactivity. Move mouse or press any key to resume.</span>
                `;
                chatThread.insertBefore(chatPausedBanner, chatMessages);
            }
        }, 5000);

        // Start Polling initially
        startPolling();
    }

    // ── 5. QR Code Panel Toggles ──
    const showQrBtn = document.getElementById('show-qr-btn');
    const hideQrBtn = document.getElementById('hide-qr-btn');
    const pinDigitsBlock = document.getElementById('pin-digits-block');
    const qrPanel = document.getElementById('qr-panel');

    if (showQrBtn && hideQrBtn && pinDigitsBlock && qrPanel) {
        showQrBtn.addEventListener('click', () => {
            pinDigitsBlock.style.display = 'none';
            qrPanel.style.display = 'block';
        });
        hideQrBtn.addEventListener('click', () => {
            qrPanel.style.display = 'none';
            pinDigitsBlock.style.display = 'block';
        });
    }
});
