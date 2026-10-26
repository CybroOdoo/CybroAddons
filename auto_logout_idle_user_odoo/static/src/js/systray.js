/* @odoo-module */

import { Component, proxy, onWillStart, onWillUnmount } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";
import { registry } from "@web/core/registry";

import { post } from "@web/core/network/http_service";
import { redirect } from "@web/core/utils/urls";

const STORAGE_KEY = "odoo_idle_last_activity";

class TimerSystrayItem extends Component {
    static template = "auto_logout_idle_user_odoo.TimerSystray";

    setup() {
        this.state = proxy({
            idle_time: null,
        });

        let updatedTimestamp = 0;
        let lastLoggedActivity = 0;
        const events = ["mousemove", "keydown", "click", "touchstart", "mousedown"];

        const resetTimer = () => {
            if (this.minutes) {
                const now = Date.now();
                updatedTimestamp = now + this.minutes * 60 * 1000;
                if (now - lastLoggedActivity > 1000) {
                    lastLoggedActivity = now;
                    try {
                        localStorage.setItem(STORAGE_KEY, now.toString());
                    } catch {
                        // ignore storage errors (e.g. private mode)
                    }
                }
            }
        };

        const handleActivity = () => resetTimer();

        const handleStorageChange = (e) => {
            if (e.key === STORAGE_KEY && e.newValue && this.minutes) {
                const lastActivity = parseInt(e.newValue, 10);
                if (!isNaN(lastActivity)) {
                    updatedTimestamp = lastActivity + this.minutes * 60 * 1000;
                }
            }
        };

        onWillStart(async () => {
            const data = await rpc("/auto_logout_idle_user_odoo/idle_time", {});
            if (data && data.idle_time > 0) {
                this.minutes = data.idle_time;
                const now = Date.now();
                updatedTimestamp = now + this.minutes * 60 * 1000;
                lastLoggedActivity = now;

                // Register event listeners only when idle timer is enabled
                events.forEach((event) => {
                    window.addEventListener(event, handleActivity, { passive: true });
                });
                window.addEventListener("storage", handleStorageChange);

                this.idleInterval = setInterval(async () => {
                    const currentTime = Date.now();
                    const distance = updatedTimestamp - currentTime;

                    if (distance <= 0) {
                        clearInterval(this.idleInterval);
                        this.state.idle_time = "EXPIRED";
                        const url = await post("/web/session/logout", { csrf_token: odoo.csrf_token }, "url");
                        redirect(url);
                        return;
                    }

                    const days = Math.floor(distance / (1000 * 60 * 60 * 24));
                    const hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
                    const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
                    const seconds = Math.floor((distance % (1000 * 60)) / 1000);

                    if (hours && days) {
                        this.state.idle_time = `${days}d ${hours}h ${minutes}m ${seconds}s`;
                    } else if (hours) {
                        this.state.idle_time = `${hours}h ${minutes}m ${seconds}s`;
                    } else {
                        this.state.idle_time = `${minutes}m ${seconds}s`;
                    }
                }, 1000);
            }
        });

        onWillUnmount(() => {
            if (this.idleInterval) {
                clearInterval(this.idleInterval);
            }
            events.forEach((event) => {
                window.removeEventListener(event, handleActivity);
            });
            window.removeEventListener("storage", handleStorageChange);
        });
    }
}

export const systrayItem = {
    Component: TimerSystrayItem,
};

registry.category("systray").add("auto_logout_idle_user_odoo.TimerSystray", systrayItem, { sequence: 25 });

