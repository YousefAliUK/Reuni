document.addEventListener("DOMContentLoaded", () => {
    // ─── 1. Tab Switching System ───
    const tabs = document.querySelectorAll("[data-tab-target]");
    const tabContents = document.querySelectorAll(".leaderboard-tab-content");

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
        }

        // Show matching content
        const activeContent = document.getElementById(`tab-content-${targetId}`);
        if (activeContent) {
            activeContent.style.display = "block";
            // Trigger staggered animation on rows
            animateRows(activeContent);
        }
    }

    // Trigger row animation with staggered delays
    function animateRows(container) {
        const rows = container.querySelectorAll(".rank-row");
        rows.forEach((row, index) => {
            row.classList.remove("animate-in");
            // Set transitions delay dynamically
            row.style.transitionDelay = `${index * 40}ms`;
            // Trigger reflow to restart transition
            void row.offsetWidth;
            row.classList.add("animate-in");
        });
    }

    // Bind tab button click listeners
    tabs.forEach(tab => {
        tab.addEventListener("click", (e) => {
            e.preventDefault();
            const targetId = tab.getAttribute("data-tab-target");
            // Update URL hash without jumping the page
            history.pushState(null, null, `#${targetId}`);
            switchTab(targetId);
        });
    });

    // ─── 2. Handle URL Hash on Load ───
    const currentHash = window.location.hash.substring(1); // strip '#'
    const validHashes = ["weekly", "seasonal", "universities"];
    if (currentHash && validHashes.includes(currentHash)) {
        switchTab(currentHash);
    } else {
        // Default to weekly
        switchTab("weekly");
    }

    // Handle back/forward browser navigation
    window.addEventListener("hashchange", () => {
        const newHash = window.location.hash.substring(1);
        if (newHash && validHashes.includes(newHash)) {
            switchTab(newHash);
        }
    });

    // ─── 3. Podium Animations (Hall of Fame) ───
    const podiums = document.querySelectorAll(".podium-column");
    if (podiums.length > 0) {
        // Stagger animations on podium entries
        podiums.forEach((col, index) => {
            col.style.transitionDelay = `${index * 150}ms`;
            // Force layout reflow
            void col.offsetWidth;
            col.classList.add("animate-in");
        });
    }
});
