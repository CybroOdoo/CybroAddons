/** @odoo-module **/
// Import necessary components from the Odoo web core library
import { BlockUI } from "@web/core/ui/block_ui";
import { patch } from "@web/core/utils/patch";
import { session } from "@web/session";
const { xml } = owl;

// Patch the BlockUI component to customize loading spinner
patch(BlockUI.prototype, {
  setup() {
    // Call the setup method of the parent class
    super.setup();
    // Assign the loader class from session settings
    this.loaderClass = session.loaderClass;
  },
});
// Define the template for the BlockUI component
BlockUI.template = xml`
    <div t-att-class="state.blockUI ? 'o_blockUI' : ''">
      <t t-if="state.blockUI">
        <div class="o_spinner">
        <t t-if="loaderClass != 'default'">
            <a href ="#" t-att-class="loaderClass"></a>
        </t>
        <t t-else="">
            <img src="/web/static/img/spin.png" alt="Loading..."/>
        </t>
        </div>
        <div class="o_message">
            <t t-raw="state.line1"/> <br/>
            <t t-raw="state.line2"/>
        </div>
      </t>
    </div>`;
