/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/services/pos_store";

patch(PosStore.prototype, {
    // We handle every shortcut logic directly in screens
    // using synchronously available pos.config fields
    async _processData(loadedData) {
        await super._processData(...arguments);
        if (loadedData && loadedData['pos.keyboard.shortcut']) {
            this.pos_keyboard_shortcut = loadedData['pos.keyboard.shortcut'];
        }
        if (loadedData && loadedData['pos.payment.method.key']) {
            this.pos_payment_method_key = loadedData['pos.payment.method.key'];
        }
    },
    async processServerData() {
        await super.processServerData(...arguments);
        const data = arguments.length > 0 ? arguments[0] : null;
        if (data && data['pos.keyboard.shortcut']) {
            this.pos_keyboard_shortcut = data['pos.keyboard.shortcut'];
        }
        if (data && data['pos.payment.method.key']) {
            this.pos_payment_method_key = data['pos.payment.method.key'];
        }
        if (!this.pos_payment_method_key && this.env?.services?.orm) {
            try {
                this.pos_payment_method_key = await this.env.services.orm.searchRead(
                    'pos.payment.method.key',
                    [['keyboard_shortcut_id', '=', this.config.select_shortcut_id?.[0] || this.config.select_shortcut_id]],
                    ['id', 'key_code', 'payment_method_id']
                );
            } catch (e) {
                console.warn("Failed to load pos_payment_method_key via RPC", e);
            }
        }
    },
});