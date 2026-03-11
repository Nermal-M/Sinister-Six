/**
 * Railway Complaint System - Notifications Handler
 * Manages real-time notifications for department staff
 */

class NotificationManager {
    constructor() {
        this.department = null;
        this.notifications = [];
        this.unreadCount = 0;
        this.pollingInterval = null;
        this.pollingDelay = 2000; // 2 seconds for faster real-time updates
        this.init();
    }

    /**
     * Initialize notification system
     */
    init() {
        this.createNotificationContainer();
        this.setupEventListeners();
        console.log('✓ NotificationManager initialized');
    }

    /**
     * Create notification container in the DOM
     */
    createNotificationContainer() {
        if (document.getElementById('notification-container')) {
            return; // Already exists
        }

        const container = document.createElement('div');
        container.id = 'notification-container';
        container.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            max-width: 400px;
        `;
        document.body.appendChild(container);

        // Create notification badge for unread count
        const badge = document.createElement('div');
        badge.id = 'notification-badge';
        badge.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #d32f2f;
            color: white;
            width: 30px;
            height: 30px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            cursor: pointer;
            z-index: 10000;
            display: none;
        `;
        badge.addEventListener('click', () => this.showNotificationPanel());
        document.body.appendChild(badge);
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Listen for new complaint registrations
        window.addEventListener('complaintRegistered', (e) => {
            const { department, category, priority, complaintId } = e.detail;
            console.log('📢 Complaint registered:', complaintId, 'for department:', department);
            // Refresh notifications immediately
            this.fetchNotifications();
        });
    }

    /**
     * Set the department for this notification manager
     */
    setDepartment(department) {
        if (this.department !== department) {
            this.department = department;
            console.log('📍 Notification department set to:', department);
            this.startPolling();
        }
    }

    /**
     * Start polling for new notifications
     */
    startPolling() {
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
        }

        // Fetch immediately
        this.fetchNotifications();

        // Then poll periodically
        this.pollingInterval = setInterval(() => {
            this.fetchNotifications();
        }, this.pollingDelay);

        console.log('🔄 Started polling for notifications every', this.pollingDelay, 'ms');
    }

    /**
     * Stop polling for notifications
     */
    stopPolling() {
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
            this.pollingInterval = null;
        }
        console.log('⏹️ Stopped notification polling');
    }

    /**
     * Fetch notifications from API
     */
    async fetchNotifications() {
        if (!this.department) {
            return;
        }

        try {
            const response = await fetch(
                `http://localhost:5000/api/notifications/department/${encodeURIComponent(this.department)}?show_read=false`,
                {
                    method: 'GET',
                    headers: { 'Content-Type': 'application/json' }
                }
            );

            if (!response.ok) {
                console.error('Failed to fetch notifications:', response.status);
                return;
            }

            const data = await response.json();

            if (data.success) {
                const previousCount = this.unreadCount;
                this.notifications = data.notifications || [];
                this.unreadCount = data.count || 0;

                // Update badge
                this.updateBadge();

                // Show toast for new notifications
                if (this.unreadCount > previousCount) {
                    const newNotifications = this.unreadCount - previousCount;
                    this.showToast(`🔔 ${newNotifications} new complaint(s) received!`, 'info', 5000);
                }

                console.log('📬 Fetched', this.unreadCount, 'unread notifications');
            }
        } catch (error) {
            console.error('Error fetching notifications:', error);
        }
    }

    /**
     * Update notification badge
     */
    updateBadge() {
        const badge = document.getElementById('notification-badge');
        if (!badge) return;

        if (this.unreadCount > 0) {
            badge.textContent = this.unreadCount > 99 ? '99+' : this.unreadCount;
            badge.style.display = 'flex';
        } else {
            badge.style.display = 'none';
        }
    }

    /**
     * Show a notification toast
     */
    showToast(message, type = 'info', duration = 4000) {
        const container = document.getElementById('notification-container');
        if (!container) return;

        const toast = document.createElement('div');
        toast.className = `notification-toast notification-${type}`;
        toast.style.cssText = `
            background: ${this.getToastColor(type)};
            color: white;
            padding: 16px;
            margin-bottom: 10px;
            border-radius: 4px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.2);
            animation: slideIn 0.3s ease-out;
            cursor: pointer;
            min-width: 300px;
        `;

        toast.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span>${message}</span>
                <button style="background: none; border: none; color: white; cursor: pointer; font-size: 20px; padding: 0;">×</button>
            </div>
        `;

        const closeBtn = toast.querySelector('button');
        closeBtn.addEventListener('click', () => {
            toast.style.animation = 'slideOut 0.3s ease-out';
            setTimeout(() => toast.remove(), 300);
        });

        container.appendChild(toast);

        // Add CSS animations if not already present
        if (!document.getElementById('notification-animations')) {
            const style = document.createElement('style');
            style.id = 'notification-animations';
            style.textContent = `
                @keyframes slideIn {
                    from {
                        transform: translateX(400px);
                        opacity: 0;
                    }
                    to {
                        transform: translateX(0);
                        opacity: 1;
                    }
                }
                @keyframes slideOut {
                    to {
                        transform: translateX(400px);
                        opacity: 0;
                    }
                }
            `;
            document.head.appendChild(style);
        }

        // Auto-remove after duration
        if (duration > 0) {
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.style.animation = 'slideOut 0.3s ease-out';
                    setTimeout(() => toast.remove(), 300);
                }
            }, duration);
        }

        return toast;
    }

    /**
     * Get toast color based on type
     */
    getToastColor(type) {
        const colors = {
            'success': '#4CAF50',
            'error': '#f44336',
            'warning': '#ff9800',
            'info': '#2196F3'
        };
        return colors[type] || colors['info'];
    }

    /**
     * Show notification panel with all notifications
     */
    showNotificationPanel() {
        // Create modal
        const modal = document.createElement('div');
        modal.id = 'notification-modal';
        modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            display: flex;
            justify-content: flex-end;
            z-index: 9998;
        `;

        const panel = document.createElement('div');
        panel.style.cssText = `
            background: white;
            width: 400px;
            height: 100%;
            overflow-y: auto;
            box-shadow: -2px 0 8px rgba(0,0,0,0.2);
        `;

        // Header
        const header = document.createElement('div');
        header.style.cssText = `
            background: #d32f2f;
            color: white;
            padding: 16px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: sticky;
            top: 0;
            z-index: 1;
        `;
        header.innerHTML = `
            <h3 style="margin: 0;">🔔 Notifications</h3>
            <button id="close-modal" style="background: none; border: none; color: white; font-size: 24px; cursor: pointer;">×</button>
        `;

        panel.appendChild(header);

        // Notifications list
        const content = document.createElement('div');
        content.style.cssText = `padding: 0;`;

        if (this.notifications.length === 0) {
            content.innerHTML = '<p style="padding: 20px; text-align: center; color: #999;">No notifications</p>';
        } else {
            this.notifications.forEach(notif => {
                const notifElement = this.createNotificationElement(notif);
                content.appendChild(notifElement);
            });
        }

        panel.appendChild(content);

        // Footer
        if (this.notifications.length > 0) {
            const footer = document.createElement('div');
            footer.style.cssText = `
                padding: 12px;
                border-top: 1px solid #ddd;
                position: sticky;
                bottom: 0;
                background: #f9f9f9;
            `;
            footer.innerHTML = `
                <button id="mark-all-read" style="width: 100%; padding: 8px; background: #2196F3; color: white; border: none; border-radius: 4px; cursor: pointer;">
                    Mark all as read
                </button>
            `;
            footer.querySelector('#mark-all-read').addEventListener('click', () => this.markAllRead());
            panel.appendChild(footer);
        }

        modal.appendChild(panel);
        document.body.appendChild(modal);

        // Close button
        modal.querySelector('#close-modal').addEventListener('click', () => {
            modal.remove();
        });

        // Close on outside click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
    }

    /**
     * Create notification element
     */
    createNotificationElement(notif) {
        const element = document.createElement('div');
        element.style.cssText = `
            padding: 12px 16px;
            border-bottom: 1px solid #eee;
            cursor: pointer;
            transition: background 0.2s;
            background: ${notif.is_read ? 'white' : '#f0f8ff'};
        `;

        const priorityColor = this.getPriorityColor(notif.priority);
        const createdAt = new Date(notif.created_at).toLocaleString();

        element.innerHTML = `
            <div style="display: flex; gap: 8px; margin-bottom: 8px;">
                <span style="background: ${priorityColor}; color: white; padding: 2px 8px; border-radius: 3px; font-size: 12px; font-weight: bold;">
                    ${notif.priority}
                </span>
                <span style="background: #e0e0e0; color: #333; padding: 2px 8px; border-radius: 3px; font-size: 12px;">
                    ${notif.category}
                </span>
            </div>
            <p style="margin: 4px 0; font-size: 14px; line-height: 1.4; color: #333;">
                <strong>Complaint ID:</strong> ${notif.complaint_id}
            </p>
            <p style="margin: 4px 0; font-size: 13px; line-height: 1.4; color: #666;">
                ${notif.complaint_text}
            </p>
            <p style="margin: 4px 0; font-size: 12px; color: #999;">
                <strong>From:</strong> ${notif.user_email}
            </p>
            <p style="margin: 4px 0; font-size: 11px; color: #bbb;">
                ${createdAt}
            </p>
        `;

        element.addEventListener('mouseover', () => {
            element.style.background = '#f5f5f5';
        });

        element.addEventListener('mouseout', () => {
            element.style.background = notif.is_read ? 'white' : '#f0f8ff';
        });

        element.addEventListener('click', () => {
            this.markAsRead(notif._id);
        });

        return element;
    }

    /**
     * Get priority color
     */
    getPriorityColor(priority) {
        const colors = {
            'Low': '#4CAF50',
            'Medium': '#ff9800',
            'High': '#f44336',
            'Critical': '#9c27b0'
        };
        return colors[priority] || '#999';
    }

    /**
     * Mark notification as read
     */
    async markAsRead(notificationId) {
        try {
            const response = await fetch(
                `http://localhost:5000/api/notifications/${notificationId}/read`,
                {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' }
                }
            );

            if (response.ok) {
                this.fetchNotifications();
                console.log('✓ Notification marked as read');
            }
        } catch (error) {
            console.error('Error marking notification as read:', error);
        }
    }

    /**
     * Mark all notifications as read
     */
    async markAllRead() {
        try {
            const response = await fetch(
                `http://localhost:5000/api/notifications/mark-all-read`,
                {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ department: this.department })
                }
            );

            if (response.ok) {
                const data = await response.json();
                this.showToast(`✓ Marked ${data.modified_count} notifications as read`, 'success');
                this.fetchNotifications();
                document.getElementById('notification-modal')?.remove();
                console.log('✓ All notifications marked as read');
            }
        } catch (error) {
            console.error('Error marking all notifications as read:', error);
        }
    }

    /**
     * Show notification popup when complaint is registered
     */
    showRegistrationNotification(complaintData) {
        const { complaintId, department, category, priority } = complaintData;

        // Create popup
        const popup = document.createElement('div');
        popup.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: white;
            padding: 24px;
            border-radius: 8px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            z-index: 10001;
            max-width: 400px;
            text-align: center;
        `;

        const overlay = document.createElement('div');
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.3);
            z-index: 10000;
        `;

        popup.innerHTML = `
            <div style="font-size: 48px; margin-bottom: 16px;">✅</div>
            <h2 style="margin: 0 0 12px 0; color: #333;">Complaint Registered Successfully!</h2>
            <p style="margin: 12px 0; color: #666;">Complaint ID: <strong>${complaintId}</strong></p>
            <div style="background: #f5f5f5; padding: 12px; border-radius: 4px; margin: 16px 0;">
                <p style="margin: 4px 0; font-size: 14px;">
                    📌 <strong>Category:</strong> ${category}
                </p>
                <p style="margin: 4px 0; font-size: 14px;">
                    ⚡ <strong>Priority:</strong> ${priority}
                </p>
                <p style="margin: 4px 0; font-size: 14px;">
                    🏢 <strong>Department:</strong> ${department}
                </p>
            </div>
            <p style="margin: 12px 0; color: #999; font-size: 13px;">
                The notification has been sent to ${department}
            </p>
            <button id="close-popup" style="background: #4CAF50; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; font-size: 14px;">
                Close
            </button>
        `;

        document.body.appendChild(overlay);
        document.body.appendChild(popup);

        const closeBtn = popup.querySelector('#close-popup');
        closeBtn.addEventListener('click', () => {
            popup.remove();
            overlay.remove();
        });

        overlay.addEventListener('click', () => {
            popup.remove();
            overlay.remove();
        });

        return { popup, overlay };
    }
}

// Initialize global notification manager
const notificationManager = new NotificationManager();

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = notificationManager;
}
