(function() {
    try {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; theme=`);
        let savedTheme = parts.length === 2 ? parts.pop().split(';').shift() : null;
        
        if (!savedTheme) {
            savedTheme = localStorage.getItem('theme');
        }
        
        const theme = savedTheme === 'dark' || savedTheme === 'light' ? savedTheme : 'light';
        document.documentElement.setAttribute('data-theme', theme);
    } catch (e) {
        // Fallback to light theme on errors
        document.documentElement.setAttribute('data-theme', 'light');
    }
})();
