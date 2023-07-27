/** @odoo-module **/
import { WebsitePreview } from '@website/client_actions/website_preview/website_preview';
import { patch } from "@web/core/utils/patch";
const { useState } = owl;
const rpc = require('web.rpc');
var self = this;
/**
 * Customization of BlockPreview setup method to handle the website preview style.
 */
patch(WebsitePreview.components.BlockPreview.prototype, 'website_preview_style', {
    /**
     * Overrides the setup method to set the website preview style based on a configuration parameter.
     * @override
     */
    setup() {
        this._super(...arguments);
        this.spin_state = useState({
            style: ''
        })
        const self = this;
        rpc.query({
            model: 'ir.config_parameter',
            method: 'get_param',
            args: ['website_pre_loader_style.loader_style'],
        }).then(function(result) {
            self.spin_state.style = result
        })
    }
});
