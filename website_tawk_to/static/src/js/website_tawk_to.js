/** @odoo-module **/
import { WebClient } from "@web/webclient/webclient";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart } from "@odoo/owl";

patch(WebClient.prototype,{
    /**
     * Setup method for the WebClient prototype
     */
    setup() {
        super.setup();
        this.orm = useService("orm");
        this.state.tawk = null;
        /**
         * onWillStart hook to perform actions before the component is mounted
         */
        onWillStart(async () => {
            const property = await this.orm.call("ir.config_parameter", "get_param", ["website_tawk_to.property_id"])
            const widget = await this.orm.call("ir.config_parameter", "get_param", ["website_tawk_to.widget_id"])
            this.state.property = property
            this.state.widget = widget
        })
    },
});
