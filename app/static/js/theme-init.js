(function() {
    try {
        const savedTheme = localStorage.getItem('theme');
        const theme = savedTheme === 'dark' || savedTheme === 'light' ? savedTheme : 'light';
        document.documentElement.setAttribute('data-theme', theme);
    } catch (e) {
        // localStorage unavailable (restricted browser, incognito) — default to light
        document.documentElement.setAttribute('data-theme', 'light');
    }
})();
