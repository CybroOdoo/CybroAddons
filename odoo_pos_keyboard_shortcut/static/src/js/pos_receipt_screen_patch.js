/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { ReceiptScreen } from "@point_of_sale/app/screens/receipt_screen/receipt_screen";
import { onMounted, onWillUnmount } from "@odoo/owl";

//Patch the Receipt screen and add the shortcuts on the Receipt screen
patch(ReceiptScreen.prototype, {
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

        // 1. Select User (Cashier)
        if ((isCtrl || isShift) && (pressedKey === shortcutSelectUser || (pressedCode === 'KeyU' && shortcutSelectUser === 'u'))) {
            matched = true;
            if (typeof this.pos.selectEmployee === 'function') {
                this.pos.selectEmployee();
            } else if (typeof this.pos.selectCashier === 'function') {
                this.pos.selectCashier();
            } else {
                const userSelectors = ['.header-button.cashier-name', '.pos-rightheader .username', '.status-buttons .username', '.username', '.current-user', 'button.user-button', '.cashier-name', '.pos-topheader .username'];
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
        else if (isCtrl && (pressedKey === shortcutClickOk || (shortcutClickOk === 'enter' && pressedKey === 'enter'))) {
            const okBtn = document.querySelector('.popup .confirm') || document.querySelector('.popup .btn-primary') || document.querySelector('.modal-footer .btn-primary');
            if (okBtn) { okBtn.click(); matched = true; }
        }
        else if ((isCtrl && pressedKey === shortcutClickCancel) || (shortcutClickCancel === 'esc' && pressedKey === 'escape')) {
            const cancelBtn = document.querySelector('.popup .cancel') || document.querySelector('.popup .btn-secondary') || document.querySelector('.modal-footer .btn-secondary');
            if (cancelBtn) { cancelBtn.click(); matched = true; }
        }
        else if (isCtrl && (pressedKey === shortcutClosePos || (pressedCode === 'KeyM' && shortcutClosePos === 'm'))) {
            if (typeof this.pos.closePos === 'function') { this.pos.closePos(); matched = true; }
        }

        // RECEIPT SCREEN SPECIFIC
        if (!matched && isCtrl) {
            if (pressedKey === config.shortcut_print_receipt?.trim().toLowerCase()) {
                this.pos.printReceipt();
                matched = true;
            } else if (pressedKey === config.shortcut_new_order?.trim().toLowerCase() ||
                (config.shortcut_new_order?.trim() === 'Enter' && pressedKey === 'enter')) {
                const nextBtn = document.querySelector('.button.next.validation') || document.querySelector('.button.next') || document.querySelector('button.next') || document.querySelector('.top-content-center .button');
                if (nextBtn && typeof nextBtn.click === 'function') {
                    nextBtn.click();
                } else if (typeof this.orderDone === 'function') {
                    this.orderDone();
                } else if (typeof this.orderNext === 'function') {
                    this.orderNext();
                } else {
                    // Fallback to POS clear/add new order if needed
                    this.pos.removeOrder(this.pos.get_order());
                    this.pos.add_new_order();
                }
                matched = true;
            } else if (pressedKey === config.shortcut_sent_email?.trim().toLowerCase()) {
                this.actionSendReceiptOnEmail();
                matched = true;
            }
        }

        if (matched) {
            event.preventDefault();
            event.stopPropagation();
            event.stopImmediatePropagation();
        }
    },
});