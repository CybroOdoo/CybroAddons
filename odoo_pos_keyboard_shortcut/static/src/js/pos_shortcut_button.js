/** @odoo-module */
import { _t } from "@web/core/l10n/translation";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { patch } from "@web/core/utils/patch";
import { ShortcutPopup } from "./pos_shortcut_popup.js";
import { onMounted, onWillUnmount } from "@odoo/owl";

/* Patching ControlButtons and adding keyboard listener */
patch(ControlButtons.prototype, {
    setup() {
        super.setup(...arguments);
        this.pos = usePos();

        // Global key listener added from this component
        const handler = (event) => this._onGlobalShortcutsCapture(event);
        onMounted(() => {
            document.addEventListener("keydown", handler, true);
        });
        onWillUnmount(() => {
            document.removeEventListener("keydown", handler, true);
        });
    },

    /* Function while clicking the button */
    async onClick() {
        if (this.pos.config.is_enable_keyboard_shortcuts) {
            await this.dialog.add(ShortcutPopup, {
                title: _t("POS Keyboard Shortcuts"),
            });
        }
    },

    _onGlobalShortcutsCapture(event) {
        const config = this.pos?.config;
        if (!config?.is_enable_keyboard_shortcuts || !config?.select_shortcut_id) {
            return;
        }

        const pressedKey = event.key.toLowerCase();
        const pressedCode = event.code;
        const isCtrl = (event.ctrlKey || event.metaKey);
        const isShift = event.shiftKey;

        // Block shortcuts if user is typing in an input/textarea/contenteditable
        const isInput = ['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName) || document.activeElement.isContentEditable;
        if (isInput && !isCtrl && !event.altKey) {
            if (pressedKey.length === 1) return;
        }

        let matched = false;

        const shortcutSelectUser = config.shortcut_select_user?.trim().toLowerCase();
        const shortcutCustomerScreen = config.shortcut_customer_screen?.trim().toLowerCase();
        const shortcutClickOk = config.shortcut_click_ok?.trim().toLowerCase();
        const shortcutClickCancel = config.shortcut_click_cancel?.trim().toLowerCase();
        const shortcutClosePos = config.shortcut_close_pos?.trim().toLowerCase();
        const shortcutBackScreen = config.shortcut_back_screen?.trim().toLowerCase();

        // 1. Select User (Cashier)
        if ((isCtrl || isShift) && (pressedKey === shortcutSelectUser || (pressedCode === 'KeyU' && shortcutSelectUser === 'u'))) {
            matched = true;
            if (typeof this.pos.selectEmployee === 'function') {
                this.pos.selectEmployee();
            } else if (typeof this.pos.selectCashier === 'function') {
                this.pos.selectCashier();
            } else {
                const userSelectors = ['.header-button.cashier-name', '.pos-rightheader .username', '.status-buttons .username', '.username', '.current-user', 'button.user-button', '.cashier-name', '.pos-topheader .username', '.status-buttons .pos-profile'];
                for (const selector of userSelectors) {
                    const btn = document.querySelector(selector);
                    if (btn && typeof btn.click === 'function') {
                        btn.click();
                        break;
                    }
                }
            }
        }
        // 1.5 Select Customer
        else if ((isCtrl || isShift) && (pressedKey === shortcutCustomerScreen || (pressedCode === 'KeyC' && shortcutCustomerScreen === 'c'))) {
            matched = true;
            if (typeof this.pos.selectPartner === 'function') {
                this.pos.selectPartner();
            }
        }
        // 2. OK / Cancel
        else if (isCtrl && (pressedKey === shortcutClickOk || (shortcutClickOk === 'enter' && pressedKey === 'enter'))) {
            const okBtn = document.querySelector('.popup .confirm') || document.querySelector('.popup .btn-primary') || document.querySelector('.modal-footer .btn-primary');
            if (okBtn) { okBtn.click(); matched = true; }
        }
        else if ((isCtrl && pressedKey === shortcutClickCancel) || (shortcutClickCancel === 'esc' && pressedKey === 'escape')) {
            const cancelBtn = document.querySelector('.popup .cancel') || document.querySelector('.popup .btn-secondary') || document.querySelector('.modal-footer .btn-secondary');
            if (cancelBtn) { cancelBtn.click(); matched = true; }
        }
        // 3. Close POS
        else if (isCtrl && (pressedKey === shortcutClosePos || (pressedCode === 'KeyM' && shortcutClosePos === 'm'))) {
            if (typeof this.pos.closePos === 'function') { this.pos.closePos(); matched = true; }
            else {
                const closeBtn = document.querySelector('.close-button') || document.querySelector('.header-button.close-pos');
                if (closeBtn) { closeBtn.click(); matched = true; }
            }
        }
        // 4. Back Screen
        else if (isCtrl && pressedKey === shortcutBackScreen) {
            const backBtn = document.querySelector('.back-button') || document.querySelector('.button.back') || document.querySelector('.back');
            if (backBtn) { backBtn.click(); matched = true; }
        }

        if (matched) {
            event.preventDefault();
            event.stopPropagation();
            event.stopImmediatePropagation();
        }
    }
});