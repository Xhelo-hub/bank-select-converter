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
    // Notification Bell System
    // ============================================
    function initNotifications() {
        // Update badge on load
        updateNotificationBadge();

        // Poll for new notifications every 30 seconds
        setInterval(updateNotificationBadge, 30000);

        // Close dropdown when clicking outside
        document.addEventListener('click', function(e) {
            var dropdown = document.getElementById('notificationDropdown');
            var wrapper = e.target.closest('.notification-wrapper');
            if (!wrapper && dropdown) {
                dropdown.classList.remove('active');
            }
        });
    }

    // Toggle notification dropdown
    window.toggleNotifications = function() {
        var dropdown = document.getElementById('notificationDropdown');
        if (!dropdown) return;

        var isActive = dropdown.classList.toggle('active');
        if (isActive) {
            loadNotifications();
        }
    };

    // Update unread notification badge
    function updateNotificationBadge() {
        fetch('/notifications/unread-count')
            .then(function(r) { return r.json(); })
            .then(function(data) {
                var badge = document.getElementById('notifBadge');
                if (!badge) return;
                if (data.count > 0) {
                    badge.textContent = data.count > 99 ? '99+' : data.count;
                    badge.style.display = 'flex';
                } else {
                    badge.style.display = 'none';
                }
            })
            .catch(function() {});
    }

    // Load notifications into dropdown
    function loadNotifications() {
        var list = document.getElementById('notifList');
        if (!list) return;

        fetch('/notifications/my')
            .then(function(r) { return r.json(); })
            .then(function(data) {
                var notifications = data.notifications || [];
                if (notifications.length === 0) {
                    list.innerHTML = '<div class="notif-empty">Nuk ka njoftime</div>';
                    return;
                }

                // Show max 5 in dropdown
                var html = '';
                var shown = notifications.slice(0, 5);
                shown.forEach(function(n) {
                    var isUnread = !n.is_read;
                    html += '<div class="notif-item ' + (isUnread ? 'unread' : '') + '" onclick="markNotificationRead(\'' + n.id + '\', this)">';
                    html += '<div class="notif-item-header">';
                    html += '<span class="notif-title">' + escapeHtml(n.title) + '</span>';
                    html += '<span class="notif-time">' + formatRelativeTime(n.created_at) + '</span>';
                    html += '</div>';
                    html += '<div class="notif-message">' + escapeHtml(n.message) + '</div>';
                    html += '</div>';
                });
                list.innerHTML = html;
            })
            .catch(function() {
                list.innerHTML = '<div class="notif-empty">Gabim në ngarkim</div>';
            });
    }

    // Mark single notification as read
    window.markNotificationRead = function(id, el) {
        fetch('/notifications/mark-read/' + id, { method: 'POST' })
            .then(function(r) { return r.json(); })
            .then(function() {
                if (el) el.classList.remove('unread');
                updateNotificationBadge();
            })
            .catch(function() {});
    };

    // Mark all notifications as read
    window.markAllRead = function() {
        fetch('/notifications/mark-all-read', { method: 'POST' })
            .then(function(r) { return r.json(); })
            .then(function() {
                var items = document.querySelectorAll('.notif-item.unread');
                items.forEach(function(item) { item.classList.remove('unread'); });
                updateNotificationBadge();
            })
            .catch(function() {});
    };

    // Format relative time
    function formatRelativeTime(isoString) {
        if (!isoString) return '';
        var date = new Date(isoString);
        var now = new Date();
        var diff = Math.floor((now - date) / 1000);

        if (diff < 60) return 'tani';
        if (diff < 3600) return Math.floor(diff / 60) + 'm';
        if (diff < 86400) return Math.floor(diff / 3600) + 'o';
        if (diff < 604800) return Math.floor(diff / 86400) + 'd';
        return date.toLocaleDateString('sq');
    }

    // Escape HTML to prevent XSS
    function escapeHtml(text) {
        var div = document.createElement('div');
        div.textContent = text || '';
        return div.innerHTML;
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
        initNotifications();
    }

    // Start initialization
    init();

})();
