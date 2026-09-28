/** @odoo-module **/
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { patch } from "@web/core/utils/patch";
import { onMounted, onWillUnmount } from "@odoo/owl";

patch(ProductScreen.prototype, {
    setup() {
        super.setup(...arguments);

        // Use a persistent capture-phase listener to beat the browser's Ctrl+U interception
        const handler = (event) => this._onShortcutsCapture(event);

        onMounted(() => {
            document.addEventListener("keydown", handler, true);
        });

        onWillUnmount(() => {
            document.removeEventListener("keydown", handler, true);
        });
    },

    /**
     * Highly robust synchronous handler with multi-stage execution
     */
    _onShortcutsCapture(event) {
        const config = this.pos?.config;
        if (!config?.is_enable_keyboard_shortcuts || !config?.select_shortcut_id) {
            return;
        }

        const pressedKey = event.key.toLowerCase();
        const pressedCode = event.code;
        const isCtrl = event.ctrlKey || event.metaKey;
        const isShift = event.shiftKey;

        // Block shortcuts if user is typing in an input/textarea/contenteditable
        const isInput = ['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName) || document.activeElement.isContentEditable;
        if (isInput && !isCtrl && !event.altKey) {
            // If it's a plain key or shift+key in an input, don't trigger shortcuts
            // Except for special keys like Backspace/Enter which might be handled later
            if (pressedKey.length === 1) return;
        }

        let matched = false;

        // ALL SCREEN SHORTCUTS (Require Ctrl based on XML, but we handle flexibly)
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
        // 2. OK / Confirm
        else if (isCtrl && (pressedKey === shortcutClickOk || (shortcutClickOk === 'enter' && pressedKey === 'enter'))) {
            const okBtn = document.querySelector('.popup .confirm') || document.querySelector('.popup .btn-primary') || document.querySelector('.modal-footer .btn-primary') || document.querySelector('.button.confirm');
            if (okBtn) { okBtn.click(); matched = true; }
        }
        // 3. Cancel / Exit
        else if ((isCtrl && pressedKey === shortcutClickCancel) || (shortcutClickCancel === 'esc' && pressedKey === 'escape')) {
            const cancelBtn = document.querySelector('.popup .cancel') || document.querySelector('.popup .btn-secondary') || document.querySelector('.modal-footer .btn-secondary') || document.querySelector('.button.cancel');
            if (cancelBtn) { cancelBtn.click(); matched = true; }
        }
        // 4. Close POS
        else if (isCtrl && (pressedKey === shortcutClosePos || (pressedCode === 'KeyM' && shortcutClosePos === 'm'))) {
            const closeBtn = document.querySelector('.close-button') || document.querySelector('.header-button.close-pos');
            if (closeBtn) { closeBtn.click(); matched = true; }
            else if (typeof this.pos.closePos === 'function') { this.pos.closePos(); matched = true; }
        }
        // 5. Back Screen
        else if (isCtrl && pressedKey === shortcutBackScreen) {
            const backBtn = document.querySelector('.back-button') || document.querySelector('.button.back') || document.querySelector('.back');
            if (backBtn) { backBtn.click(); matched = true; }
        }

        // PRODUCT SCREEN SPECIFIC SHORTCUTS (Require Ctrl based on XML)
        if (!matched && isCtrl) {
            if (pressedKey === config.shortcut_select_price?.toLowerCase()) {
                this.onNumpadClick?.('price');
                matched = true;
            } else if (pressedKey === config.shortcut_select_discount?.toLowerCase()) {
                this.onNumpadClick?.('discount');
                matched = true;
            } else if (pressedKey === config.shortcut_select_qty?.toLowerCase()) {
                this.onNumpadClick?.('quantity');
                matched = true;
            } else if (pressedKey === config.shortcut_next_screen?.toLowerCase()) {
                this.pos.pay();
                matched = true;
            }
        }

        // NON-CTRL SHORTCUTS
        if (!matched) {
            // Delete Orderlines (Backspace)
            if (pressedKey === 'backspace' || pressedKey === config.shortcut_delete_orderlines?.toLowerCase()) {
                // Only if not in an input field
                if (!['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)) {
                    this.onNumpadClick?.('delete');
                    matched = true;
                }
            }
        }

        if (matched) {
            event.preventDefault();
            event.stopPropagation();
            event.stopImmediatePropagation();
        }
    },
});