/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { onMounted, onWillUnmount } from "@odoo/owl";

patch(PaymentScreen.prototype, {
    setup() {
        super.setup(...arguments);

        // Use capture phase for maximum reliability against browser defaults
        const handler = (event) => this._onShortcutsCapture(event);

        onMounted(() => {
            document.addEventListener("keydown", handler, true);
        });

        onWillUnmount(() => {
            document.removeEventListener("keydown", handler, true);
        });
    },

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
            if (pressedKey.length === 1) return;
        }

        let matched = false;

        // ALL SCREEN SHORTCUTS
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
                const userSelectors = ['.header-button.cashier-name', '.pos-rightheader .username', '.status-buttons .username', '.current-user', 'button.user-button', '.cashier-name', '.pos-topheader .username'];
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
            const okBtn = document.querySelector('.popup .confirm') || document.querySelector('.popup .btn-primary') || document.querySelector('.modal-footer .btn-primary');
            if (okBtn) { okBtn.click(); matched = true; }
        }
        // 3. Cancel / Exit
        else if ((isCtrl && pressedKey === shortcutClickCancel) || (shortcutClickCancel === 'esc' && pressedKey === 'escape')) {
            const cancelBtn = document.querySelector('.popup .cancel') || document.querySelector('.popup .btn-secondary') || document.querySelector('.modal-footer .btn-secondary');
            if (cancelBtn) { cancelBtn.click(); matched = true; }
        }
        // 4. Close POS
        else if (isCtrl && (pressedKey === shortcutClosePos || (pressedCode === 'KeyM' && shortcutClosePos === 'm'))) {
            if (typeof this.pos.closePos === 'function') { this.pos.closePos(); matched = true; }
        }

        // PAYMENT SCREEN SPECIFIC
        if (!matched && isCtrl) {
            if (pressedKey === config.shortcut_select_invoice?.trim().toLowerCase()) {
                const invoiceButton = document.querySelector('.js_invoice');
                if (invoiceButton) { invoiceButton.click(); matched = true; }
            }
            else if (pressedKey === shortcutBackScreen) {
                const backButton = document.querySelector('.back');
                if (backButton) { backButton.click(); matched = true; }
            }
            else if (pressedKey === config.shortcut_validate_order?.trim().toLowerCase()) {
                if (typeof this.validateOrder === 'function') { this.validateOrder(); matched = true; }
            }
            else {
                const pmKeys = this.pos.pos_payment_method_key || [];
                const paymentKey = pmKeys.find(pk => pk.key_code?.trim().toLowerCase() === pressedKey || (pressedCode === `Key${pk.key_code?.trim().toUpperCase()}` && pk.key_code?.trim().length === 1));
                if (paymentKey) {
                    const methodId = Array.isArray(paymentKey.payment_method_id) ? paymentKey.payment_method_id[0] : paymentKey.payment_method_id;
                    const methodObj = this.paymentMethods?.find(p => p.id === methodId) || this.pos.payment_methods?.find(p => p.id === methodId);
                    if (methodObj && typeof this.addNewPaymentLine === 'function') {
                        this.addNewPaymentLine({ paymentMethod: methodObj });
                        matched = true;
                    } else if (methodObj && typeof this.addNewPaymentLine === 'function') {
                        this.addNewPaymentLine(methodObj); // alternative argument format
                        matched = true;
                    } else {
                        const methodName = Array.isArray(paymentKey.payment_method_id) ? paymentKey.payment_method_id[1] : '';
                        if (methodName) {
                            const elements = Array.from(document.querySelectorAll('.paymentmethod, .payment-method, .payment-name, .payment-method-display, .payment-method-button'));
                            const el = elements.find(e => e.textContent.includes(methodName) || e.innerText.includes(methodName));
                            if (el) { el.click(); matched = true; }
                        }
                    }
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