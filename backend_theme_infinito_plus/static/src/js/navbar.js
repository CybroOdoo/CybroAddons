/** @odoo-module **/
import { NavBar } from "@web/webclient/navbar/navbar";
import { WebClient } from "@web/webclient/webclient";
import { ControlPanel } from "@web/search/control_panel/control_panel";
import { patch } from "@web/core/utils/patch";
import { session } from "@web/session";
/**
 * Patching ControlPanel prototype to handle refresh functionality.
 */
patch(ControlPanel.prototype, {
     /**
     * Handles the refresh event.
     * Triggers search model notification.
     * @param {Event} ev - The event object.
     */
     onRefresh(ev) {
           this.env.searchModel._notify();
    },
     /**
     * Getter for RefreshOn property.
     * Checks whether the refresh feature is enabled or disabled.
     * @returns {boolean} - Refresh feature status.
     */
    get RefreshOn() {
         return session.infinitoRefresh;
    },
});
