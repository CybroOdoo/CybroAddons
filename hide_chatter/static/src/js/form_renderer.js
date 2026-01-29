/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import FormRenderer from 'web.FormRenderer';
var rpc = require('web.rpc');
/**Patched FormRender for hide chatter.*/
patch(FormRenderer.prototype, "parse", {
    /** The function to render the chatter once the form view is rendered.**/
    _renderNode(node) {
        const parsedResult = this._super.apply(this, arguments);
        if (node.tag === 'div' && node.attrs.class === 'oe_chatter') {
            rpc.query({
                model: "ir.model",
                method: "search",
                args: [[["model", "=", this.state.model]]],
                kwargs: { limit: 1 },
            }).then((result) => {
                const resModelId = result;
                rpc.query({
                    model: "ir.config_parameter",
                    method: "get_param",
                    args: ["chatter_enable.model_ids"],
                }).then((result) => {
                    const modelIds = JSON.parse(result);
                    if (modelIds){
                        if (modelIds.includes(resModelId[0])) {
                            if (this._chatterContainerTarget) {
                                this._chatterContainerTarget.style.display = 'none';
                            }
                        }
                    }
                })
            })
        }
        return parsedResult;
    },
});
