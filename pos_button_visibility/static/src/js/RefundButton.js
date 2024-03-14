/** @odoo-module */

import { PosStore } from "@point_of_sale/app/store/pos_store";
import { patch } from "@web/core/utils/patch";
/** Extends PosStore to load model to pos **/
patch(PosStore.prototype, {
        async _processData(loadedData) {
            await super._processData(loadedData);
            this.res_user = loadedData['res.users'];
            this.user_session = loadedData['user_session_ids'];
            this.buttons_pos = loadedData['buttons_pos_ids']
        }
    });
