/** @odoo-module **/

import { registry } from "@web/core/registry";
import { formView } from "@web/views/form/form_view";
import { FormController } from "@web/views/form/form_controller";
import { onWillStart } from "@odoo/owl";

export class InformationArticleFormController extends FormController {
    setup() {
        super.setup();
        onWillStart(async () => {
            if (this.props.resId) {
                try {
                    this.actionService.doAction("info_hub.action_info_client", {
                        additionalContext: {
                            active_id: this.props.resId,
                        },
                        props: {
                            resId: this.props.resId,
                        },
                        stackPosition: "replaceCurrentAction",
                    });
                } catch (error) {
                    console.error("Failed to redirect existing article to client action:", error);
                }
            } else {
                try {
                    const vals = {
                        name: "Untitled",
                    };
                    const context = this.props.context || {};
                    if (context.default_parent_id) {
                        vals.parent_id = context.default_parent_id;
                    }
                    if (context.default_category) {
                        vals.category = context.default_category;
                    } else if (context.category) {
                        vals.category = context.category;
                    } else {
                        vals.category = "private";
                    }
                    if (context.default_is_template !== undefined) {
                        vals.is_template = context.default_is_template;
                    }

                    const newArticleId = await this.orm.create("info.hub.article", [vals]);
                    this.actionService.doAction("info_hub.action_info_client", {
                        additionalContext: {
                            active_id: newArticleId,
                            new_article_created: true,
                        },
                        props: {
                            resId: newArticleId,
                        },
                        stackPosition: "replaceCurrentAction",
                    });
                } catch (error) {
                    console.error("Failed to auto-create and redirect new article:", error);
                }
            }
        });
    }
}

export const infoArticleFormView = {
    ...formView,
    Controller: InformationArticleFormController,
};

registry.category("views").add("info_article_form", infoArticleFormView);
