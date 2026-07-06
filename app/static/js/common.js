/**
 * Reuni — Global Shared UI Logic (Pure Vanilla JS, CSP-safe)
 */

document.addEventListener('DOMContentLoaded', function () {
    // localStorage helper with graceful fallback for restricted/private browsers
    function lsGet(key, fallback) {
        try { return localStorage.getItem(key); } catch(e) { return fallback; }
    }
    function lsSet(key, value) {
        try { localStorage.setItem(key, value); } catch(e) { /* restricted — silently skip */ }
    }
    function lsRemove(key) {
        try { localStorage.removeItem(key); } catch(e) { /* restricted — silently skip */ }
    }

    // ── 1. Theme Toggling Logic ──
    const themeToggle = document.getElementById('theme-toggle');
    const mobileThemeToggle = document.getElementById('mobile-theme-toggle');
    
    function getThemeCookie() {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; theme=`);
        return parts.length === 2 ? parts.pop().split(';').shift() : null;
    }

    function updateThemeUI(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        lsSet('theme', theme);

        // Set cookie shared across subdomains
        const hostParts = window.location.hostname.split('.');
        let domainAttr = "";
        const isLocalhostSubdomain = hostParts.length >= 2 && hostParts[hostParts.length - 1] === "localhost";
        if (isLocalhostSubdomain) domainAttr = "; domain=.localhost";
        else if (hostParts.length >= 2) domainAttr = `; domain=.${hostParts.slice(-2).join('.')}`;
        document.cookie = `theme=${theme}; path=/; max-age=31536000; SameSite=Lax${domainAttr}`;

        const themeToggleIcon = document.getElementById('theme-toggle-icon');
        if (themeToggleIcon) {
            themeToggleIcon.textContent = theme === 'dark' ? 'dark_mode' : 'light_mode';
        }

        const mobileThemeToggleIcon = document.getElementById('mobile-theme-toggle-icon');
        if (mobileThemeToggleIcon) {
            mobileThemeToggleIcon.textContent = theme === 'dark' ? 'dark_mode' : 'light_mode';
        }
    }

    const currentTheme = getThemeCookie() || lsGet('theme') || 'light';
    updateThemeUI(currentTheme);

    // Re-apply theme state on pageshow (ensures bfcache recoveries sync correctly)
    window.addEventListener('pageshow', () => {
        const current = getThemeCookie() || lsGet('theme') || 'light';
        updateThemeUI(current);
    });
    
    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            const current = document.documentElement.getAttribute('data-theme') || 'light';
            const next = current === 'dark' ? 'light' : 'dark';
            updateThemeUI(next);
        });
    }
    if (mobileThemeToggle) {
        mobileThemeToggle.addEventListener('click', () => {
            const current = document.documentElement.getAttribute('data-theme') || 'light';
            const next = current === 'dark' ? 'light' : 'dark';
            updateThemeUI(next);
        });
    }

    // ── 2. User Dropdown Toggle (Desktop) ──
    const dropdownTrigger = document.getElementById('profile-dropdown-trigger');
    const dropdownMenu = document.getElementById('profile-dropdown-menu');
    if (dropdownTrigger && dropdownMenu) {
        dropdownTrigger.addEventListener('click', function (e) {
            e.stopPropagation();
            const isOpen = dropdownMenu.classList.contains('user-dropdown__menu--open');
            if (isOpen) {
                dropdownMenu.classList.remove('user-dropdown__menu--open');
                dropdownTrigger.setAttribute('aria-expanded', 'false');
            } else {
                dropdownMenu.classList.add('user-dropdown__menu--open');
                dropdownTrigger.setAttribute('aria-expanded', 'true');
            }
        });
        
        document.addEventListener('click', function () {
            dropdownMenu.classList.remove('user-dropdown__menu--open');
            dropdownTrigger.setAttribute('aria-expanded', 'false');
        });
    }

    // ── 3. Mobile Navigation Drawer (Hamburger menu) ──
    const hamburgerBtn = document.getElementById('mobile-hamburger-btn');
    const drawer = document.getElementById('mobile-drawer');
    const backdrop = document.getElementById('mobile-drawer-backdrop');
    const drawerClose = document.getElementById('mobile-drawer-close');
    
    function openDrawer() {
        if (drawer && backdrop) {
            backdrop.classList.add('mobile-drawer-backdrop--open');
            drawer.classList.add('mobile-drawer--open');
        }
    }
    
    function closeDrawer() {
        if (drawer && backdrop) {
            backdrop.classList.remove('mobile-drawer-backdrop--open');
            drawer.classList.remove('mobile-drawer--open');
        }
    }
    
    if (hamburgerBtn) hamburgerBtn.addEventListener('click', openDrawer);
    if (drawerClose) drawerClose.addEventListener('click', closeDrawer);
    if (backdrop) backdrop.addEventListener('click', closeDrawer);

    // ── 4. Desktop Search Form & Dropdown Panel ──
    const desktopSearchForm = document.getElementById('desktop-search-form');
    const desktopSearchInput = document.getElementById('desktop-search-input');
    const desktopSearchDropdown = document.getElementById('desktop-search-dropdown');
    const desktopSearchClearBtn = document.getElementById('desktop-search-clear-btn');
    const desktopChipsContainer = document.getElementById('desktop-search-chips-container');

    function getRecentSearches() {
        try {
            const parsed = JSON.parse(lsGet('recent_searches', '[]') || '[]');
            return Array.isArray(parsed) ? parsed.filter(s => typeof s === 'string') : [];
        } catch (e) {
            lsRemove('recent_searches');
            return [];
        }
    }

    function saveRecentSearch(query) {
        if (!query) return;
        const searches = [query, ...getRecentSearches().filter(s => s !== query)].slice(0, 5);
        lsSet('recent_searches', JSON.stringify(searches));
    }

    function renderDesktopRecentSearches() {
        if (!desktopChipsContainer || !desktopSearchClearBtn) return;
        const searches = getRecentSearches();
        if (searches.length === 0) {
            if (desktopSearchDropdown) desktopSearchDropdown.style.display = 'none';
            return;
        }
        if (desktopSearchDropdown && document.activeElement === desktopSearchInput) {
            desktopSearchDropdown.style.display = 'block';
        }
        desktopChipsContainer.innerHTML = '';
        searches.forEach(search => {
            const chip = document.createElement('button');
            chip.type = 'button';
            chip.className = 'recent-search-chip';
            const icon = document.createElement('span');
            icon.className = 'material-symbols-outlined';
            icon.setAttribute('aria-hidden', 'true');
            icon.style.fontSize = '14px';
            icon.textContent = 'history';
            const label = document.createElement('span');
            label.textContent = search;
            chip.append(icon, label);
            chip.addEventListener('click', (e) => {
                e.stopPropagation();
                desktopSearchInput.value = search;
                if (desktopSearchForm) desktopSearchForm.submit();
            });
            desktopChipsContainer.appendChild(chip);
        });
    }

    if (desktopSearchInput) {
        desktopSearchInput.addEventListener('focus', () => {
            renderDesktopRecentSearches();
        });
        document.addEventListener('click', (e) => {
            if (desktopSearchDropdown && desktopSearchForm && !desktopSearchForm.contains(e.target)) {
                desktopSearchDropdown.style.display = 'none';
            }
        });
    }

    if (desktopSearchClearBtn) {
        desktopSearchClearBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            lsRemove('recent_searches');
            if (desktopSearchDropdown) desktopSearchDropdown.style.display = 'none';
        });
    }

    if (desktopSearchForm) {
        desktopSearchForm.addEventListener('submit', () => {
            const query = desktopSearchInput.value.trim();
            saveRecentSearch(query);
        });
    }

    // ── 5. Mobile Full-screen Search Overlay ──
    const searchOverlay = document.getElementById('search-overlay');
    const searchOverlayClose = document.getElementById('search-overlay-close');
    const searchOverlayInput = document.getElementById('search-overlay-input');
    const mobileSearchTabBtn = document.getElementById('mobile-tab-search-btn');
    const searchClearBtn = document.getElementById('search-clear-btn');
    const chipsContainer = document.getElementById('search-recent-chips-container');
    const overlayForm = searchOverlay ? searchOverlay.querySelector('form') : null;

    function openSearchOverlay() {
        if (searchOverlay) {
            searchOverlay.classList.add('search-overlay--open');
            document.body.style.overflow = 'hidden';
            setTimeout(() => {
                if (searchOverlayInput) searchOverlayInput.focus();
            }, 50);
            renderRecentSearches();
        }
    }

    function closeSearchOverlay() {
        if (searchOverlay) {
            searchOverlay.classList.remove('search-overlay--open');
            document.body.style.overflow = '';
        }
    }

    function renderRecentSearches() {
        if (!chipsContainer || !searchClearBtn) return;
        const searches = getRecentSearches();
        const historySection = document.getElementById('search-overlay-history');
        if (searches.length === 0) {
            if (historySection) historySection.style.display = 'none';
            return;
        }
        if (historySection) historySection.style.display = 'block';
        chipsContainer.innerHTML = '';
        searches.forEach(search => {
            const chip = document.createElement('button');
            chip.type = 'button';
            chip.className = 'recent-search-chip';
            const icon = document.createElement('span');
            icon.className = 'material-symbols-outlined';
            icon.setAttribute('aria-hidden', 'true');
            icon.style.fontSize = '14px';
            icon.textContent = 'history';
            const label = document.createElement('span');
            label.textContent = search;
            chip.append(icon, label);
            chip.addEventListener('click', () => {
                if (searchOverlayInput) searchOverlayInput.value = search;
                if (overlayForm) overlayForm.submit();
            });
            chipsContainer.appendChild(chip);
        });
    }

    if (mobileSearchTabBtn) mobileSearchTabBtn.addEventListener('click', openSearchOverlay);
    if (searchOverlayClose) searchOverlayClose.addEventListener('click', closeSearchOverlay);

    if (overlayForm) {
        overlayForm.addEventListener('submit', () => {
            if (searchOverlayInput) {
                const query = searchOverlayInput.value.trim();
                saveRecentSearch(query);
            }
        });
    }

    if (searchClearBtn) {
        searchClearBtn.addEventListener('click', () => {
            lsRemove('recent_searches');
            renderRecentSearches();
        });
    }

    // ── 6. Global Notifications System ──
    const notifBell = document.getElementById('notification-bell-trigger');
    const mobileNotifBell = document.getElementById('mobile-notification-bell-trigger');
    const notifDropdown = document.getElementById('notification-dropdown');
    const mobileNotifDropdown = document.getElementById('mobile-notification-dropdown');
    const notifList = document.getElementById('notification-list');
    const mobileNotifList = document.getElementById('mobile-notification-list');
    const notifBadge = document.getElementById('notification-badge');
    const mobileNotifBadge = document.getElementById('mobile-notification-badge');
    const clearAllBtn = document.getElementById('notification-clear-all');
    const mobileClearAllBtn = document.getElementById('mobile-notification-clear-all');

    let notifPollInterval = null;

    // Helper to get CSRF token securely from meta tags
    function getCsrfToken() {
        const meta = document.querySelector('meta[name="csrf-token"]');
        return meta ? meta.getAttribute('content') : '';
    }

    // Toggle dropdown
    function toggleNotifDropdown(e) {
        if (e) e.stopPropagation();
        
        // Close other dropdowns if open
        const profileDropdown = document.getElementById('profile-dropdown-menu');
        if (profileDropdown && profileDropdown.classList.contains('user-dropdown__menu--open')) {
            profileDropdown.classList.remove('user-dropdown__menu--open');
            const trigger = document.getElementById('profile-dropdown-trigger');
            if (trigger) trigger.setAttribute('aria-expanded', 'false');
        }

        // Determine whether we are toggling mobile or desktop dropdown
        const isMobileTrigger = e && mobileNotifBell && (mobileNotifBell.contains(e.target) || mobileNotifBell === e.target);
        const targetDropdown = isMobileTrigger ? mobileNotifDropdown : notifDropdown;
        const siblingDropdown = isMobileTrigger ? notifDropdown : mobileNotifDropdown;
        const targetBell = isMobileTrigger ? mobileNotifBell : notifBell;
        const siblingBell = isMobileTrigger ? notifBell : mobileNotifBell;

        // Close sibling dropdown
        if (siblingDropdown) {
            siblingDropdown.classList.remove('notification-dropdown--open');
            if (siblingBell) siblingBell.setAttribute('aria-expanded', 'false');
        }

        if (targetDropdown) {
            const isOpen = targetDropdown.classList.contains('notification-dropdown--open');
            if (isOpen) {
                targetDropdown.classList.remove('notification-dropdown--open');
                if (targetBell) targetBell.setAttribute('aria-expanded', 'false');
            } else {
                targetDropdown.classList.add('notification-dropdown--open');
                if (targetBell) targetBell.setAttribute('aria-expanded', 'true');
                fetchNotifications();
            }
        }
    }

    if (notifBell) notifBell.addEventListener('click', toggleNotifDropdown);
    if (mobileNotifBell) mobileNotifBell.addEventListener('click', toggleNotifDropdown);

    // Close dropdowns on click outside
    document.addEventListener('click', function(e) {
        if (notifDropdown && notifDropdown.classList.contains('notification-dropdown--open')) {
            if (!notifDropdown.contains(e.target) && (!notifBell || !notifBell.contains(e.target))) {
                notifDropdown.classList.remove('notification-dropdown--open');
                if (notifBell) notifBell.setAttribute('aria-expanded', 'false');
            }
        }
        if (mobileNotifDropdown && mobileNotifDropdown.classList.contains('notification-dropdown--open')) {
            if (!mobileNotifDropdown.contains(e.target) && (!mobileNotifBell || !mobileNotifBell.contains(e.target))) {
                mobileNotifDropdown.classList.remove('notification-dropdown--open');
                if (mobileNotifBell) mobileNotifBell.setAttribute('aria-expanded', 'false');
            }
        }
    });

    // Format relative time (e.g. "2m ago")
    function formatRelativeTime(isoString) {
        try {
            const diffMs = Date.now() - new Date(isoString).getTime();
            const diffSec = Math.floor(diffMs / 1000);
            const diffMin = Math.floor(diffSec / 60);
            const diffHour = Math.floor(diffMin / 60);
            const diffDay = Math.floor(diffHour / 24);

            if (diffSec < 60) return 'Just now';
            if (diffMin < 60) return `${diffMin}m ago`;
            if (diffHour < 24) return `${diffHour}h ago`;
            return `${diffDay}d ago`;
        } catch (e) {
            return '';
        }
    }

    // Fetch and update unread count
    async function fetchUnreadCount() {
        if (!notifBell && !mobileNotifBell) return; // Anonymous user
        try {
            const response = await fetch('/api/notifications/unread-count', {
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            });
            if (response.ok) {
                const data = await response.json();
                updateBadge(data.count);
            }
        } catch (e) {
            console.error('Error fetching unread count:', e);
        }
    }

    function updateBadge(count) {
        if (count > 0) {
            if (notifBadge) {
                notifBadge.textContent = count;
                notifBadge.style.display = 'flex';
            }
            if (mobileNotifBadge) {
                mobileNotifBadge.textContent = count;
                mobileNotifBadge.style.display = 'flex';
            }
        } else {
            if (notifBadge) notifBadge.style.display = 'none';
            if (mobileNotifBadge) mobileNotifBadge.style.display = 'none';
        }
    }

    function setNotificationListMessage(listEl, message, modifier) {
        const state = document.createElement('div');
        state.className = `notification-dropdown__status${modifier ? ` notification-dropdown__status--${modifier}` : ''}`;
        state.textContent = message;
        listEl.replaceChildren(state);
    }

    // Fetch notification items
    async function fetchNotifications() {
        const lists = [notifList, mobileNotifList].filter(Boolean);
        if (lists.length === 0) return;
        
        lists.forEach(l => {
            setNotificationListMessage(l, 'Loading...');
        });

        try {
            const response = await fetch('/api/notifications', {
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            });
            if (response.ok) {
                const notifications = await response.json();
                renderNotifications(notifications);
            } else {
                lists.forEach(l => {
                    setNotificationListMessage(l, 'Failed to load notifications.', 'error');
                });
            }
        } catch (e) {
            console.error('Error fetching notifications:', e);
            lists.forEach(l => {
                setNotificationListMessage(l, 'A network error occurred.', 'error');
            });
        }
    }

    // Render notification rows
    function renderNotifications(notifications) {
        const lists = [
            { el: notifList, badge: notifBadge },
            { el: mobileNotifList, badge: mobileNotifBadge }
        ];

        lists.forEach(target => {
            const listEl = target.el;
            if (!listEl) return;
            listEl.innerHTML = '';

            if (notifications.length === 0) {
                listEl.innerHTML = `
                    <div class="notification-dropdown__empty">
                        <span class="material-symbols-outlined notification-dropdown__empty-icon" aria-hidden="true">notifications_off</span>
                        <span>No notifications yet.</span>
                    </div>
                `;
                return;
            }

            notifications.forEach(notif => {
                const row = document.createElement('a');
                // Validate notification link prefix (prevent protocol-relative links)
                const safeLink = (
                    typeof notif.link === 'string' &&
                    notif.link.startsWith('/') &&
                    !notif.link.startsWith('//')
                ) ? notif.link : '#';
                row.setAttribute('href', safeLink);
                row.className = `notification-row ${!notif.is_read ? 'notification-row--unread' : ''}`;
                row.dataset.id = notif.id;

                const avatar = document.createElement('span');
                avatar.className = 'chat-avatar chat-avatar--small';
                avatar.setAttribute('aria-hidden', 'true');
                const namePart = notif.title.replace('New message from ', '');
                avatar.textContent = namePart[0].toUpperCase();

                const contentDiv = document.createElement('div');
                contentDiv.className = 'notification-row__content';

                const titleSpan = document.createElement('span');
                titleSpan.className = 'notification-row__title';
                titleSpan.textContent = notif.title;

                const textSpan = document.createElement('span');
                textSpan.className = 'notification-row__text';
                textSpan.textContent = notif.content || '';

                const timeSpan = document.createElement('span');
                timeSpan.className = 'notification-row__time';
                timeSpan.textContent = formatRelativeTime(notif.created_at);

                contentDiv.appendChild(titleSpan);
                if (notif.content) contentDiv.appendChild(textSpan);
                contentDiv.appendChild(timeSpan);

                row.appendChild(avatar);
                row.appendChild(contentDiv);

                if (!notif.is_read) {
                    const dot = document.createElement('span');
                    dot.className = 'notification-row__dot';
                    row.appendChild(dot);
                }

                row.addEventListener('click', async () => {
                    if (!notif.is_read) {
                        const csrfToken = getCsrfToken();
                        
                        // Mark all notifications for the same link as read in DOM instantly
                        lists.forEach(otherList => {
                            if (otherList.el) {
                                otherList.el.querySelectorAll('.notification-row').forEach(sib => {
                                    if (sib.getAttribute('href') !== safeLink) return;
                                    if (sib.classList.contains('notification-row--unread')) {
                                        sib.classList.remove('notification-row--unread');
                                        const dot = sib.querySelector('.notification-row__dot');
                                        if (dot) dot.remove();
                                    }
                                });
                            }
                        });

                        // Send background DB update
                        fetch(`/api/notifications/${notif.id}/read`, {
                            method: 'POST',
                            headers: {
                                'X-CSRFToken': csrfToken,
                                'X-Requested-With': 'XMLHttpRequest'
                            },
                            keepalive: true
                        });
                    }
                });

                listEl.appendChild(row);
            });
        });
    }

    // Mark all as read
    const clearButtons = [clearAllBtn, mobileClearAllBtn].filter(Boolean);
    clearButtons.forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.preventDefault();
            e.stopPropagation();
            const csrfToken = getCsrfToken();
            try {
                const response = await fetch('/api/notifications/read-all', {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': csrfToken,
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                });
                if (response.ok) {
                    updateBadge(0);
                    fetchNotifications();
                }
            } catch (err) {
                console.error('Error marking all as read:', err);
            }
        });
    });

    // Listen to notifications-updated custom event from chat room
    window.addEventListener('notifications-updated', () => {
        fetchUnreadCount();
        const anyOpen = (notifDropdown && notifDropdown.classList.contains('notification-dropdown--open')) || 
                       (mobileNotifDropdown && mobileNotifDropdown.classList.contains('notification-dropdown--open'));
        if (anyOpen) {
            fetchNotifications();
        }
    });

    // Start global polling
    function startGlobalNotifPolling() {
        if (!notifBell && !mobileNotifBell) return;
        fetchUnreadCount();
        notifPollInterval = setInterval(fetchUnreadCount, 10000);
    }

    function stopGlobalNotifPolling() {
        if (notifPollInterval) {
            clearInterval(notifPollInterval);
            notifPollInterval = null;
        }
    }

    // Handle visibility change
    document.addEventListener('visibilitychange', () => {
        if (document.hidden) {
            stopGlobalNotifPolling();
        } else {
            startGlobalNotifPolling();
        }
    });

    // Initial poll
    if (notifBell || mobileNotifBell) {
        startGlobalNotifPolling();
    }

    // ── 7. Auto-dismiss Flash Alerts ──
    const flashAlerts = document.querySelectorAll('.flash-alert');
    flashAlerts.forEach(alert => {
        setTimeout(() => {
            alert.classList.add('flash-alert--fade-out');
            alert.addEventListener('animationend', function() {
                alert.remove();
            });
            // Fallback to remove in case animation is blocked
            setTimeout(() => {
                alert.remove();
            }, 500);
        }, 5000);
    });

    // ── 8. Dashboard Tab Switcher ──
    function switchTab(tab) {
        const wrapper = document.querySelector('.dashboard-wrapper');
        
        // Reset all tabs
        document.querySelectorAll('.dashboard-tab').forEach(btn => {
            btn.classList.remove('active-tab');
        });
        document.querySelectorAll('.dashboard-tab-content').forEach(content => {
            content.style.display = 'none';
        });
        
        // Hide all section headers by default
        document.querySelectorAll('.dashboard-section-header').forEach(header => {
            header.style.display = 'none';
        });
        
        // Activate current tab
        if (tab === 'overview') {
            if (wrapper) wrapper.classList.add('dashboard-wrapper--overview');
            const tabBtn = document.getElementById('tab-btn-overview');
            if (tabBtn) tabBtn.classList.add('active-tab');
            
            const contentClaims = document.getElementById('tab-content-claims');
            const contentListings = document.getElementById('tab-content-listings');
            const contentPurchases = document.getElementById('tab-content-purchases');
            if (contentClaims) contentClaims.style.display = 'flex';
            if (contentListings) contentListings.style.display = 'flex';
            if (contentPurchases) contentPurchases.style.display = 'flex';
            
            // Show all section headers
            document.querySelectorAll('.dashboard-section-header').forEach(header => {
                header.style.display = 'block';
            });
        } else {
            if (wrapper) wrapper.classList.remove('dashboard-wrapper--overview');
            const tabBtn = document.getElementById('tab-btn-' + tab);
            const tabContent = document.getElementById('tab-content-' + tab);
            if (tabBtn) tabBtn.classList.add('active-tab');
            if (tabContent) tabContent.style.display = 'flex';
        }
    }

    // Tab button click delegation (replace inline onclick)
    document.addEventListener('click', (e) => {
        const tabBtn = e.target.closest('[data-tab]');
        if (tabBtn) {
            e.preventDefault();
            switchTab(tabBtn.dataset.tab);
        }
    });

    // Auto-init dashboard if overview tab exists
    if (document.getElementById('tab-btn-overview')) {
        switchTab('overview');
    }

    // Confirm delete forms event delegation (replace inline onsubmit)
    document.addEventListener('submit', (e) => {
        if (e.target.classList.contains('confirm-delete-form')) {
            if (!confirm('Are you sure you want to delete this listing?')) {
                e.preventDefault();
            }
        }
    });

    // ── 9. Description Show More Toggle ──
    const descContent = document.getElementById('detail-desc-content');
    const descToggle = document.getElementById('desc-toggle');
    
    if (descContent && descToggle) {
        descContent.style.maxHeight = '150px';
        descContent.style.overflow = 'hidden';
        descContent.style.transition = 'max-height var(--duration-mid) var(--ease-out)';
        
        descToggle.addEventListener('click', function() {
            if (descContent.style.maxHeight === '150px') {
                descContent.style.maxHeight = descContent.scrollHeight + 'px';
                descToggle.textContent = 'Show less';
            } else {
                descContent.style.maxHeight = '150px';
                descToggle.textContent = 'Show more';
            }
        });
    }

    // ── 10. Celebratory count-up animation for KG Saved ──
    const valueEl = document.getElementById('celebration-kg-value');
    if (valueEl && valueEl.dataset.target) {
        const target = parseFloat(valueEl.dataset.target);
        const duration = 1200; // ms
        const start = 0;
        const startTime = performance.now();
        
        function animate(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            // easeOutExpo curve
            const ease = progress === 1 ? 1 : 1 - Math.pow(2, -10 * progress);
            const currentVal = start + (target - start) * ease;
            
            valueEl.textContent = `${currentVal.toFixed(1)} kg`;
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        }
        
        requestAnimationFrame(animate);
    }

    // Event delegation: Flash alert dismissal (replace inline onclick)
    document.addEventListener('click', (e) => {
        const dismissBtn = e.target.closest('.flash-alert__dismiss');
        if (dismissBtn) {
            dismissBtn.parentElement.remove();
        }
    });

    // Event delegation: Reload Page button
    document.addEventListener('click', (e) => {
        const reloadBtn = e.target.closest('[data-action="reload-page"]');
        if (reloadBtn) {
            e.preventDefault();
            window.location.reload();
        }
    });

    // Event delegation: Mobile back button (replace inline onclick)
    document.addEventListener('click', (e) => {
        const backBtn = e.target.closest('[data-action="back"]');
        if (backBtn) {
            e.preventDefault();
            if (document.referrer && document.referrer.includes(window.location.host)) {
                window.history.back();
            } else {
                window.location.href = '/';
            }
        }
    });

    // ── 4. Change Campus Functionality ──
    const changeCampusFooterLink = document.getElementById('change-campus-footer-link');
    const changeCampusDropdownLink = document.getElementById('change-campus-dropdown-link');
    
    function handleChangeCampus(e) {
        e.preventDefault();
        
        // Dynamically compute wildcard domain for clearing the cookie
        const hostParts = window.location.hostname.split('.');
        let domainAttr = "";
        let mainHost = window.location.host;
        
        if (hostParts.length >= 2) {
            const isLocalhostSubdomain = hostParts[hostParts.length - 1] === "localhost";
            const parentDomain = isLocalhostSubdomain ? "localhost" : hostParts.slice(-2).join('.');
            domainAttr = `; domain=.${parentDomain}`;
            
            // Calculate landing URL host (removing subdomain)
            mainHost = parentDomain;
            const port = window.location.port;
            if (port) {
                mainHost = `${mainHost}:${port}`;
            }
        }
        
        // Clear selected_uni cookie by expiring it in the past on wildcard domain
        document.cookie = `selected_uni=; path=/; expires=Thu, 01 Jan 1970 00:00:00 UTC${domainAttr};`;
        
        // Double-check: clear exact host cookie just in case it was written there
        document.cookie = `selected_uni=; path=/; expires=Thu, 01 Jan 1970 00:00:00 UTC;`;
        
        // Redirect back to main domain landing page with noredirect=true parameter
        window.location.href = `${window.location.protocol}//${mainHost}/?noredirect=true`;
    }
    
    if (changeCampusFooterLink) {
        changeCampusFooterLink.addEventListener('click', handleChangeCampus);
    }
    if (changeCampusDropdownLink) {
        changeCampusDropdownLink.addEventListener('click', handleChangeCampus);
    }
});
