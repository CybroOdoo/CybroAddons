/** @odoo-module */
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { patch } from "@web/core/utils/patch";
import { onMounted, onWillUnmount } from "@odoo/owl";
import { CustomMessageAlertPopup } from "./Popup/AlertPopup";
import { CustomMessageInfoPopup } from "./Popup/InfoPopup";
import { CustomMessageWarnPopup } from "./Popup/WarningPopup";

const MESSAGE_TYPE_LABELS = {
    alert: "Alert",
    info: "Information",
    warn: "Warning",
};

const MESSAGE_POPUP_COMPONENTS = {
    alert: CustomMessageAlertPopup,
    info: CustomMessageInfoPopup,
    warn: CustomMessageWarnPopup,
};

// Patching the ProductScreen to show timed custom messages.
patch(ProductScreen.prototype, {
    setup() {
        super.setup();
        this.customMessageInterval = null;
        if (!this.pos.customMessageState) {
            let initialShownKeys = [];
            try {
                const stored = localStorage.getItem('pos_custom_message_shownKeys');
                if (stored) {
                    initialShownKeys = JSON.parse(stored);
                }
            } catch (e) {
                console.warn("Failed to read from localStorage", e);
            }
            this.pos.customMessageState = {
                shownKeys: new Set(initialShownKeys),
            };
        }
        onMounted(() => {
            this._checkCustomMessages();
            this.customMessageInterval = setInterval(() => {
                this._checkCustomMessages();
            }, 1000);
        });
        onWillUnmount(() => {
            if (this.customMessageInterval) {
                clearInterval(this.customMessageInterval);
                this.customMessageInterval = null;
            }
        });
    },

    _checkCustomMessages() {
        const messages = this._getCustomMessages();
        const currentConfigId = this.pos.config?.id;
        if (!currentConfigId || !messages.length) {
            return;
        }
        const now = new Date();
        const dateKey = this._getCustomMessageDateKey(now);
        for (const message of messages) {
            if (!this._messageMatchesCurrentConfig(message, currentConfigId)) {
                continue;
            }
            const scheduledAt = this._getScheduledExecutionDate(
                message.execution_time,
                now
            );
            if (!scheduledAt) {
                continue;
            }
            const shownKey = `${message.id}:${currentConfigId}:${dateKey}:${message.execution_time}`;

            const isExactTime = now.getHours() === scheduledAt.getHours() && now.getMinutes() === scheduledAt.getMinutes();

            if (this.pos.customMessageState.shownKeys.has(shownKey) || !isExactTime) {
                continue;
            }
            this.pos.customMessageState.shownKeys.add(shownKey);
            try {
                localStorage.setItem(
                    'pos_custom_message_shownKeys',
                    JSON.stringify([...this.pos.customMessageState.shownKeys])
                );
            } catch (e) {
                console.warn("Failed to write to localStorage", e);
            }
            this._showCustomMessage(message);
        }
    },

    _getCustomMessages() {
        return this.pos.models?.["pos.custom.message"]?.getAll?.() || [];
    },

    _messageMatchesCurrentConfig(message, currentConfigId) {
        const configs = message.pos_config_ids || message.raw?.pos_config_ids || [];
        if (!Array.isArray(configs)) {
            return false;
        }
        return configs.some((config) =>
            typeof config === "number" ? config === currentConfigId : config?.id === currentConfigId
        );
    },

    _getScheduledExecutionDate(executionTime, referenceDate) {
        const executionMinutes = this._getExecutionMinutes(executionTime);
        if (executionMinutes === null) {
            return null;
        }
        const hours = Math.floor(executionMinutes / 60);
        const minutes = executionMinutes % 60;
        return new Date(
            referenceDate.getFullYear(),
            referenceDate.getMonth(),
            referenceDate.getDate(),
            hours,
            minutes,
            0,
            0
        );
    },

    _getExecutionMinutes(executionTime) {
        if (typeof executionTime !== "number" || Number.isNaN(executionTime)) {
            return null;
        }
        const totalMinutes = Math.round(executionTime * 60);
        return Math.max(0, Math.min((24 * 60) - 1, totalMinutes));
    },

    _getCustomMessageDateKey(date) {
        const year = date.getFullYear();
        const month = `${date.getMonth() + 1}`.padStart(2, "0");
        const day = `${date.getDate()}`.padStart(2, "0");
        return `${year}-${month}-${day}`;
    },

    _showCustomMessage(message) {
        const typeLabel = MESSAGE_TYPE_LABELS[message.message_type] || "Alert";
        const title = message.title
            ? `${typeLabel}: ${message.title}`
            : typeLabel;
        const PopupComponent =
            MESSAGE_POPUP_COMPONENTS[message.message_type] || CustomMessageAlertPopup;
        this.dialog.add(PopupComponent, {
            title,
            body: message.message_text || "",
        });
    },
});
