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
            // Stagger 3rd, then 2nd, then 1st
            let delay = 0;
            if (col.classList.contains("reuni-podium-step--3")) delay = 0;
            else if (col.classList.contains("reuni-podium-step--2")) delay = 80;
            else if (col.classList.contains("reuni-podium-step--1")) delay = 160;
            
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

        const rows = table.querySelectorAll("tbody tr.rank-row");
        const limit = 50;

        // Hide rows beyond limit on load
        rows.forEach((row, index) => {
            if (index >= limit) {
                row.classList.add("sr-only");
            }
        });

        // Click to load all remaining rows
        showMoreBtn.addEventListener("click", () => {
            rows.forEach(row => row.classList.remove("sr-only"));
            if (paginationWrapper) {
                paginationWrapper.style.display = "none";
            }
            // Trigger animation on newly shown rows
            animateRows(table);
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

    if (termSelect && universitiesTbody) {
        termSelect.addEventListener("change", () => {
            const seasonId = termSelect.value;
            fetch(`/leaderboard/api/universities?season_id=${seasonId}`)
                .then(response => {
                    if (!response.ok) throw new Error("Network response was not ok");
                    return response.json();
                })
                .then(data => {
                    universitiesTbody.innerHTML = "";
                    if (data.standings && data.standings.length > 0) {
                        data.standings.forEach(entry => {
                            const tr = document.createElement("tr");
                            tr.className = "reuni-university-row-tr";
                            
                            let logoHTML = "";
                            if (entry.logo_status === "fetched") {
                                logoHTML = `<img src="/static/img/logos/${entry.slug}.png" alt="${entry.display_name}">`;
                            } else {
                                logoHTML = `<div class="reuni-university-logo-monogram" style="background-color: ${entry.brand_color}; color: ${entry.brand_text_color};">${entry.initials}</div>`;
                            }
                            
                            tr.innerHTML = `
                                <td class="reuni-row-rank">${entry.rank}</td>
                                <td>
                                    <div class="reuni-university-logo-wrap">
                                        ${logoHTML}
                                    </div>
                                </td>
                                <td class="reuni-row-name-stack">
                                    <span class="reuni-university-name">${entry.display_name}</span>
                                </td>
                                <td class="reuni-university-students">${entry.active_students} students</td>
                                <td class="reuni-university-items">${entry.transaction_count} items</td>
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
                    console.error("Failed to load university standings:", err);
                });
        });
    }
});
