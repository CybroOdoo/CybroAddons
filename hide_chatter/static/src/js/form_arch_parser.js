/** @odoo-module */
//Hide chatter by checking models
import { patch } from "@web/core/utils/patch";
import { Chatter } from "@mail/chatter/web_portal/chatter";
import { useService } from "@web/core/utils/hooks";
import  {onMounted} from "@odoo/owl";
const ChatterPatch = {
    async setup() {
        super.setup(...arguments);
        const orm = useService("orm")
        onMounted(async () => {
        const modelIdsConfigKey = "hide_chatter.model_ids";
            try {
                // Fetch the list of model names from the configuration parameter
                const response = await this.orm.call("ir.config_parameter", "get_param", [
                    "hide_chatter.model_ids",
                ])
                const model = await orm.search("ir.model",[["model", "=", this.env.model.root.resModel]],{ limit: 1 })
                const modelsToHideChatter = response
                if (
                    response &&
                    response.includes(model)
                ) {
                this.rootRef.el.parentElement.classList.add("d-none")
                }
            } catch (error) {
                console.error("Error fetching configuration parameter:", error);
            }
        })
    }
};
patch(Chatter.prototype, ChatterPatch);
