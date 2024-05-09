/** @odoo-module **/
import { WebClient } from "@web/webclient/webclient";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
const { useState } = owl;

patch(WebClient.prototype, "webclient_patch", {
    async setup() {
        var self= this
        this._super.apply(this, arguments);
        this.state = useState({
            widget: false,
            property: false,
        });
        this.orm = useService("orm");
        this.tawk = null;
        const data = await this.orm.call("res.config.settings",
                "get_tawk_to_credential",[""] )
        self.state.property = data['property_id']
        self.state.widget = data['widget_id']

    },
})
