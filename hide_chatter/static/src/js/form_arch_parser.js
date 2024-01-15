/** @odoo-module */
//Hide chatter by checking models
import { patch } from "@web/core/utils/patch";
import { Chatter } from "@mail/core/web/chatter";
import { useService } from "@web/core/utils/hooks";
import  {onMounted} from "@odoo/owl";
const ChatterPatch = {
    async setup() {
        super.setup(...arguments);
        const rpc = useService("rpc")
        onMounted(async () => {
         const modelIdsConfigKey = "hide_chatter.model_ids";
        try {
            // Fetch the list of model names from the configuration parameter
            const response = await this.orm.call("ir.config_parameter", "get_param", [
                "hide_chatter.model_ids",
            ])
            const model = await rpc('/web/dataset/call_kw', {
                model: "ir.model",
                method: "search",
                args: [[["model", "=", this.env.model.root.resModel]]],
                kwargs: { limit: 1 },})
            const modelsToHideChatter = response
            if (
                response &&
                response.includes(model)
            ) {
            this.rootRef.el.classList.add("d-none")
            }
        } catch (error) {
            console.error("Error fetching configuration parameter:", error);
        }
    })
     }
};
patch(Chatter.prototype, ChatterPatch);
