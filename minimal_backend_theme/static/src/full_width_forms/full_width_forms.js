import { registry } from "@web/core/registry";
import { useBus } from "@web/core/utils/hooks";
import { patch } from "@web/core/utils/patch";
import { render } from "@web/owl2/utils";
import { FormRenderer } from "@web/views/form/form_renderer";
import { getOption, themeBus } from "../theme_settings";

/**
 * Full-width forms: on wide screens Odoo puts the chatter beside the form
 * (Discuss's "SIDE_CHATTER" layout), which leaves the form only part of the
 * screen. With the option on, the chatter goes below the form instead, as it
 * does on smaller screens. The attachment preview layout ("COMBO") is kept.
 */
const BELOW_INSTEAD_OF_ASIDE = {
    SIDE_CHATTER: "BOTTOM_CHATTER",
    EXTERNAL_COMBO_XXL: "EXTERNAL_COMBO",
};

/**
 * The chatter layout (FormRenderer.mailLayout) comes from Discuss (mail),
 * which the theme does not depend on. So the patch is applied when the web
 * client starts, once every installed module's code is loaded: then it can
 * tell whether Discuss is there, and wraps its method whatever the order in
 * which the modules' assets were bundled.
 */
registry.category("services").add("minimal_backend_theme.full_width_forms", {
    start() {
        if (typeof FormRenderer.prototype.mailLayout !== "function") {
            return; // Discuss not installed: no chatter to move
        }
        patch(FormRenderer.prototype, {
            setup() {
                super.setup();
                // Switching the option from Quick settings applies to the open form.
                useBus(themeBus, "OPTION-CHANGED", ({ detail }) => {
                    if (detail.key === "full_width") {
                        render(this);
                    }
                });
            },

            mailLayout(hasAttachmentContainer) {
                const layout = super.mailLayout(hasAttachmentContainer);
                if (getOption("full_width")) {
                    return BELOW_INSTEAD_OF_ASIDE[layout] || layout;
                }
                return layout;
            },
        });
    },
});
