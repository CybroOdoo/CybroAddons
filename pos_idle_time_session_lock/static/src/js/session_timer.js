import { onMounted, onWillUnmount, proxy, useExternalListener } from "@odoo/owl";
import { patch } from "@web/core/utils/patch";
import { Navbar } from "@point_of_sale/app/components/navbar/navbar";

patch(Navbar.prototype, {
    setup() {
        super.setup(...arguments);
        this.timerState = proxy({ time: null });
        this.idleIntervalId = null;
        this.idleDeadline = 0;

        if (this.pos?.config?.pos_lock) {
            useExternalListener(window, "click", () => this.onUserActivity(), true);
            useExternalListener(window, "keydown", () => this.onUserActivity(), true);
            useExternalListener(window, "pointerdown", () => this.onUserActivity(), true);
            useExternalListener(window, "touchstart", () => this.onUserActivity(), true);

            onMounted(() => this.startIdleTimer());
            onWillUnmount(() => this.stopIdleTimer());
        }
    },

    startIdleTimer() {
        this.stopIdleTimer();
        this.resetTimer();
        this.tickTimer();
        this.idleIntervalId = setInterval(() => this.tickTimer(), 1000);
    },

    stopIdleTimer() {
        if (this.idleIntervalId) {
            clearInterval(this.idleIntervalId);
            this.idleIntervalId = null;
        }
    },

    onUserActivity() {
        if (this.pos?.config?.pos_lock) {
            this.resetTimer();
        }
    },

    resetTimer() {
        const timeoutMinutes = this.pos?.config?.idle_time_limit;
        if (!timeoutMinutes || timeoutMinutes <= 0) {
            this.timerState.time = null;
            return;
        }
        this.idleDeadline = Date.now() + timeoutMinutes * 60 * 1000;
    },

    lockSession() {
        if (this.pos?.router?.currentScreen?.() !== "LoginScreen") {
            if (typeof this.pos?.showLoginScreen === "function") {
                this.pos.showLoginScreen();
            } else if (typeof this.pos?.navigate === "function") {
                this.pos.navigate("LoginScreen");
            }
        }
    },

    tickTimer() {
        const timeoutMinutes = this.pos?.config?.idle_time_limit;
        if (!this.pos?.config?.pos_lock || !timeoutMinutes || timeoutMinutes <= 0 || !this.idleDeadline) {
            this.timerState.time = null;
            return;
        }

        const remainingMs = this.idleDeadline - Date.now();
        if (remainingMs <= 0) {
            this.timerState.time = "0 m 0 s";
            this.lockSession();
            this.resetTimer();
            return;
        }

        const totalSeconds = Math.max(0, Math.floor(remainingMs / 1000));
        const hours = Math.floor(totalSeconds / 3600);
        const minutes = Math.floor((totalSeconds % 3600) / 60);
        const seconds = totalSeconds % 60;

        this.timerState.time = hours > 0
            ? `${hours} h ${minutes} m ${seconds} s`
            : `${minutes} m ${seconds} s`;
    },
});