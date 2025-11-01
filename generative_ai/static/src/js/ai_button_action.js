/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { rpc } from "@web/core/network/rpc";
import { Component, xml, useRef, useState } from "@odoo/owl";
import { AddSnippetDialog } from "@web_editor/js/editor/add_snippet_dialog";


// Define a custom Owl component for the AI Prompt Modal
class AIPromptModal extends Component {
    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.textAreaRef = useRef('textAreaRef');
        this.nameRef = useRef('snippetNameRef');
        this.state = useState({
            isLoading: false,
        });
    }
    // Close the modal (disabled if a request is loading)
    onClose() {
        if (this.state.isLoading) {
            return;
        }
        this.props.close();
    }
    async onSubmit() {
        const promptValue = this.textAreaRef.el.value;
        const snippetName = this.nameRef.el.value;

        if (!promptValue || !snippetName) {
            this.notification.add(
                "Please fill in both the prompt and snippet name",
                { type: "warning" }
            );
            return;
        }
        try {
            this.state.isLoading = true;
            const result = await rpc('/website/generate_snippet', {
                prompt: promptValue,
                name: snippetName
            });
            if (result.error) {
                this.notification.add(result.error, { type: "danger" });
            } else {
                this.notification.add(
                    "Snippet generated successfully! Refreshing snippet panel...",
                    { type: "success" }
                );
                window.location.reload();
            }
        } catch (error) {
            this.notification.add(
                "Failed to generate snippet: " + error,
                { type: "danger" }
            );
        } finally {
            this.state.isLoading = false;
        }
        this.props.close();
    }
}

// Define the template for the modal
AIPromptModal.template = xml`
    <div class="modal o_technical_modal d-block" tabindex="-1" role="dialog">
        <div class="modal-dialog" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Generate Snippet with AI</h5>
                    <button type="button" class="btn-close" t-att-disabled="state.isLoading" t-on-click="onClose" aria-label="Close"/>
                </div>
                <div class="modal-body">
                    <div class="form-group mb-3">
                        <label for="snippet-name" class="form-label">Snippet Name</label>
                        <input type="text" id="snippet-name" class="form-control" t-ref="snippetNameRef"
                               t-att-disabled="state.isLoading" placeholder="Enter a name for your snippet"/>
                    </div>
                    <div class="form-group">
                        <label for="ai-prompt" class="form-label">Enter your prompt here...</label>
                        <textarea id="ai-prompt" class="form-control" rows="3" t-ref="textAreaRef"
                                 t-att-disabled="state.isLoading"/>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" t-att-disabled="state.isLoading" t-on-click="onClose">Cancel</button>
                    <button type="button" class="btn btn-primary" t-att-disabled="state.isLoading" t-on-click="onSubmit">
                        <t t-if="state.isLoading">
                            <span class="fa fa-spinner fa-spin me-1"></span>
                            Generating...
                        </t>
                        <t t-else="">Generate</t>
                    </button>
                </div>
            </div>
        </div>
    </div>
`;

// Patch the AddSnippetDialog to add the AI prompt dialog on click
const originalSetup = AddSnippetDialog.prototype.setup;
patch(AddSnippetDialog.prototype, {
    setup() {
        originalSetup.call(this);
        this.dialog = useService("dialog");
    },
    async _onGenerateClick() {
        this.dialog.add(AIPromptModal, {
            onClose: () => {
                // Refresh the snippets panel after closing
                this.render();
            }
        });
    }
});
