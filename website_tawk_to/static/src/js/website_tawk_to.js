/** @odoo-module **/
import { WebClient } from "@web/webclient/webclient";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
const { Component, onWillStart } = owl;

patch(WebClient.prototype, "webclient_patch", {
    //super the setup and on onWillStart get the values from the settings
    setup() {
        this._super.apply(this, arguments);
        this.orm = useService("orm");
        this.state.tawk = null;
        onWillStart(async () => {
            const property = await this.orm.call("ir.config_parameter", "get_param", ["website_tawk_to.property_id"])
            const widget = await this.orm.call("ir.config_parameter", "get_param", ["website_tawk_to.widget_id"])
            this.state.property = property
            this.state.widget = widget
        })
    },
})
