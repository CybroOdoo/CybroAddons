/** @odoo-module **/
import {BlockUI} from "@web/core/ui/block_ui";
import {ImportBlockUI} from "@base_import/import_block_ui";
import {patch} from "@web/core/utils/patch";
import {session} from "@web/session";

const {xml} = owl;

patch(BlockUI.prototype, {
    setup() {
        super.setup();
        this.loaderClass = session.loaderClass;
    },
});
BlockUI.template = xml`
    <t t-if="state.blockState === BLOCK_STATES.UNBLOCKED">
        <div/>
    </t>
    <t t-else="">
        <t t-set="visiblyBlocked" t-value="state.blockState === BLOCK_STATES.VISIBLY_BLOCKED"/>
        <div class="o_blockUI fixed-top d-flex justify-content-center align-items-center flex-column vh-100"
             t-att-class="visiblyBlocked ? '' : 'o_blockUI_invisible'">
            <t t-if="visiblyBlocked">
                <div class="o_spinner mb-4">
                    <t t-if="loaderClass and loaderClass != 'default'">
                        <a href="#" t-att-class="loaderClass"></a>
                    </t>
                    <t t-else="">
                        <img src="/web/static/img/spin.svg" alt="Loading..."/>
                    </t>
                </div>
                <div class="o_message text-center px-4">
                    <t t-esc="state.line1"/><br/>
                    <t t-esc="state.line2"/>
                </div>
            </t>
        </div>
    </t>
`;


patch(ImportBlockUI.prototype, {
    setup() {
        super.setup();
        this.loaderClass = session.loaderClass;
    },
});

ImportBlockUI.template = xml`
    <div class="o_blockUI fixed-top d-flex justify-content-center align-items-center flex-column vh-100 bg-black-50">
        <div class="o_spinner mb-4">
            <t t-if="loaderClass and loaderClass != 'default'">
                <a href="#" t-att-class="loaderClass"></a>
            </t>
            <t t-else="">
                <img src="/web/static/img/spin.svg" alt="Loading..."/>
            </t>
        </div>
        <div t-if="props.message or props.blockComponent">
            <div class="o_message text-center px-4" t-esc="props.message" />
            <t t-if="props.blockComponent" t-component="props.blockComponent.class" t-props="props.blockComponent.props"/>
        </div>
    </div>
`;
