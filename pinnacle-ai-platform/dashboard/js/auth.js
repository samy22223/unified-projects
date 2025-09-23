/**
 * Authentication Module
 * Handles user authentication, session management, and authorization
 */

class AuthManager {
    constructor() {
        this.token = null;
        this.user = null;
        this.refreshTimer = null;
    }

    async initialize() {
        this.token = localStorage.getItem('pinnacle_auth_token');
        if (this.token) {
            await this.validateToken();
            this.startTokenRefresh();
        }
    }

    async validateToken() {
        try {
            const response = await fetch('/api/v1/auth/verify', {
                headers: {
                    'Authorization': `Bearer ${this.token}`
                }
            });

            if (response.ok) {
                this.user = await response.json();
                return true;
            } else {
                this.logout();
                return false;
            }
        } catch (error) {
            console.error('Token validation failed:', error);
            this.logout();
            return false;
        }
    }

    async login(email, password) {
        try {
            const response = await fetch('/api/v1/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ email, password })
            });

            if (response.ok) {
                const data = await response.json();
                this.setSession(data.token, data.user);
                return { success: true, user: data.user };
            } else {
                const error = await response.json();
                return { success: false, error: error.message };
            }
        } catch (error) {
            return { success: false, error: 'Network error' };
        }
    }

    async register(userData) {
        try {
            const response = await fetch('/api/v1/auth/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(userData)
            });

            if (response.ok) {
                const data = await response.json();
                this.setSession(data.token, data.user);
                return { success: true, user: data.user };
            } else {
                const error = await response.json();
                return { success: false, error: error.message };
            }
        } catch (error) {
            return { success: false, error: 'Network error' };
        }
    }

    setSession(token, user) {
        this.token = token;
        this.user = user;
        localStorage.setItem('pinnacle_auth_token', token);
        this.startTokenRefresh();
    }

    startTokenRefresh() {
        // Refresh token every 50 minutes
        this.refreshTimer = setInterval(async () => {
            await this.refreshToken();
        }, 50 * 60 * 1000);
    }

    async refreshToken() {
        try {
            const response = await fetch('/api/v1/auth/refresh', {
                headers: {
                    'Authorization': `Bearer ${this.token}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.setSession(data.token, data.user);
            } else {
                this.logout();
            }
        } catch (error) {
            console.error('Token refresh failed:', error);
        }
    }

    logout() {
        this.token = null;
        this.user = null;
        localStorage.removeItem('pinnacle_auth_token');
        if (this.refreshTimer) {
            clearInterval(this.refreshTimer);
        }
        window.location.reload();
    }

    isAuthenticated() {
        return !!this.token && !!this.user;
    }

    getUser() {
        return this.user;
    }

    getToken() {
        return this.token;
    }

    hasPermission(permission) {
        if (!this.user || !this.user.permissions) return false;
        return this.user.permissions.includes(permission);
    }

    hasRole(role) {
        return this.user && this.user.role === role;
    }
}

// Export for global use
window.AuthManager = AuthManager;</content>
</edit_file>