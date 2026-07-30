/** @odoo-module **/

import { Component } from "@odoo/owl";
import { browser } from "@web/core/browser/browser";
import { registry } from "@web/core/registry";

/**
 * Systray button component used to open the Offline Sales interface.
 */

class OfflineSystrayButton extends Component {
    static template = "offline_sale.SystrayButton";
    /**
     * Open the Offline Sales terminal in a new browser tab.
     *
     * Opening the terminal in a separate tab allows users to continue
     * using the Odoo backend while performing offline sales operations.
     */

    on_click() {
        // Open the offline terminal in a NEW tab so the user doesn't lose their main Odoo session.
        // Because this is triggered by a direct user click, the browser will NOT block it!
        window.open("/offline_sale/ui", "_blank");
    }
}
/**
 * Systray item configuration.
 */
const systrayItem = {
    Component: OfflineSystrayButton,
};
/**
 * Register the Offline Sales button in the Odoo systray.
 */
registry.category("systray").add("offline_sale.systray_button", systrayItem, { sequence: 100 });
