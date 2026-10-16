import { patch } from "@web/core/utils/patch";
import { WebsiteBuilderClientAction } from "@website/client_actions/website_preview/website_builder_action";

patch(WebsiteBuilderClientAction.prototype, {
    async addWelcomeMessage() {
        await super.addWelcomeMessage(...arguments);
        this.welcomeMessageEl?.classList.add("o_homepage_editor_welcome_message", "h-100");
    },
});
