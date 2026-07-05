/**
 * Reuni Landing Page (landing.js)
 * Standalone landing script managing premium animations, theme toggles,
 * sticky-scroll phone walkthroughs, search filtering, and mobile menus.
 */

document.addEventListener("DOMContentLoaded", () => {
    // 1. FLOATING NAVBAR SCROLL SHADOW EFFECT
    const navbar = document.querySelector('.floating-navbar');
    if (navbar) {
        window.addEventListener('scroll', () => {
            if (window.scrollY > 60) {
                navbar.classList.add('scrolled');
            } else {
                navbar.classList.remove('scrolled');
            }
        }, { passive: true });
    }

    // 2. MOBILE DRAWER MENUS & NAV
    const menuToggle = document.getElementById('mobile-menu-toggle');
    const drawer = document.getElementById('mobile-nav-drawer');
    const drawerBackdrop = document.getElementById('mobile-drawer-backdrop');
    const drawerClose = document.getElementById('mobile-drawer-close');
    const drawerLinks = drawer ? drawer.querySelectorAll('.landing-drawer__link, .landing-drawer__btn-login, .landing-drawer__btn-cta') : [];

    function openDrawer() {
        if (menuToggle && drawer) {
            menuToggle.setAttribute('aria-expanded', 'true');
            drawer.classList.add('active');
            drawer.setAttribute('aria-hidden', 'false');
            document.body.style.overflow = 'hidden'; // Prevent background scrolling
        }
    }

    function closeDrawer() {
        if (menuToggle && drawer) {
            menuToggle.setAttribute('aria-expanded', 'false');
            drawer.classList.remove('active');
            drawer.setAttribute('aria-hidden', 'true');
            document.body.style.overflow = '';
        }
    }

    if (menuToggle) {
        menuToggle.addEventListener('click', () => {
            const expanded = menuToggle.getAttribute('aria-expanded') === 'true';
            if (expanded) {
                closeDrawer();
            } else {
                openDrawer();
            }
        });
    }

    if (drawerBackdrop) drawerBackdrop.addEventListener('click', closeDrawer);
    if (drawerClose) drawerClose.addEventListener('click', closeDrawer);
    drawerLinks.forEach(link => link.addEventListener('click', closeDrawer));

    // 3. THEME TOGGLE LOGIC
    const themeToggle = document.getElementById('landing-theme-toggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            const current = document.documentElement.getAttribute('data-theme') || 'light';
            const target = current === 'dark' ? 'light' : 'dark';
            document.documentElement.setAttribute('data-theme', target);
            try {
                localStorage.setItem('theme', target);
            } catch (e) {
                // localStorage unavailable (restricted browser/incognito)
            }
        });
    }

    // 4. METRICS COUNT-UP (LIVE PROOF)
    const counter = document.querySelector('.kg-counter');
    if (counter) {
        const target = parseFloat(counter.getAttribute('data-value'));
        const duration = 1400; // ms
        
        const countObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    countObserver.unobserve(entry.target);
                    
                    // Fallback if reduced-motion is requested
                    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
                        counter.innerHTML = target.toFixed(1) + '&nbsp;kg';
                        return;
                    }
                    
                    const start = performance.now();
                    const tick = (now) => {
                        const elapsed = Math.min((now - start) / duration, 1);
                        // easeOutExpo
                        const eased = elapsed === 1 ? 1 : 1 - Math.pow(2, -10 * elapsed);
                        const currentVal = target * eased;
                        counter.innerHTML = currentVal.toFixed(1) + '&nbsp;kg';
                        
                        if (elapsed < 1) {
                            requestAnimationFrame(tick);
                        } else {
                            counter.innerHTML = target.toFixed(1) + '&nbsp;kg';
                        }
                    };
                    requestAnimationFrame(tick);
                }
            });
        }, { threshold: 0.3 });
        
        countObserver.observe(counter);
    }

    // 5. STICKY-SCROLL WALKTHROUGH (DESKTOP)
    const steps = document.querySelectorAll('.step-text-block');
    const screens = document.querySelectorAll('.phone-screen');
    const tabBtns = document.querySelectorAll('.walkthrough-tab-btn');
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    if (steps.length > 0 && screens.length > 0 && !prefersReducedMotion) {
        const stepObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const stepIdx = parseInt(entry.target.getAttribute('data-step'), 10);
                    
                    // Sync active status for step text blocks
                    steps.forEach(s => s.classList.remove('active'));
                    entry.target.classList.add('active');
                    
                    // Sync active status for phone screens
                    screens.forEach(sc => sc.classList.remove('active'));
                    if (screens[stepIdx]) {
                        screens[stepIdx].classList.add('active');
                    }
                }
            });
        }, {
            rootMargin: '-30% 0px -30% 0px', // Triggers when step text block reaches center
            threshold: 0.1
        });

        steps.forEach(step => stepObserver.observe(step));
    }

    // 6. WALKTHROUGH STEP SWITCHER TABS (MOBILE)
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const stepIdx = parseInt(btn.id.replace('tab-step-', ''), 10);
            
            // Sync mobile tab button visual states
            tabBtns.forEach(b => {
                b.classList.remove('walkthrough-tab-btn--active');
                b.setAttribute('aria-selected', 'false');
            });
            btn.classList.add('walkthrough-tab-btn--active');
            btn.setAttribute('aria-selected', 'true');
            
            // Sync active screens inside mock phone
            screens.forEach((sc, idx) => {
                if (idx === stepIdx) {
                    sc.classList.add('active');
                } else {
                    sc.classList.remove('active');
                }
            });
        });
    });

    // 7. UNIVERSITY PICKER CARD SELECTOR COOKIE SETTINGS
    const uniCards = document.querySelectorAll('.uni-card');
    uniCards.forEach(card => {
        card.addEventListener('click', () => {
            const slug = card.getAttribute('data-slug');
            if (slug) {
                const hostParts = window.location.hostname.split('.');
                let domainAttr = "";
                if (hostParts.length >= 2) {
                    const baseParts = hostParts.slice(-2);
                    domainAttr = `; domain=.${baseParts.join('.')}`;
                }
                // Set selected_uni cookie on root domain for 1 year
                document.cookie = `selected_uni=${slug}; path=/; max-age=31536000; SameSite=Lax${domainAttr}`;
            }
        });
    });

    // 8. UNIVERSITY SEARCH FIELD FILTERING
    const searchInput = document.getElementById('landing-uni-search');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase().trim();
            uniCards.forEach(card => {
                const uniName = card.querySelector('.uni-card-name').textContent.toLowerCase();
                const uniDomain = card.getAttribute('data-domain').toLowerCase();
                if (uniName.includes(query) || uniDomain.includes(query)) {
                    card.style.display = 'flex';
                } else {
                    card.style.display = 'none';
                }
            });
        });
    }

    // 9. ENTRANCE ANIMATION FADE REVEALS
    const revealElements = document.querySelectorAll('.reveal');
    if (revealElements.length > 0) {
        const revealObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('revealed');
                    revealObserver.unobserve(entry.target);
                }
            });
        }, {
            rootMargin: '0px 0px -10% 0px',
            threshold: 0.05
        });

        revealElements.forEach(el => revealObserver.observe(el));
    }
});
