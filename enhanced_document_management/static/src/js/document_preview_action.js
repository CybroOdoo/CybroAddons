/** @odoo-module */
import { registry } from "@web/core/registry";
import { onMounted, useRef } from "@odoo/owl";
const actionRegistry = registry.category("actions");

class DocumentPreview extends owl.Component {
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
    render_template() {
        /* Method to render the template*/
        this.__owl__.bdom.el.parentElement.classList.add('document_preview_action')
        if (localStorage.getItem("myContent")) {
            this.template_div.el.innerHTML = localStorage.getItem("myContent");
        }
        if (this.template) {
            this.template_div.el.innerHTML = this.template;
        }
    }
    prevent_reload() {
        /* Method to prevent reload and set the template contents into local storage */
        var self = this
        window.addEventListener('beforeunload', function (event) {
            if (self.template_div.el) {
                localStorage.setItem("myContent", self.template_div.el.innerHTML);
            }
        });
    }
}
DocumentPreview.template = "DocumentPreviewTemplate";
actionRegistry.add('preview_document', DocumentPreview);
