document.addEventListener("DOMContentLoaded", () => {
    // Determine page context based on route
    const isLeaderboardPage = !!document.getElementById("tab-btn-weekly");
    const defaultScope = isLeaderboardPage ? "weekly" : "seasonal";

    // ─── 1. Tab Switching & Sliding Indicator System ───
    const tabs = document.querySelectorAll("[data-tab-target]");
    const tabContents = document.querySelectorAll(".leaderboard-tab-content");
    const indicator = document.querySelector(".reuni-tab-indicator");
    const eyebrowElement = document.getElementById("leaderboard-eyebrow");
    const mainContainer = document.getElementById("leaderboard-main-container");

    function updateTabIndicator(activeBtn) {
        if (indicator && activeBtn) {
            const parent = activeBtn.parentElement;
            if (parent) {
                // Screen coordinates are immune to offsetParent race conditions
                const activeRect = activeBtn.getBoundingClientRect();
                const parentRect = parent.getBoundingClientRect();
                
                const offsetLeft = activeRect.left - parentRect.left + parent.scrollLeft;
                
                indicator.style.width = `${activeRect.width}px`;
                indicator.style.transform = `translateX(${offsetLeft}px)`;
            }
        }
    }

    function switchTab(targetId, updateHistory = false) {
        const targetButton = document.querySelector(`[data-tab-target="${targetId}"]`);
        const targetContent = document.getElementById(`tab-content-${targetId}`);
        if (tabs.length && (!targetButton || !targetContent)) {
            targetId = defaultScope;
        }

        // Deactivate all tab buttons
        tabs.forEach(btn => btn.classList.remove("active-tab"));

        // Hide all tab contents
        tabContents.forEach(content => {
            content.style.display = "none";
        });

        // Activate matching button
        const activeBtn = document.querySelector(`[data-tab-target="${targetId}"]`);
        if (activeBtn) {
            activeBtn.classList.add("active-tab");
            updateTabIndicator(activeBtn);
        }

        // Show matching content
        const activeContent = document.getElementById(`tab-content-${targetId}`);
        if (activeContent) {
            activeContent.style.display = "block";
            
            // Adjust container width layout class
            const newLayoutClass = activeContent.getAttribute("data-layout-class");
            if (mainContainer && newLayoutClass) {
                mainContainer.className = newLayoutClass;
            }

            // Update eyebrow title dynamically
            const newEyebrow = activeContent.getAttribute("data-eyebrow");
            if (eyebrowElement && newEyebrow) {
                eyebrowElement.textContent = newEyebrow;
            }

            // Trigger animations
            animateRows(activeContent);
            animatePodiums(activeContent);
        }

        // Update URL query parameters (preserve scroll position)
        if (updateHistory) {
            const url = new URL(window.location.href);
            url.searchParams.set("scope", targetId);
            window.history.pushState({ scope: targetId }, "", url);
        }
    }

    // Trigger row entrance animations
    function animateRows(container) {
        const rows = container.querySelectorAll(".rank-row");
        rows.forEach((row, index) => {
            row.classList.remove("animate-in");
            row.style.transitionDelay = `${index * 40}ms`;
            void row.offsetWidth; // Force reflow
            row.classList.add("animate-in");
        });
    }

    // Trigger podium entrance animations
    function animatePodiums(container) {
        const columns = container.querySelectorAll(".reuni-podium-step");
        columns.forEach((col, index) => {
            col.classList.remove("animate-in");
            let delay = 0;
            if (window.innerWidth < 1024) {
                // Mobile stagger: duo row (Rank 2 and 3) first, spotlight last
                if (col.classList.contains("reuni-podium-step--1")) delay = 120;
                else delay = 0;
            } else {
                // Desktop stagger: 3rd, then 2nd, then 1st
                if (col.classList.contains("reuni-podium-step--3")) delay = 0;
                else if (col.classList.contains("reuni-podium-step--2")) delay = 80;
                else if (col.classList.contains("reuni-podium-step--1")) delay = 160;
            }
            
            col.style.transitionDelay = `${delay}ms`;
            void col.offsetWidth;
            col.classList.add("animate-in");
        });
    }

    // Bind click events to tabs
    tabs.forEach(tab => {
        tab.addEventListener("click", (e) => {
            e.preventDefault();
            const targetId = tab.getAttribute("data-tab-target");
            switchTab(targetId, true);
        });
    });

    // Handle browser back/forward buttons
    window.addEventListener("popstate", (e) => {
        if (e.state && e.state.scope) {
            switchTab(e.state.scope, false);
        } else {
            const urlParams = new URLSearchParams(window.location.search);
            const scope = urlParams.get("scope") || defaultScope;
            switchTab(scope, false);
        }
    });

    // Recalculate tab indicator when tab buttons change size (e.g. CSS loads, fonts load, window resizes)
    if (tabs.length > 0) {
        const resizeObserver = new ResizeObserver(() => {
            const activeBtn = document.querySelector(".reuni-tab-btn.active-tab");
            if (activeBtn) {
                updateTabIndicator(activeBtn);
            }
        });
        tabs.forEach(tab => resizeObserver.observe(tab));
    }

    // Fallback: Recalculate on window load event when all external resources (CSS/Fonts) are fully loaded
    window.addEventListener("load", () => {
        const activeBtn = document.querySelector(".reuni-tab-btn.active-tab");
        if (activeBtn) {
            updateTabIndicator(activeBtn);
        }
    });

    // Parse URL on initial page load
    const urlParams = new URLSearchParams(window.location.search);
    const initialScope = urlParams.get("scope") || defaultScope;
    
    // Stagger to ensure initial elements and styling are compiled for offset math
    setTimeout(() => {
        switchTab(initialScope, false);
    }, 50);

    // ─── 2. Clientside Pagination System ───
    function setupPagination(scope) {
        const table = document.getElementById(`table-${scope}`);
        const paginationWrapper = document.getElementById(`pagination-wrapper-${scope}`);
        const showMoreBtn = document.getElementById(`show-more-btn-${scope}`);
        if (!table || !showMoreBtn) return;

        const rows = Array.from(table.querySelectorAll("tbody tr.rank-row"));

        // Hide rows with rank > 10 on load
        rows.forEach((row) => {
            const rank = parseInt(row.getAttribute("data-rank"), 10);
            if (rank > 10) {
                row.classList.add("sr-only");
            }
        });

        let currentVisibleLimit = 10;

        // Click to load next 20 rows
        showMoreBtn.addEventListener("click", () => {
            if (showMoreBtn.disabled) return;

            showMoreBtn.disabled = true;
            const originalHTML = showMoreBtn.innerHTML;
            showMoreBtn.innerHTML = `<span class="material-symbols-outlined reuni-spinner-spin" style="font-size: 16px; display: inline-block; vertical-align: middle; margin-right: 8px;">sync</span>Loading…`;

            setTimeout(() => {
                currentVisibleLimit += 20;
                let hasMoreHidden = false;

                rows.forEach((row) => {
                    const rank = parseInt(row.getAttribute("data-rank"), 10);
                    if (rank <= currentVisibleLimit) {
                        row.classList.remove("sr-only");
                    } else {
                        hasMoreHidden = true;
                    }
                });

                showMoreBtn.disabled = false;
                showMoreBtn.innerHTML = originalHTML;

                if (!hasMoreHidden && paginationWrapper) {
                    paginationWrapper.style.display = "none";
                }

                // Trigger animation on newly shown rows
                animateRows(table);
            }, 350);
        });
    }

    if (isLeaderboardPage) {
        setupPagination("weekly");
        setupPagination("seasonal");
    }

    // ─── 3. My-Rank Sticky Bar Visibility Observer ───
    function setupStickyRankBar(scope) {
        const stickyBar = document.getElementById(`my-rank-sticky-${scope}`);
        const userRow = document.getElementById(`current-user-row-${scope}`);
        const stickyBtn = document.getElementById(`sticky-bar-btn-${scope}`);

        if (!stickyBar) return;

        if (userRow) {
            // Setup intersection observer to hide bar when user's row is visible
            const observer = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        stickyBar.style.display = "none";
                    } else {
                        stickyBar.style.display = "block";
                    }
                });
            }, { threshold: 0.1 });

            observer.observe(userRow);

            // Bind scroll click
            stickyBtn.addEventListener("click", () => {
                userRow.scrollIntoView({ behavior: "smooth", block: "center" });
                
                // Trigger visual pulse highlight
                userRow.classList.add("row-highlight-pulse");
                setTimeout(() => {
                    userRow.classList.remove("row-highlight-pulse");
                }, 800);
            });
        } else {
            // User row not present in DOM list, show sticky bar permanently
            stickyBar.style.display = "block";
        }
    }

    if (isLeaderboardPage) {
        setupStickyRankBar("weekly");
        setupStickyRankBar("seasonal");
    }

    // ─── 4. AJAX Cross-University Term Selector ───
    const termSelect = document.getElementById("university-term-select");
    const universitiesTbody = document.getElementById("universities-list-tbody");
    const universityPodiumContainer = document.getElementById("university-podium-container");

    function escapeHtml(str) {
        if (!str) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    let currentController = null;

    if (termSelect && universitiesTbody) {
        termSelect.addEventListener("change", () => {
            const seasonId = termSelect.value;

            if (currentController) {
                currentController.abort();
            }
            currentController = new AbortController();
            const signal = currentController.signal;

            fetch(`/leaderboard/api/universities?season_id=${seasonId}`, { signal })
                .then(response => {
                    if (!response.ok) throw new Error("Network response was not ok");
                    return response.json();
                })
                .then(data => {
                    // 1. Update Podium Container
                    if (universityPodiumContainer) {
                        if (data.standings && data.standings.length >= 3) {
                            const first = data.standings[0];
                            const second = data.standings[1];
                            const third = data.standings[2];
                            
                            const getDisplayNameHTML = (entry) => {
                                const full = escapeHtml(entry.display_name);
                                const short = escapeHtml(entry.short_name || entry.display_name);
                                return `
                                    <span class="reuni-university-name--full">${full}</span>
                                    <span class="reuni-university-name--short" style="display: none;">${short}</span>
                                `;
                            };

                            const getLogoHTML = (entry) => {
                                const full = escapeHtml(entry.display_name);
                                const slug = escapeHtml(entry.slug);
                                const initials = escapeHtml(entry.initials);
                                if (entry.logo_status === "fetched") {
                                    return `<img src="/static/img/logos/${slug}.png" alt="${full}">`;
                                } else {
                                    return `<div class="reuni-university-logo-monogram" style="background-color: var(--color-primary-muted); color: var(--color-primary);">${initials}</div>`;
                                }
                            };
                            
                            universityPodiumContainer.innerHTML = `
                                <div class="reuni-podium">
                                    <!-- Rank 2 -->
                                    <div class="reuni-podium-step reuni-podium-step--2">
                                        <div class="reuni-podium-avatar-wrapper">
                                            <div class="reuni-podium-logo">
                                                ${getLogoHTML(second)}
                                            </div>
                                            <span class="reuni-podium-badge">2</span>
                                        </div>
                                        <div class="reuni-podium-name">${getDisplayNameHTML(second)}</div>
                                        <div class="reuni-podium-value">${second.total_kg.toFixed(1)} kg</div>
                                        <div class="reuni-podium-base"><span class="reuni-podium-base-num">2</span></div>
                                    </div>
                                    <!-- Rank 1 -->
                                    <div class="reuni-podium-step reuni-podium-step--1">
                                        <div class="reuni-podium-avatar-wrapper">
                                            <div class="reuni-podium-logo">
                                                ${getLogoHTML(first)}
                                            </div>
                                            <span class="reuni-podium-badge">
                                                <span class="material-symbols-outlined" style="font-size: 14px; line-height: 20px;">workspace_premium</span>
                                            </span>
                                        </div>
                                        <div class="reuni-podium-name">${getDisplayNameHTML(first)}</div>
                                        <div class="reuni-podium-value">${first.total_kg.toFixed(1)} kg</div>
                                        <div class="reuni-podium-base"><span class="material-symbols-outlined reuni-step-icon">eco</span></div>
                                    </div>
                                    <!-- Rank 3 -->
                                    <div class="reuni-podium-step reuni-podium-step--3">
                                        <div class="reuni-podium-avatar-wrapper">
                                            <div class="reuni-podium-logo">
                                                ${getLogoHTML(third)}
                                            </div>
                                            <span class="reuni-podium-badge">3</span>
                                        </div>
                                        <div class="reuni-podium-name">${getDisplayNameHTML(third)}</div>
                                        <div class="reuni-podium-value">${third.total_kg.toFixed(1)} kg</div>
                                        <div class="reuni-podium-base"><span class="reuni-podium-base-num">3</span></div>
                                    </div>
                                </div>
                            `;
                            
                            // Trigger entrance animations for the new podium steps
                            const newSteps = universityPodiumContainer.querySelectorAll(".reuni-podium-step");
                            newSteps.forEach((col) => {
                                col.classList.remove("animate-in");
                                let delay = 0;
                                if (window.innerWidth < 1024) {
                                    if (col.classList.contains("reuni-podium-step--1")) delay = 120;
                                    else delay = 0;
                                } else {
                                    if (col.classList.contains("reuni-podium-step--3")) delay = 0;
                                    else if (col.classList.contains("reuni-podium-step--2")) delay = 80;
                                    else if (col.classList.contains("reuni-podium-step--1")) delay = 160;
                                }
                                
                                col.style.transitionDelay = `${delay}ms`;
                                void col.offsetWidth;
                                col.classList.add("animate-in");
                            });
                        } else {
                            universityPodiumContainer.innerHTML = "";
                        }
                    }

                    // 2. Update Standings Table
                    const universitiesTable = document.getElementById("universities-table");
                    universitiesTbody.innerHTML = "";
                    if (data.standings && data.standings.length > 0) {
                        if (universitiesTable) {
                            if (data.standings.length <= 3) {
                                universitiesTable.style.display = "none";
                            } else {
                                universitiesTable.style.display = "table";
                            }
                        }
                        const startIdx = data.standings.length >= 3 ? 3 : 0;
                        data.standings.forEach((entry, idx) => {
                            const tr = document.createElement("tr");
                            tr.className = "reuni-university-row-tr";
                            if (idx < startIdx) {
                                tr.classList.add("sr-only");
                            }
                            
                            let logoHTML = "";
                            const full = escapeHtml(entry.display_name);
                            const slug = escapeHtml(entry.slug);
                            const initials = escapeHtml(entry.initials);
                            const short = escapeHtml(entry.short_name || entry.display_name);
                            if (entry.logo_status === "fetched") {
                                logoHTML = `<img src="/static/img/logos/${slug}.png" alt="${full}">`;
                            } else {
                                logoHTML = `<div class="reuni-university-logo-monogram" style="background-color: var(--color-primary-muted); color: var(--color-primary);">${initials}</div>`;
                            }
                            
                            tr.innerHTML = `
                                <td class="reuni-row-rank">${entry.rank}</td>
                                <td>
                                    <div class="reuni-university-logo-wrap">
                                        ${logoHTML}
                                    </div>
                                </td>
                                <td class="reuni-row-name-stack">
                                    <span class="reuni-university-name">
                                        <span class="reuni-university-name--full">${full}</span>
                                        <span class="reuni-university-name--short" style="display: none;">${short}</span>
                                    </span>
                                </td>
                                <td class="reuni-university-students">${entry.active_students} ${entry.active_students === 1 ? 'student' : 'students'}</td>
                                <td class="reuni-university-items">${entry.transaction_count} ${entry.transaction_count === 1 ? 'item' : 'items'}</td>
                                <td class="reuni-university-kg">${entry.total_kg.toFixed(1)} kg</td>
                            `;
                            universitiesTbody.appendChild(tr);
                        });
                    } else {
                        universitiesTbody.innerHTML = `
                            <tr>
                                <td colspan="6">
                                    <div class="leaderboard-empty-state">
                                        <span class="material-symbols-outlined leaderboard-empty-icon">explore</span>
                                        <h3 class="leaderboard-empty-title">No inter-university data</h3>
                                        <p class="leaderboard-empty-body">Standings will be compiled as soon as seasonal rankings compute.</p>
                                    </div>
                                </td>
                            </tr>
                        `;
                    }
                })
                .catch(err => {
                    if (err.name === 'AbortError') return;
                    console.error("Failed to load university standings:", err);
                });
        });
    }

    // ─── 5. Term Selector Bottom Sheet (Mobile) ───
    const selectContainer = document.querySelector(".reuni-term-select-container");
    const bottomSheet = document.getElementById("term-bottom-sheet");
    const closeSheetBtn = document.getElementById("close-term-sheet");
    const sheetRows = document.querySelectorAll(".reuni-bottom-sheet-row");
    const nativeSelect = document.getElementById("university-term-select");

    if (selectContainer && bottomSheet && nativeSelect) {
        // Tap to open bottom sheet on mobile
        selectContainer.addEventListener("click", (e) => {
            if (window.innerWidth < 1024) {
                e.preventDefault();
                openBottomSheet();
            }
        });

        function openBottomSheet() {
            bottomSheet.classList.add("reuni-bottom-sheet-overlay--open");
            document.body.style.overflow = "hidden"; // Prevent background scroll
            
            // Focus trap - focus the close button initially
            if (closeSheetBtn) {
                closeSheetBtn.focus();
            }
            
            // Add escape event
            document.addEventListener("keydown", handleEscapeKey);
            // Click outside to close
            bottomSheet.addEventListener("click", handleOutsideClick);
        }

        function closeBottomSheet() {
            bottomSheet.classList.remove("reuni-bottom-sheet-overlay--open");
            document.body.style.overflow = "";
            document.removeEventListener("keydown", handleEscapeKey);
            bottomSheet.removeEventListener("click", handleOutsideClick);
        }

        function handleEscapeKey(e) {
            if (e.key === "Escape") {
                closeBottomSheet();
            }
        }

        function handleOutsideClick(e) {
            if (e.target === bottomSheet) {
                closeBottomSheet();
            }
        }

        if (closeSheetBtn) {
            closeSheetBtn.addEventListener("click", closeBottomSheet);
        }

        // Tap row to select term
        sheetRows.forEach((row) => {
            row.addEventListener("click", () => {
                const termId = row.getAttribute("data-term-id");
                
                // Update active highlight
                sheetRows.forEach(r => r.classList.remove("reuni-bottom-sheet-row--selected"));
                row.classList.add("reuni-bottom-sheet-row--selected");
                
                // Update native select and trigger AJAX
                nativeSelect.value = termId;
                nativeSelect.dispatchEvent(new Event("change"));
                
                // Close bottom sheet
                closeBottomSheet();
            });
        });
    }
});
