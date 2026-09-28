/** @odoo-module **/
import { _t } from "@web/core/l10n/translation";
import { Dialog } from "@web/core/dialog/dialog";
import { Component, onMounted, useState } from "@odoo/owl";

export class ShortcutPopup extends Component {
    static template = "pos_keyboard_shortcut.ShortcutPopup";
    static components = { Dialog };
    static defaultProps = {
        confirmText: _t('Ok'),
        cancelText: _t('Cancel'),
        title: '',
        body: '',
    };

    setup() {
    super.setup();
    this.shortcuts = useState({});

    onMounted(async () => {
        await this.loadShortcuts();
    });
}

async loadShortcuts() {
    try {
        const shortcutId = this.env.services.pos.config.select_shortcut_id;

        if (shortcutId) {
            const shortcuts = await this.env.services.orm.read(
                'pos.keyboard.shortcut',
                [shortcutId],
                ['customer_screen', 'next_screen', 'select_qty',
                    'select_discount', 'select_price', 'print_receipt',
                    'back_screen', 'select_user', 'sent_email', 'resume_order',
                    'new_order', 'close_pos', 'select_invoice',
                    'validate_order', 'click_cancel', 'click_ok',
                    'next_screen_show', 'delete_orderlines']
            );

            if (shortcuts && shortcuts.length > 0) {
                Object.assign(this.shortcuts, shortcuts[0]);
            }
        }
    } catch (error) {
        console.error("Error loading shortcuts:", error);
    }
}

    cancel() {
        this.props.close();
    }
}