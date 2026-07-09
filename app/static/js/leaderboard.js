document.addEventListener("DOMContentLoaded", () => {
    // ─── 1. Tab Switching & Sliding Indicator System ───
    const tabs = document.querySelectorAll("[data-tab-target]");
    const tabContents = document.querySelectorAll(".leaderboard-tab-content");
    const indicator = document.querySelector(".tab-indicator");

    function updateTabIndicator(activeBtn) {
        if (indicator && activeBtn) {
            const parent = activeBtn.parentElement;
            const activeRect = activeBtn.getBoundingClientRect();
            const parentRect = parent.getBoundingClientRect();
            
            // Calculate relative offset of tab inside its container
            const offsetLeft = activeRect.left - parentRect.left;
            
            indicator.style.width = `${activeRect.width}px`;
            indicator.style.transform = `translateX(${offsetLeft}px)`;
        }
    }

    function switchTab(targetId) {
        // Deactivate all tab buttons
        tabs.forEach(btn => {
            btn.classList.remove("active-tab");
        });

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
            // Trigger staggered animation on rows and progress bars
            animateRows(activeContent);
            animatePodiums(activeContent);
        }
    }

    // Trigger row animation and score progress bars dynamically
    function animateRows(container) {
        const rows = container.querySelectorAll(".rank-row");
        rows.forEach((row, index) => {
            row.classList.remove("animate-in");
            row.style.transitionDelay = `${index * 40}ms`;
            
            // Reset and animate associated progress bar background
            const progressBar = row.querySelector(".row-progress-bar");
            if (progressBar) {
                progressBar.style.width = "0";
                const targetWidth = progressBar.getAttribute("data-width") || "0";
                row.style.transitionEndCallback = () => {
                    progressBar.style.width = `${targetWidth}%`;
                };
                // Fallback to trigger progress bar expand after small delay
                setTimeout(() => {
                    progressBar.style.width = `${targetWidth}%`;
                }, index * 40 + 100);
            }

            void row.offsetWidth; // Force reflow
            row.classList.add("animate-in");
        });
    }

    // Trigger podium animations inside active container
    function animatePodiums(container) {
        const columns = container.querySelectorAll(".podium-member");
        columns.forEach((col, index) => {
            col.classList.remove("animate-in");
            col.style.transitionDelay = `${index * 120}ms`;
            void col.offsetWidth;
            col.classList.add("animate-in");
        });
    }

    // Bind tab button click listeners
    tabs.forEach(tab => {
        tab.addEventListener("click", (e) => {
            e.preventDefault();
            const targetId = tab.getAttribute("data-tab-target");
            history.pushState(null, null, `#${targetId}`);
            switchTab(targetId);
        });
    });

    // Recalibrate sliding indicator on window resizing
    window.addEventListener("resize", () => {
        const activeBtn = document.querySelector(".leaderboard-tab.active-tab");
        if (activeBtn) {
            updateTabIndicator(activeBtn);
        }
    });

    // ─── 2. Handle URL Hash on Load ───
    const currentHash = window.location.hash.substring(1);
    const validHashes = ["weekly", "seasonal", "universities"];
    
    // Slight delay on first load to ensure layout dimensions are fully calculated
    setTimeout(() => {
        if (currentHash && validHashes.includes(currentHash)) {
            switchTab(currentHash);
        } else {
            switchTab("weekly");
        }
    }, 50);

    window.addEventListener("hashchange", () => {
        const newHash = window.location.hash.substring(1);
        if (newHash && validHashes.includes(newHash)) {
            switchTab(newHash);
        }
    });

    // ─── 3. Global Podiums (Hall of Fame Page) ───
    const globalPodiums = document.querySelectorAll(".podium-member");
    // Only animate if they are not inside tab contents (which are handled by animatePodiums)
    globalPodiums.forEach((col, index) => {
        if (!col.closest(".leaderboard-tab-content")) {
            col.style.transitionDelay = `${index * 120}ms`;
            void col.offsetWidth;
            col.classList.add("animate-in");
        }
    });
});
