document.addEventListener("DOMContentLoaded", () => {
    // Toggle edit rows
    document.querySelectorAll('[data-action="edit-season"]').forEach(button => {
        button.addEventListener("click", () => {
            const seasonId = button.getAttribute("data-season-id");
            const displayRow = document.getElementById(`display-row-${seasonId}`);
            const editRow = document.getElementById(`edit-row-${seasonId}`);
            if (displayRow && editRow) {
                displayRow.style.display = "none";
                editRow.style.display = "table-row";
            }
        });
    });

    document.querySelectorAll('[data-action="cancel-edit-season"]').forEach(button => {
        button.addEventListener("click", () => {
            const seasonId = button.getAttribute("data-season-id");
            const displayRow = document.getElementById(`display-row-${seasonId}`);
            const editRow = document.getElementById(`edit-row-${seasonId}`);
            if (displayRow && editRow) {
                displayRow.style.display = "table-row";
                editRow.style.display = "none";
            }
        });
    });

    // Handle filter submission dynamically (Anti-Inline-Event-Handler rule)
    const filterSelect = document.getElementById("university_domain_filter");
    if (filterSelect) {
        filterSelect.addEventListener("change", () => {
            filterSelect.closest("form").submit();
        });
    }
});
