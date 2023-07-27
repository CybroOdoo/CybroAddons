/** @odoo-module **/
import {
    BlockUI
} from "@web/core/ui/block_ui";
import { patch } from "@web/core/utils/patch";
import { xml } from "@odoo/owl";
const { useState } = owl;
const rpc = require('web.rpc');
/**
 * Customization of BlockUI setup method to handle the loading spinner and message.
 */
patch(BlockUI.prototype, 'blockUi', {
    /**
     * Custom setup method.
     */
    setup() {
        this._super.apply(this, arguments);
        this.spin_state = useState({
            loader_style: ''
        });
        const self = this;
        rpc.query({
            model: 'ir.config_parameter',
            method: 'get_param',
            args: ['website_pre_loader_style.loader_style'],
        }).then(function(result) {
            self.spin_state.loader_style = result;
        });
    }
});
BlockUI.template = xml`
    <div t-att-class="state.blockUI ? 'o_blockUI fixed-top d-flex justify-content-center align-items-center flex-column vh-100 bg-black-50' : ''">
      <t t-if="state.blockUI">
        <div class="o_spinner mb-4">
            <img t-att-src="'website_pre_loader_style/static/src/img/' + this.spin_state.loader_style + '.png'" alt="Loading..."/>
        </div>
        <div class="o_message text-center px-4">
            <t t-esc="state.line1"/> <br/>
            <t t-esc="state.line2"/>
        </div>
      </t>
    </div>`;
