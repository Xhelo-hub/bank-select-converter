/**
 * Base JavaScript - Albanian Bank Statement Converter
 * Handles sidebar toggle, active menu highlighting, and common UI interactions
 */

(function() {
    'use strict';

    // ============================================
    // Sidebar Toggle
    // ============================================
    function initSidebarToggle() {
        const sidebar = document.querySelector('.sidebar');
        const toggleBtn = document.querySelector('.sidebar-toggle');

        if (!sidebar || !toggleBtn) return;

        // Load saved state from localStorage
        const savedState = localStorage.getItem('sidebarCollapsed');
        if (savedState === 'true') {
            sidebar.classList.add('collapsed');
        }

        // Toggle sidebar on button click
        toggleBtn.addEventListener('click', function() {
            sidebar.classList.toggle('collapsed');

            // Save state to localStorage
            const isCollapsed = sidebar.classList.contains('collapsed');
            localStorage.setItem('sidebarCollapsed', isCollapsed);
        });
    }

    // ============================================
    // Active Menu Item Highlighting
    // ============================================
    function highlightActiveMenuItem() {
        const currentPath = window.location.pathname;
        const menuLinks = document.querySelectorAll('.sidebar-menu-link');

        menuLinks.forEach(function(link) {
            const linkPath = new URL(link.href).pathname;

            // Check if current path matches link path
            if (currentPath === linkPath ||
                (linkPath !== '/' && currentPath.startsWith(linkPath))) {
                link.classList.add('active');
            } else {
                link.classList.remove('active');
            }
        });
    }

    // ============================================
    // Mobile Sidebar Toggle
    // ============================================
    function initMobileSidebar() {
        const sidebar = document.querySelector('.sidebar');
        const mobileMenuBtn = document.querySelector('.mobile-menu-btn');

        if (!sidebar || !mobileMenuBtn) return;

        // Create overlay
        const overlay = document.createElement('div');
        overlay.className = 'sidebar-overlay';
        overlay.style.cssText = `
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            z-index: 99;
        `;

        // Add overlay to body
        document.body.appendChild(overlay);

        // Toggle sidebar on mobile button click
        mobileMenuBtn.addEventListener('click', function() {
            sidebar.classList.add('mobile-open');
            overlay.style.display = 'block';
        });

        // Close sidebar when clicking overlay
        overlay.addEventListener('click', function() {
            sidebar.classList.remove('mobile-open');
            overlay.style.display = 'none';
        });

        // Close sidebar when clicking a menu link on mobile
        const menuLinks = document.querySelectorAll('.sidebar-menu-link');
        menuLinks.forEach(function(link) {
            link.addEventListener('click', function() {
                if (window.innerWidth <= 768) {
                    sidebar.classList.remove('mobile-open');
                    overlay.style.display = 'none';
                }
            });
        });
    }

    // ============================================
    // Flash Message Auto-dismiss
    // ============================================
    function initFlashMessages() {
        const alerts = document.querySelectorAll('.alert');

        alerts.forEach(function(alert) {
            // Add close button if doesn't exist
            if (!alert.querySelector('.alert-close')) {
                const closeBtn = document.createElement('button');
                closeBtn.className = 'alert-close';
                closeBtn.innerHTML = '×';
                closeBtn.style.cssText = `
                    float: right;
                    background: none;
                    border: none;
                    font-size: 1.5rem;
                    cursor: pointer;
                    line-height: 1;
                    margin-left: 1rem;
                    opacity: 0.6;
                `;

                closeBtn.addEventListener('click', function() {
                    alert.style.opacity = '0';
                    setTimeout(function() {
                        alert.remove();
                    }, 300);
                });

                alert.insertBefore(closeBtn, alert.firstChild);
            }

            // Auto-dismiss after 5 seconds
            setTimeout(function() {
                if (alert.parentElement) {
                    alert.style.transition = 'opacity 0.3s ease';
                    alert.style.opacity = '0';
                    setTimeout(function() {
                        alert.remove();
                    }, 300);
                }
            }, 5000);
        });
    }

    // ============================================
    // Logout Confirmation
    // ============================================
    function initLogoutConfirmation() {
        const logoutBtn = document.querySelector('.header-logout-btn');

        if (logoutBtn) {
            logoutBtn.addEventListener('click', function(e) {
                e.preventDefault();

                if (confirm('Are you sure you want to logout?')) {
                    window.location.href = logoutBtn.getAttribute('data-logout-url') || '/logout';
                }
            });
        }
    }

    // ============================================
    // Tooltips for Collapsed Sidebar
    // ============================================
    function initTooltips() {
        const sidebar = document.querySelector('.sidebar');
        if (!sidebar) return;

        const menuLinks = document.querySelectorAll('.sidebar-menu-link');

        menuLinks.forEach(function(link) {
            const text = link.querySelector('.sidebar-menu-text');
            if (text) {
                link.setAttribute('title', text.textContent.trim());
            }
        });
    }

    // ============================================
    // Admin Section Toggle
    // ============================================
    function initAdminSectionToggle() {
        const sectionHeaders = document.querySelectorAll('.sidebar-menu-section-header');

        sectionHeaders.forEach(function(header) {
            const section = header.closest('.sidebar-menu-section');
            const sectionName = header.getAttribute('data-section');

            // Load saved state from localStorage
            const savedState = localStorage.getItem('adminSection_' + sectionName);
            if (savedState === 'collapsed') {
                section.classList.add('collapsed');
            }

            // Toggle section on button click
            header.addEventListener('click', function() {
                section.classList.toggle('collapsed');

                // Save state to localStorage
                const isCollapsed = section.classList.contains('collapsed');
                localStorage.setItem('adminSection_' + sectionName, isCollapsed ? 'collapsed' : 'expanded');
            });
        });
    }

    // ============================================
    // Initialize All Features
    // ============================================
    function init() {
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', init);
            return;
        }

        initSidebarToggle();
        highlightActiveMenuItem();
        initMobileSidebar();
        initFlashMessages();
        initLogoutConfirmation();
        initTooltips();
        initAdminSectionToggle();
    }

    // Start initialization
    init();

})();
