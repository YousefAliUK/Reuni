(function() {
    try {
        const savedTheme = localStorage.getItem('theme') || 'light';
        document.documentElement.setAttribute('data-theme', savedTheme);
    } catch (e) {
        // localStorage unavailable (restricted browser, incognito) — default to light
        document.documentElement.setAttribute('data-theme', 'light');
    }
})();
