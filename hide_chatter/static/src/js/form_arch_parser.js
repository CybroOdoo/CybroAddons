/** @odoo-module */
//Hide chatter by checking models
import { patch } from "@web/core/utils/patch";
import { Chatter } from "@mail/chatter/web_portal_project/chatter";
import { useService } from "@web/core/utils/hooks";
import { onMounted } from "@odoo/owl";
const ChatterPatch = {
    setup() {
        super.setup(...arguments);
        const orm = useService("orm");
        onMounted(async () => {
            // Fetch the models whose chatter should be hidden. The lookup runs
            // with sudo on the server so it works for every user.
            const hiddenModels = await orm.call(
                "ir.model", "get_hidden_chatter_models", []
            );
            if (hiddenModels.includes(this.threadModel())) {
                this.rootRef().parentElement.classList.add("d-none");
            }
        });
    }
};
patch(Chatter.prototype, ChatterPatch);
