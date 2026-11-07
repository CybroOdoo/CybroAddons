/** @odoo-module **/
import { ControlPanel } from "@web/search/control_panel/control_panel";
import { patch } from "@web/core/utils/patch";
import { session } from "@web/session";

patch(ControlPanel.prototype, {
    onRefresh() {
        this.env.searchModel?._notify();
    },
    get RefreshOn() {
        return Boolean(session.infinitoRefresh && this.env.searchModel);
    },
});