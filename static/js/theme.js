// --- Theme Management ---

class ThemeManager {
    static THEME_KEY = 'preferred-theme';
    static DARK_THEME = 'dark';
    static LIGHT_THEME = 'light';

    static init() {
        // Load saved theme or default to dark
        const savedTheme = localStorage.getItem(this.THEME_KEY);
        if (savedTheme) {
            this.setTheme(savedTheme);
        } else {
            // Default to dark theme instead of system preference
            this.setTheme(this.DARK_THEME);
        }

        // Add event listener for theme toggle button
        const themeToggle = document.getElementById('theme-toggle');
        if (themeToggle) {
            themeToggle.addEventListener('click', () => this.toggleTheme());
        }

        // Listen for system theme changes
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
            if (!localStorage.getItem(this.THEME_KEY)) {
                this.setSystemTheme();
            }
        });
    }

    static setTheme(theme) {
        const previousTheme = document.documentElement.getAttribute('data-theme');
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem(this.THEME_KEY, theme);
        this.updateThemeToggleButton(theme);
        
        // Dispatch custom event for theme change
        if (previousTheme !== theme) {
            document.dispatchEvent(new CustomEvent('themeChanged', { 
                detail: { 
                    oldTheme: previousTheme, 
                    newTheme: theme
                } 
            }));
        }
        
        // Apply neon flicker effect to navbar brand when in dark mode
        const navbarBrand = document.querySelector('.navbar-brand');
        if (navbarBrand) {
            if (theme === this.DARK_THEME) {
                navbarBrand.classList.add('neon-flicker');
                document.body.classList.add('dark-mode-active');
            } else {
                navbarBrand.classList.remove('neon-flicker');
                document.body.classList.remove('dark-mode-active');
            }
        }
    }

    static setSystemTheme() {
        const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        this.setTheme(isDark ? this.DARK_THEME : this.LIGHT_THEME);
    }

    static toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === this.DARK_THEME ? this.LIGHT_THEME : this.DARK_THEME;
        
        // Add transition class for smooth theme switching
        document.body.classList.add('theme-transition');
        
        // Set the new theme
        this.setTheme(newTheme);
        
        // Remove transition class after animation completes
        setTimeout(() => {
            document.body.classList.remove('theme-transition');
        }, 1000);
    }

    static updateThemeToggleButton(theme) {
        const themeToggle = document.getElementById('theme-toggle');
        if (themeToggle) {
            const icon = themeToggle.querySelector('i');
            if (icon) {
                icon.className = theme === this.DARK_THEME ? 'bi bi-sun' : 'bi bi-moon';
            }
            themeToggle.setAttribute('data-tooltip', `Switch to ${theme === this.DARK_THEME ? 'light' : 'dark'} theme`);
            
            // Add neon effect to the toggle button in dark mode
            if (theme === this.DARK_THEME) {
                themeToggle.classList.add('neon-border');
            } else {
                themeToggle.classList.remove('neon-border');
            }
        }
    }
}

// --- Initialize Theme Manager ---
document.addEventListener('DOMContentLoaded', () => {
    ThemeManager.init();
}); 