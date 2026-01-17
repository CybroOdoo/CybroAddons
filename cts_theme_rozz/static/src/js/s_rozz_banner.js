/** @odoo-module **/
import { SnippetOption } from "@web_editor/js/editor/snippets.options";

export class OdometerOptions extends SnippetOption {
    // Handle live counter updates for each input
    onChangeExpCount(value) {
        this.$target.attr("data-exp-count", value);
    }
    onChangeHappyCount(value) {
        this.$target.attr("data-happy-count", value);
    }
    onChangeProjectCount(value) {
        this.$target.attr("data-project-count", value);
    }
    onChangeActiveCount(value) {
        this.$target.attr("data-active-count", value);
    }
}
