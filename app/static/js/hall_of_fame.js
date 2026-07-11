document.addEventListener("DOMContentLoaded", () => {
    // ─── Weekly HOF Accordion Handler ───
    const HOFItems = document.querySelectorAll(".reuni-weekly-hof-item");
    HOFItems.forEach(item => {
        const btn = item.querySelector(".reuni-weekly-hof-expand-btn");
        const details = item.querySelector(".reuni-weekly-hof-details");
        if (btn && details) {
            btn.addEventListener("click", () => {
                const isExpanded = btn.getAttribute("aria-expanded") === "true";
                btn.setAttribute("aria-expanded", !isExpanded);
                if (isExpanded) {
                    details.style.display = "none";
                } else {
                    details.style.display = "block";
                }
            });
        }
    });
});
