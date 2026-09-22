/** @odoo-module **/
import { reactive } from "@odoo/owl";


export const followerState = reactive({
    checked: {},
    version: 0,

    isChecked(followerId) {
        return this.checked[followerId] !== false;
    },

    toggle(followerId, value) {
        this.checked[followerId] = value;
        this.version++;
    }
});
