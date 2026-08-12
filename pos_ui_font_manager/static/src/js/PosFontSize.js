/** @odoo-module */

import { Chrome } from "@point_of_sale/app/pos_app";
import { patch } from "@web/core/utils/patch";
import { onMounted } from "@odoo/owl";

patch(Chrome.prototype, {
    setup() {
        super.setup(...arguments);
        onMounted(() => {
            this._applyPosFontSizes();
        });
    },

    _applyPosFontSizes() {
        const config = this.pos?.config;
        if (!config) {
            return;
        }

        const preset = config.pos_font_preset || 'medium';
        const globalScale = ((config.pos_global_scale ?? 100) / 100);

        // Base font sizes for the "medium" preset (in px)
        const baseSizes = {
            'product-card': 14,
            'product-price': 12,
            'categories': 13,
            'numpad': 14,
            'order-line': 13,
            'control-buttons': 13,
            'payment-screen': 14,
            'payment-total': 60,
            'receipt-preview': 12,
            'customer-list': 13,
            'navbar': 14,
            'ticket-screen': 13,
            'popups-dialogs': 14,
        };

        // Multipliers for each preset
        const multipliers = {
            small: 0.80,
            medium: 1.00,
            large: 1.20,
            extra_large: 1.40,
            custom: 1.00,
        };

        // Map CSS-var key → pos.config field name (underscore version)
        const fieldMap = {
            'product-card': 'pos_product_card_font_size',
            'product-price': 'pos_product_price_font_size',
            'categories': 'pos_categories_font_size',
            'numpad': 'pos_numpad_font_size',
            'order-line': 'pos_order_line_font_size',
            'control-buttons': 'pos_control_buttons_font_size',
            'payment-screen': 'pos_payment_screen_font_size',
            'payment-total': 'pos_payment_total_font_size',
            'receipt-preview': 'pos_receipt_preview_font_size',
            'customer-list': 'pos_customer_list_font_size',
            'navbar': 'pos_navbar_font_size',
            'ticket-screen': 'pos_ticket_screen_font_size',
            'popups-dialogs': 'pos_popups_dialogs_font_size',
        };

        const presetMultiplier = multipliers[preset] ?? 1.0;
        const rootStyle = document.documentElement.style;

        for (const [key, baseSize] of Object.entries(baseSizes)) {
            let finalSize;
            if (preset === 'custom') {
                const field = fieldMap[key];
                const customVal = config[field];
                if (customVal && customVal > 0) {
                    finalSize = `${customVal}px`;
                } else {
                    finalSize = `${Math.round(baseSize * globalScale)}px`;
                }
            } else {
                finalSize = `${Math.round(baseSize * presetMultiplier * globalScale)}px`;
            }
            rootStyle.setProperty(`--pos-${key}-font-size`, finalSize);
        }

        if (preset === 'custom' && config.pos_payment_total_font_size && config.pos_payment_total_font_size > 0) {
            rootStyle.setProperty('--pos-order-summary-total-font-size', `${config.pos_payment_total_font_size}px`);
        } else {
            rootStyle.removeProperty('--pos-order-summary-total-font-size');
        }
    },
});
