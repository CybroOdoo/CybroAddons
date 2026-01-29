/** @odoo-module **/
import { BlockUI } from "@web/core/ui/block_ui";

import { patch } from 'web.utils';
import session from 'web.session';
const { tags } = owl;

patch(BlockUI.prototype, "/backend_theme_infinito/static/src/js/loaders.js", {
  setup() {
    /**
     * @override 
     */
    this._super();
    this.loaderClass = session.loaderClass;
  },
});

BlockUI.template = tags.xml`
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
