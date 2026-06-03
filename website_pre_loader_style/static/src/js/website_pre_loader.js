/** @odoo-module **/
import { WebsitePreview } from '@website/client_actions/website_preview/website_preview';
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { useState } from "@odoo/owl";

/**
 * Customization of BlockPreview setup method to handle the website preview style.
 */
patch(WebsitePreview.components.BlockPreview.prototype, {
    /**
     * Overrides the setup method to set the website preview style based on a configuration parameter.
     * @override
     */
    setup() {
        super.setup();
        this.rpc = useService("rpc");
        this.spin_state = useState({
            style: ''
        })
        this.rpc('/web/dataset/call_kw/ir.config_parameter/get_param', {
            model: 'ir.config_parameter',
            method: 'get_param',
            args: ['website_pre_loader_style.loader_style'],
            kwargs: {},
        }).then((result) => {
            this.spin_state.style = result;
        });
    }
});
