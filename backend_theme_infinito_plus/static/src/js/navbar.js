/** @odoo-module **/
import { NavBar } from "@web/webclient/navbar/navbar";
import { WebClient } from "@web/webclient/webclient";
import { ControlPanel } from "@web/search/control_panel/control_panel";
import { patch } from "@web/core/utils/patch";
import session from 'web.session';
patch(ControlPanel.prototype, 'backend_theme_infinito_plus/static/src/js/navbar.ControlPanel.js', {
//     works when clicking refresh icon
     onRefresh(ev) {
           this.env.searchModel._notify();
    },
    // check whether the refresh feature is enabled or disabled
    get RefreshOn() {
        return session.infinitoRefresh;
    },
});
