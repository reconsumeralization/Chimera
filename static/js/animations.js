// --- Animation Management ---

class AnimationManager {
    static init() {
        // Initialize animation observers
        this.initializeObservers();
        
        // Add animation classes to elements
        this.addAnimationClasses();
        
        // Initialize particle effects
        this.initializeParticles();

        // Matrix background effect for terminal windows
        this.initializeMatrixEffect();
    }

    static initializeObservers() {
        // Create intersection observer for fade-in animations
        const fadeObserver = new IntersectionObserver(
            (entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add('fade-in');
                        fadeObserver.unobserve(entry.target);
                    }
                });
            },
            {
                threshold: 0.1,
                rootMargin: '0px 0px -50px 0px'
            }
        );

        // Observe elements with fade-in class
        document.querySelectorAll('.animate-fade-in').forEach(element => {
            fadeObserver.observe(element);
        });

        // Create intersection observer for slide-in animations
        const slideObserver = new IntersectionObserver(
            (entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add('slide-in');
                        slideObserver.unobserve(entry.target);
                    }
                });
            },
            {
                threshold: 0.1,
                rootMargin: '0px 0px -50px 0px'
            }
        );

        // Observe elements with slide-in class
        document.querySelectorAll('.animate-slide-in').forEach(element => {
            slideObserver.observe(element);
        });
    }

    static addAnimationClasses() {
        // Add animation classes to elements based on their position
        document.querySelectorAll('.card, .section, .feature').forEach((element, index) => {
            element.classList.add('animate-fade-in');
            element.style.animationDelay = `${index * 0.1}s`;
        });

        // Add slide-in classes to elements that should slide in from sides
        document.querySelectorAll('.slide-from-left').forEach(element => {
            element.classList.add('animate-slide-in', 'slide-from-left');
        });

        document.querySelectorAll('.slide-from-right').forEach(element => {
            element.classList.add('animate-slide-in', 'slide-from-right');
        });

        // Add neon effect to headings and buttons if in dark mode
        if (document.documentElement.getAttribute('data-theme') === 'dark') {
            // Apply neon text to headings
            document.querySelectorAll('h1, h2, h3').forEach(heading => {
                heading.classList.add('neon-text');
            });
            
            // Apply neon borders to cards
            document.querySelectorAll('.card').forEach(card => {
                card.classList.add('border-glow');
            });
            
            // Apply neon underlines to nav links
            document.querySelectorAll('.nav-link').forEach(link => {
                link.classList.add('cyber-underline');
            });
            
            // Apply neon flicker to brand
            document.querySelectorAll('.navbar-brand').forEach(brand => {
                brand.classList.add('neon-flicker');
            });
        }
    }

    static initializeParticles() {
        // Create particle container if it doesn't exist
        if (!document.getElementById('particles-container')) {
            const container = document.createElement('div');
            container.id = 'particles-container';
            document.body.appendChild(container);
        }

        // Check if in dark mode
        const isDarkMode = document.documentElement.getAttribute('data-theme') === 'dark';

        // Initialize particles.js with matrix-inspired configuration
        particlesJS('particles-container', {
            particles: {
                number: {
                    value: isDarkMode ? 120 : 80,
                    density: {
                        enable: true,
                        value_area: 800
                    }
                },
                color: {
                    value: '#39ff14'
                },
                shape: {
                    type: 'char',
                    character: {
                        value: ['0', '1', '∞', '▀', '⚡', '✳', '⚒', '✧', '⟪', '⟫'],
                        font: 'Consolas',
                        style: '',
                        weight: 'normal'
                    }
                },
                opacity: {
                    value: isDarkMode ? 0.7 : 0.5,
                    random: true,
                    anim: {
                        enable: true,
                        speed: 1,
                        opacity_min: 0.1,
                        sync: false
                    }
                },
                size: {
                    value: 4,
                    random: true,
                    anim: {
                        enable: true,
                        speed: 2,
                        size_min: 1,
                        sync: false
                    }
                },
                line_linked: {
                    enable: isDarkMode,
                    distance: 150,
                    color: '#39ff14',
                    opacity: 0.2,
                    width: 1
                },
                move: {
                    enable: true,
                    speed: isDarkMode ? 2 : 1,
                    direction: 'none',
                    random: true,
                    straight: false,
                    out_mode: 'out',
                    bounce: false,
                    attract: {
                        enable: isDarkMode,
                        rotateX: 600,
                        rotateY: 1200
                    }
                }
            },
            interactivity: {
                detect_on: 'canvas',
                events: {
                    onhover: {
                        enable: true,
                        mode: isDarkMode ? 'bubble' : 'repulse'
                    },
                    onclick: {
                        enable: true,
                        mode: isDarkMode ? 'push' : 'push'
                    },
                    resize: true
                },
                modes: {
                    grab: {
                        distance: 150,
                        line_linked: {
                            opacity: 0.3
                        }
                    },
                    bubble: {
                        distance: 100,
                        size: 6,
                        duration: 2,
                        opacity: 0.8,
                        speed: 3
                    },
                    repulse: {
                        distance: 100,
                        duration: 0.4
                    },
                    push: {
                        particles_nb: 4
                    },
                    remove: {
                        particles_nb: 2
                    }
                }
            },
            retina_detect: true
        });
    }

    static initializeMatrixEffect() {
        // Apply matrix background effect to terminal elements
        document.querySelectorAll('.terminal, .terminal-output').forEach(element => {
            element.classList.add('matrix-bg');
        });
        
        // Add glitch effect to code elements when hovered
        document.querySelectorAll('code, pre').forEach(element => {
            element.setAttribute('data-text', element.textContent);
            element.classList.add('glitch');
        });
        
        // Apply typewriter effect to dashboard headings
        document.querySelectorAll('#dashboard h2').forEach(element => {
            element.classList.add('typewriter');
        });
    }

    static addLoadingAnimation(element) {
        element.classList.add('loading');
        const spinner = document.createElement('div');
        spinner.className = 'spinner';
        element.appendChild(spinner);
    }

    static removeLoadingAnimation(element) {
        element.classList.remove('loading');
        const spinner = element.querySelector('.spinner');
        if (spinner) {
            spinner.remove();
        }
    }

    static addSuccessAnimation(element) {
        element.classList.add('success');
        const checkmark = document.createElement('div');
        checkmark.className = 'checkmark';
        element.appendChild(checkmark);
        setTimeout(() => {
            element.classList.remove('success');
            checkmark.remove();
        }, 2000);
    }

    static addErrorAnimation(element) {
        element.classList.add('error');
        const xmark = document.createElement('div');
        xmark.className = 'xmark';
        element.appendChild(xmark);
        setTimeout(() => {
            element.classList.remove('error');
            xmark.remove();
        }, 2000);
    }

    static addPulseAnimation(element) {
        element.classList.add('pulse');
        setTimeout(() => {
            element.classList.remove('pulse');
        }, 1000);
    }

    static addShakeAnimation(element) {
        element.classList.add('shake');
        setTimeout(() => {
            element.classList.remove('shake');
        }, 500);
    }

    static addBounceAnimation(element) {
        element.classList.add('bounce');
        setTimeout(() => {
            element.classList.remove('bounce');
        }, 1000);
    }

    static addRotateAnimation(element) {
        element.classList.add('rotate');
        setTimeout(() => {
            element.classList.remove('rotate');
        }, 1000);
    }

    static addScaleAnimation(element) {
        element.classList.add('scale');
        setTimeout(() => {
            element.classList.remove('scale');
        }, 300);
    }

    static addFlipAnimation(element) {
        element.classList.add('flip');
        setTimeout(() => {
            element.classList.remove('flip');
        }, 1000);
    }

    static addGlitchAnimation(element) {
        if (!element.getAttribute('data-text')) {
            element.setAttribute('data-text', element.textContent);
        }
        element.classList.add('glitch');
        setTimeout(() => {
            element.classList.remove('glitch');
        }, 2000);
    }

    static addNeonPulseAnimation(element) {
        element.classList.add('neon-pulse');
        setTimeout(() => {
            element.classList.remove('neon-pulse');
        }, 2000);
    }
}

// --- Initialize Animation Manager ---
document.addEventListener('DOMContentLoaded', () => {
    AnimationManager.init();
    
    // Listen for theme changes to reinitialize particles
    document.addEventListener('themeChanged', () => {
        AnimationManager.initializeParticles();
        AnimationManager.addAnimationClasses();
        AnimationManager.initializeMatrixEffect();
    });
}); 