/** @odoo-module **/
/**
 * Editor option of the Petzen live snippets: empty the live part of the block before the
 * page is saved, so only the editable heading is stored and the data stays dynamic.
 */
import options from "@web_editor/js/editor/snippets.options";

options.registry.PetzenDynamicBlock = options.Class.extend({
    cleanForSave() {
        this.$target[0].querySelector(".pz-dynamic-body")?.replaceChildren();
    },
});
