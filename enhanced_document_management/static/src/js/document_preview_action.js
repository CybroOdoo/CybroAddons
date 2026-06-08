/** @odoo-module */
import { registry } from "@web/core/registry";
import { Component, onMounted, useRef } from "@odoo/owl";
const actionRegistry = registry.category("actions");

class DocumentPreview extends Component {
    /**
     * Setup method
     */
    setup() {
        super.setup(...arguments);
        this.template_div = useRef("document_preview_template_content");
        this.template = this.props.action.params['body_html'];
        this.stamp = this.props.action.params['stamp'];
        onMounted(async () => {
            this.render_template();
            this.prevent_reload();
        });
    }
    /**
     * Method to render the template
     */
    render_template() {
        if (this.el && this.el.parentElement) {
            this.el.parentElement.classList.add('document_preview_action')
        }
        if (this.template_div.el) {
            if (localStorage.getItem("myContent")) {
                this.template_div.el.innerHTML = localStorage.getItem("myContent");
            }
            if (this.template) {
                this.template_div.el.innerHTML = this.template;
            }
        }
    }
    /**
     * Method to prevent reload and set the template contents into local storage
     */
    prevent_reload() {
        var self = this
        window.addEventListener('beforeunload', function (event) {
            /**
             * If method
             * @param {any} self.template_div.el
             */
            if (self.template_div.el) {
                localStorage.setItem("myContent", self.template_div.el.innerHTML);
            }
        });
    }
}
DocumentPreview.template = "DocumentPreviewTemplate";
actionRegistry.add('preview_document', DocumentPreview);
