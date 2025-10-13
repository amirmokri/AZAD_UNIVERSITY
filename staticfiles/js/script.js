/**
 * Main JavaScript file for University Hub
 * 
 * Features:
 * - Hamburger menu toggle for mobile navigation
 * - Smooth scrolling
 * - Animation triggers on scroll
 * - Enhanced user interactions
 */

// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    
    /**
     * Hamburger Menu Toggle
     * Handles mobile navigation menu open/close
     */
    const hamburger = document.getElementById('hamburger');
    const navMenu = document.getElementById('navMenu');
    
    if (hamburger && navMenu) {
        hamburger.addEventListener('click', function() {
            // Toggle active class on hamburger button
            this.classList.toggle('active');
            
            // Toggle active class on navigation menu
            navMenu.classList.toggle('active');
        });
        
        // Close menu when clicking on a nav link (mobile)
        const navLinks = document.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
            link.addEventListener('click', function() {
                hamburger.classList.remove('active');
                navMenu.classList.remove('active');
            });
        });
        
        // Close menu when clicking outside
        document.addEventListener('click', function(event) {
            const isClickInsideNav = navMenu.contains(event.target);
            const isClickOnHamburger = hamburger.contains(event.target);
            
            if (!isClickInsideNav && !isClickOnHamburger && navMenu.classList.contains('active')) {
                hamburger.classList.remove('active');
                navMenu.classList.remove('active');
            }
        });
    }
    
    
    /**
     * Smooth Scroll for Anchor Links
     */
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            if (href !== '#' && document.querySelector(href)) {
                e.preventDefault();
                const target = document.querySelector(href);
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    
    /**
     * Intersection Observer for Scroll Animations
     * Adds animation classes when elements come into view
     */
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                // Optionally stop observing after animation
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);
    
    // Observe all cards and animated elements
    const animatedElements = document.querySelectorAll(
        '.info-card, .day-card, .time-card, .room-card, .floor-container'
    );
    
    animatedElements.forEach(element => {
        observer.observe(element);
    });
    
    
    /**
     * Add hover effect sound/haptic feedback (optional)
     * Can be enabled for enhanced UX
     */
    const interactiveCards = document.querySelectorAll(
        '.day-card, .time-card, .info-card'
    );
    
    interactiveCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            // Optional: Add haptic feedback on mobile
            if (navigator.vibrate) {
                navigator.vibrate(10);
            }
        });
    });
    
    
    /**
     * Loading Animation
     * Show page content with fade-in effect
     */
    window.addEventListener('load', function() {
        document.body.classList.add('loaded');
    });
    
    
    /**
     * Handle Window Resize
     * Reset mobile menu on desktop view
     */
    let resizeTimer;
    window.addEventListener('resize', function() {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(function() {
            if (window.innerWidth > 768) {
                if (navMenu) {
                    navMenu.classList.remove('active');
                }
                if (hamburger) {
                    hamburger.classList.remove('active');
                }
            }
        }, 250);
    });
    
    
    /**
     * Add Active State to Current Page in Navigation
     */
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        const linkPath = new URL(link.href).pathname;
        if (linkPath === currentPath || 
            (currentPath.includes('/class-affairs/') && link.href.includes('class-affairs'))) {
            link.style.backgroundColor = 'rgba(255, 255, 255, 0.15)';
        }
    });
    
    
    /**
     * Print Page Functionality (Optional)
     * Can be triggered by a button
     */
    window.printPage = function() {
        window.print();
    };
    
    
    /**
     * Copy to Clipboard Functionality
     * Useful for sharing schedule information
     */
    window.copyToClipboard = function(text) {
        if (navigator.clipboard) {
            navigator.clipboard.writeText(text).then(function() {
                alert('کپی شد!');
            }).catch(function(err) {
                console.error('خطا در کپی کردن:', err);
            });
        } else {
            // Fallback for older browsers
            const textArea = document.createElement('textarea');
            textArea.value = text;
            document.body.appendChild(textArea);
            textArea.select();
            try {
                document.execCommand('copy');
                alert('کپی شد!');
            } catch (err) {
                console.error('خطا در کپی کردن:', err);
            }
            document.body.removeChild(textArea);
        }
    };
    
    
    /**
     * Form Validation (if forms are added in future)
     */
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const requiredFields = form.querySelectorAll('[required]');
            let isValid = true;
            
            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    isValid = false;
                    field.classList.add('error');
                } else {
                    field.classList.remove('error');
                }
            });
            
            if (!isValid) {
                e.preventDefault();
                alert('لطفاً تمام فیلدهای الزامی را پر کنید.');
            }
        });
    });
    
    
    /**
     * Keyboard Navigation Enhancement
     * Improve accessibility with keyboard shortcuts
     */
    document.addEventListener('keydown', function(e) {
        // Press 'Escape' to close mobile menu
        if (e.key === 'Escape') {
            if (navMenu && navMenu.classList.contains('active')) {
                navMenu.classList.remove('active');
                if (hamburger) {
                    hamburger.classList.remove('active');
                }
            }
        }
        
        // Press 'H' to go to home (with Ctrl/Cmd)
        if ((e.ctrlKey || e.metaKey) && e.key === 'h') {
            e.preventDefault();
            window.location.href = '/';
        }
    });
    
    
    /**
     * Lazy Loading Images (Optional Enhancement)
     * Improves page load performance
     */
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver(function(entries, observer) {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    if (img.dataset.src) {
                        img.src = img.dataset.src;
                        img.removeAttribute('data-src');
                    }
                    imageObserver.unobserve(img);
                }
            });
        });
        
        const lazyImages = document.querySelectorAll('img[data-src]');
        lazyImages.forEach(img => imageObserver.observe(img));
    }
    
    
    /**
     * Console Message
     * Display info for developers
     */
    console.log('%cدانشکده هوش و مکاترونیک', 'font-size: 20px; font-weight: bold; color: #1e3c72;');
    console.log('%cسیستم مدیریت کلاس‌ها', 'font-size: 14px; color: #2196F3;');
    console.log('Version: 1.0.0');
    
});


/**
 * Service Worker Registration (Optional - for PWA)
 * Uncomment to enable offline functionality
 */
/*
if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        navigator.serviceWorker.register('/sw.js')
            .then(function(registration) {
                console.log('ServiceWorker registered:', registration);
            })
            .catch(function(error) {
                console.log('ServiceWorker registration failed:', error);
            });
    });
}
*/

