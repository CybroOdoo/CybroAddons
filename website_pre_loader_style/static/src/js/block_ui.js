/** @odoo-module **/
import {
    BlockUI
} from "@web/core/ui/block_ui";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { useState, xml } from "@odoo/owl";

/**
 * Customization of BlockUI setup method to handle the loading spinner and message.
 */
patch(BlockUI.prototype, {
    /**
     * Custom setup method.
     */
    setup() {
        super.setup();
        this.rpc = useService("rpc");
        this.spin_state = useState({
            enabled: true,
            loader_style: 'dual'
        });
        this.rpc('/website_pre_loader_style/loader_config', {}).then((result) => {
            this.spin_state.enabled = result.enabled;
            this.spin_state.loader_style = result.loader_style || 'dual';
        }).catch(() => {});
    }
});

BlockUI.template = xml`
    <div t-att-class="state.blockUI ? 'o_blockUI fixed-top d-flex justify-content-center align-items-center flex-column vh-100 bg-black-50' : ''">
      <t t-if="state.blockUI">
        <div t-if="this.spin_state.enabled" class="o_spinner mb-4">
            <img t-att-src="'/website_pre_loader_style/static/src/img/' + this.spin_state.loader_style + '.png'" alt="Loading..."/>
        </div>
        <div class="o_message text-center px-4">
            <t t-esc="state.line1"/> <br/>
            <t t-esc="state.line2"/>
        </div>
      </t>
    </div>`;
