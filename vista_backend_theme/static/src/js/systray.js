/* @odoo-module */
import { Component, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { session } from "@web/session";
import { useService } from "@web/core/utils/hooks";

export class ThemeWidget extends Component {
    static template = "vista_backend_theme.theme_systray"

    setup() {
        this.state = useState({
            is_admin: false,
        })
        this.action = useService("action");

        try {
            this.state.is_admin = session.is_admin || false;

            if (session.storeData &&
                session.storeData['res.partner'] &&
                session.storeData.Store &&
                session.storeData.Store.self) {

                const admin = session.storeData['res.partner'].find(
                    (partner) => partner.id === session.storeData.Store.self.id
                );

                if (admin && admin.isAdmin !== undefined) {
                    this.state.is_admin = admin.isAdmin;
                }
            }
        } catch (error) {
            console.warn("Error checking admin status:", error);
            this.state.is_admin = false;
        }
    }

    _onClick() {
        this.action.doAction({
            type: 'ir.actions.act_window',
            name: 'Theme data',
            res_model: 'theme.data',
            view_mode: 'form',
            views: [[false, 'form']],
            target: 'new'
        })
    }
}

registry.category("systray").add("vista_backend_theme.theme_widget", {
    Component: ThemeWidget
}, { sequence: 20 })