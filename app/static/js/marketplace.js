/**
 * Reuni — Marketplace Filtering & Live AJAX Updates (CSP-safe)
 */

document.addEventListener('DOMContentLoaded', function () {
    // Desktop Price Type Toggle interaction
    const priceBtns = document.querySelectorAll('.price-toggle-btn');
    const priceInput = document.getElementById('price-type-input');
    const rangeInputs = document.querySelector('.price-range-inputs');
    const mobilePriceRange = document.getElementById('mobile-price-range-group');
    const filterForm = document.querySelector('.filter-control-bar__form');
    const sectionWrapper = document.getElementById('listings-section-wrapper');

    let filterRequestController = null;
    let filterRequestId = 0;

    // AJAX live update function
    function fetchFilteredItems(url, options = {}) {
        const { updateHistory = true } = options;
        const requestId = ++filterRequestId;
        if (filterRequestController) {
            filterRequestController.abort();
        }
        filterRequestController = new AbortController();

        const grid = document.getElementById('marketplace-grid');
        if (grid) grid.style.opacity = '0.5';

        fetch(url, { signal: filterRequestController.signal })
            .then(res => {
                if (!res.ok) {
                    throw new Error(`Filter request failed with HTTP ${res.status}`);
                }
                return res.text();
            })
            .then(html => {
                if (requestId !== filterRequestId) return;

                const parser = new DOMParser();
                const doc = parser.parseFromString(html, 'text/html');

                // 1. Swap listings section
                const newSection = doc.getElementById('listings-section-wrapper');
                if (!newSection || !sectionWrapper) {
                    throw new Error('Filter response missing listings section');
                }
                sectionWrapper.innerHTML = newSection.innerHTML;

                // 2. Sync category strip
                const newStrip = doc.querySelector('.category-strip');
                const currentStrip = document.querySelector('.category-strip');
                if (newStrip && currentStrip) {
                    currentStrip.innerHTML = newStrip.innerHTML;
                }

                // 3. Sync desktop form elements
                if (filterForm) {
                    const newForm = doc.querySelector('.filter-control-bar__form');
                    if (newForm) {
                        // Sync selects (condition, sort)
                        filterForm.querySelectorAll('select').forEach(select => {
                            const newSelect = newForm.querySelector(`#${select.id}`);
                            if (newSelect) select.value = newSelect.value;
                        });
                        // Sync hidden inputs
                        const catInput = filterForm.querySelector('input[name="category"]');
                        const newCatInput = newForm.querySelector('input[name="category"]');
                        if (catInput && newCatInput) catInput.value = newCatInput.value;

                        const ptInput = document.getElementById('price-type-input');
                        const newPtInput = doc.getElementById('price-type-input');
                        if (ptInput && newPtInput) {
                            ptInput.value = newPtInput.value;
                            // Sync active state of price buttons
                            priceBtns.forEach(b => {
                                b.classList.remove('active');
                                if (b.getAttribute('data-value') === ptInput.value) {
                                    b.classList.add('active');
                                }
                            });
                            // Toggle price inputs display
                            if (ptInput.value === 'paid') {
                                if (rangeInputs) rangeInputs.style.display = 'flex';
                            } else {
                                if (rangeInputs) rangeInputs.style.display = 'none';
                            }
                        }
                        // Sync price inputs (min_price, max_price)
                        filterForm.querySelectorAll('input[type="number"]').forEach(input => {
                            const newInput = newForm.querySelector(`input[name="${input.name}"]`);
                            if (newInput) input.value = newInput.value;
                        });
                    }
                }

                // 4. Sync mobile form elements
                const mobileForm = document.getElementById('mobile-filter-form');
                if (mobileForm) {
                    const newMobileForm = doc.getElementById('mobile-filter-form');
                    if (newMobileForm) {
                        // Sync price type radio buttons
                        const checkedRadio = newMobileForm.querySelector('input[name="price_type"]:checked');
                        if (checkedRadio) {
                            const localRadio = mobileForm.querySelector(`input[name="price_type"][value="${checkedRadio.value}"]`);
                            if (localRadio) localRadio.checked = true;
                        }
                        // Toggle mobile price range group display
                        const newMobilePriceRange = doc.getElementById('mobile-price-range-group');
                        if (newMobilePriceRange && mobilePriceRange) {
                            mobilePriceRange.style.display = newMobilePriceRange.style.display;
                        }
                        // Sync min_price, max_price
                        mobileForm.querySelectorAll('input[type="number"]').forEach(input => {
                            const newInput = newMobileForm.querySelector(`input[name="${input.name}"]`);
                            if (newInput) input.value = newInput.value;
                        });
                        // Sync hidden category
                        const mCatInput = mobileForm.querySelector('input[name="category"]');
                        const newMCatInput = newMobileForm.querySelector('input[name="category"]');
                        if (mCatInput && newMCatInput) mCatInput.value = newMCatInput.value;
                    }
                }

                // 5. Sync results count
                const newCounts = doc.querySelectorAll('.filter-results-count');
                const currentCounts = document.querySelectorAll('.filter-results-count');
                currentCounts.forEach((el, idx) => {
                    if (newCounts[idx]) el.innerHTML = newCounts[idx].innerHTML;
                });

                // 6. Sync desktop clear button
                const desktopGroup = document.querySelector('.filter-control-bar__desktop');
                const currentClear = document.querySelector('.filter-clear-btn');
                const newClear = doc.querySelector('.filter-clear-btn');
                if (currentClear && !newClear) {
                    currentClear.remove();
                } else if (!currentClear && newClear) {
                    const countSpan = desktopGroup?.querySelector('.filter-results-count');
                    if (countSpan) countSpan.insertAdjacentHTML('beforebegin', newClear.outerHTML);
                } else if (currentClear && newClear) {
                    currentClear.outerHTML = newClear.outerHTML;
                }

                // 7. Sync mobile apply button results count
                const applyBtn = document.getElementById('mobile-filter-apply-btn');
                const countEl = doc.querySelector('.filter-results-count');
                if (countEl && applyBtn) {
                    const countText = countEl.textContent.trim().replace(/\D+/g, '');
                    applyBtn.textContent = `Apply — ${countText} results`;
                }

                // 8. Update browser history URL
                if (updateHistory) {
                    history.pushState(null, '', url);
                }
            })
            .catch(err => {
                if (err.name === 'AbortError') return;
                // Network failure — restore opacity
                const grid = document.getElementById('marketplace-grid');
                if (grid) grid.style.opacity = '1';
                console.warn('[Reuni] AJAX filter failed, falling back to full reload:', err);
                window.location.href = url;
            });
    }

    priceBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const val = this.getAttribute('data-value');
            if (priceInput) priceInput.value = val;
            priceBtns.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            
            if (val === 'paid') {
                if (rangeInputs) rangeInputs.style.display = 'flex';
            } else {
                if (rangeInputs) {
                    rangeInputs.style.display = 'none';
                    rangeInputs.querySelectorAll('input').forEach(input => input.value = '');
                }
                if (filterForm) {
                    const formData = new FormData(filterForm);
                    const params = new URLSearchParams(formData).toString();
                    fetchFilteredItems('/?' + params);
                }
            }
        });
    });

    // Intercept form submissions & select changes
    if (filterForm) {
        filterForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(filterForm);
            const params = new URLSearchParams(formData).toString();
            fetchFilteredItems('/?' + params);
        });

        filterForm.querySelectorAll('select').forEach(select => {
            select.addEventListener('change', function(e) {
                e.preventDefault();
                const formData = new FormData(filterForm);
                const params = new URLSearchParams(formData).toString();
                fetchFilteredItems('/?' + params);
            });
        });
    }

    // Intercept Category Chip clicks, Pagination Link clicks, and Clear clicks
    document.addEventListener('click', function(e) {
        const chip = e.target.closest('.category-chip');
        if (chip) {
            e.preventDefault();
            const url = chip.getAttribute('href');
            if (url) {
                document.querySelectorAll('.category-chip').forEach(c => c.classList.remove('category-chip--active'));
                chip.classList.add('category-chip--active');
                const urlParams = new URLSearchParams(url.split('?')[1]);
                const catInput = filterForm?.querySelector('input[name="category"]');
                if (catInput) catInput.value = urlParams.get('category') || '';
                fetchFilteredItems(url);
            }
            return;
        }

        const pagLink = e.target.closest('.pagination__link');
        if (pagLink) {
            e.preventDefault();
            const url = pagLink.getAttribute('href');
            if (url) fetchFilteredItems(url);
            return;
        }

        const clearBtn = e.target.closest('.filter-clear-btn');
        if (clearBtn) {
            e.preventDefault();
            const url = clearBtn.getAttribute('href');
            if (url && filterForm) {
                filterForm.querySelectorAll('input:not([type="hidden"])').forEach(input => input.value = '');
                filterForm.querySelectorAll('select').forEach(select => select.selectedIndex = 0);
                const catInput = filterForm.querySelector('input[name="category"]');
                if (catInput) catInput.value = '';
                const priceTypeInput = document.getElementById('price-type-input');
                if (priceTypeInput) priceTypeInput.value = 'all';
                priceBtns.forEach(b => {
                    b.classList.remove('active');
                    if (b.getAttribute('data-value') === 'all') b.classList.add('active');
                });
                if (rangeInputs) rangeInputs.style.display = 'none';
                document.querySelectorAll('.category-chip').forEach(c => c.classList.remove('category-chip--active'));
                const allCatChip = document.querySelector('.category-chip:first-child');
                if (allCatChip) allCatChip.classList.add('category-chip--active');
                fetchFilteredItems(url);
            }
        }
    });

    // Mobile Filter Drawer Logic
    const filterBtn = document.getElementById('mobile-filter-drawer-open');
    const filterDrawer = document.getElementById('mobile-filter-drawer');
    const filterBackdrop = document.getElementById('mobile-filter-drawer-backdrop');
    const filterClose = document.getElementById('mobile-filter-drawer-close');
    
    function openFilterDrawer() {
        if (filterDrawer && filterBackdrop) {
            filterBackdrop.classList.add('mobile-drawer-backdrop--open');
            filterDrawer.classList.add('mobile-drawer--open');
            filterDrawer.style.transform = 'translateY(0)';
        }
    }
    
    function closeFilterDrawer() {
        if (filterDrawer && filterBackdrop) {
            filterBackdrop.classList.remove('mobile-drawer-backdrop--open');
            filterDrawer.classList.remove('mobile-drawer--open');
            filterDrawer.style.transform = 'translateY(100%)';
        }
    }
    
    if (filterBtn) filterBtn.addEventListener('click', openFilterDrawer);
    if (filterClose) filterClose.addEventListener('click', closeFilterDrawer);
    if (filterBackdrop) filterBackdrop.addEventListener('click', closeFilterDrawer);

    // Handle price type radio changes in mobile form
    const mobileForm = document.getElementById('mobile-filter-form');
    const applyBtn = document.getElementById('mobile-filter-apply-btn');
    
    if (mobileForm) {
        mobileForm.querySelectorAll('input[name="price_type"]').forEach(radio => {
            radio.addEventListener('change', function() {
                if (this.value === 'paid') {
                    if (mobilePriceRange) mobilePriceRange.style.display = 'block';
                } else {
                    if (mobilePriceRange) {
                        mobilePriceRange.style.display = 'none';
                        mobilePriceRange.querySelectorAll('input').forEach(input => input.value = '');
                    }
                }
            });
        });

        // Dynamic results counter update
        mobileForm.addEventListener('change', function() {
            const formData = new FormData(mobileForm);
            const params = new URLSearchParams(formData).toString();
            fetch('/?' + params)
                .then(res => res.text())
                .then(html => {
                    const parser = new DOMParser();
                    const doc = parser.parseFromString(html, 'text/html');
                    const countEl = doc.querySelector('.filter-results-count');
                    if (countEl && applyBtn) {
                        const countText = countEl.textContent.trim().replace(/\D+/g, '');
                        applyBtn.textContent = `Apply — ${countText} results`;
                    }
                })
                .catch(() => {});
        });

        // Intercept mobile form submission
        mobileForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(mobileForm);
            const params = new URLSearchParams(formData).toString();
            fetchFilteredItems('/?' + params);
            closeFilterDrawer();
        });
    }

    // Dynamic count-up animation for hero stats
    const statValues = document.querySelectorAll('.marketplace-hero__stat-value');
    statValues.forEach(el => {
        const target = parseFloat(el.getAttribute('data-target') || '0');
        if (isNaN(target) || target <= 0) return;
        
        const isFloat = el.textContent.includes('.');
        const start = 0;
        const duration = 1200; // 1.2 seconds smooth ease-out
        const startTime = performance.now();
        
        function updateCount(timestamp) {
            const elapsed = timestamp - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const easeProgress = 1 - Math.pow(1 - progress, 3);
            const current = start + easeProgress * target;
            
            el.textContent = isFloat ? current.toFixed(1) : Math.floor(current);
            
            if (progress < 1) {
                requestAnimationFrame(updateCount);
            } else {
                el.textContent = isFloat ? target.toFixed(1) : Math.floor(target);
            }
        }
        requestAnimationFrame(updateCount);
    });

    window.addEventListener('popstate', function () {
        fetchFilteredItems(window.location.href, { updateHistory: false });
    });
});
