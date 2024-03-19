/** @odoo-module **/
import { Composer } from "@mail/core/common/composer";
import { useService } from "@web/core/utils/hooks";
import { patch } from "@web/core/utils/patch";
import { ChatGPTPromptDialog } from '@web_editor/js/wysiwyg/widgets/chatgpt_prompt_dialog';
/**
 * Composer Patch Object
 * Extends the Composer class with additional functionality.
 */
const composerPatch = {
    /**
     * Setup method to initialize additional properties and services.
     */
    setup() {
        super.setup();
        this.dialogService = useService("dialog");
    },
    /**
     * onClickGPT method triggered on GPT button click.
     * Opens a dialog for GPT interaction and appends the content to the composer's text input.
     */
    onClickGPT(ev){
        this.dialogService.add(ChatGPTPromptDialog, {
            insert: content => {
                const currentInputValue = this.props.composer.textInputContent
                const appendedValue = currentInputValue + ' ' + $(content)[0].textContent;
                this.props.composer.textInputContent = appendedValue
            }
        });
    },
}
// Apply the patch to the Composer class
patch(Composer.prototype, composerPatch);
