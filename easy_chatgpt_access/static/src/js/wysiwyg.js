/** @odoo-module **/
import * as OdooEditorLib from "@web_editor/js/editor/odoo-editor/src/OdooEditor";
import { Wysiwyg } from "@web_editor/js/wysiwyg/wysiwyg";
import { patch } from "@web/core/utils/patch";
import { ChatGPTPromptDialog } from '@web_editor/js/wysiwyg/widgets/chatgpt_prompt_dialog';
import { ChatGPTAlternativesDialog } from '@web_editor/js/wysiwyg/widgets/chatgpt_alternatives_dialog';
import { _t } from "@web/core/l10n/translation";

const preserveCursor = OdooEditorLib.preserveCursor;
const closestElement = OdooEditorLib.closestElement;
/**
 * Patch method for modifying the setup and openChatGPTDialog functions of the Wysiwyg class.
 * Modifies the setup function to include functionality for handling the opening of the dialog based on the 'openPrompt' prop.
 * Modifies the openChatGPTDialog function to include systray options from the component's props in the parameters for opening the dialog.
 */
patch(Wysiwyg.prototype, {
    // Extends the setup method of the superclass and adds functionality to handle the opening
    // of the dialog based on the 'openPrompt' prop.
    setup() {
        super.setup(...arguments);
        owl.useEffect((openPrompt) => {
            if (openPrompt) {
                this.openChatGPTDialog()
            }
        }, () => [this.props.options?.openPrompt])
    },
    // Modifies this function for loading the dialog box from systray icon
    openChatGPTDialog(mode = 'prompt') {
        const restore = preserveCursor(this.odooEditor.document);
        const params = {
            insert: content => {
                this.odooEditor.historyPauseSteps();
                const insertedNodes = this.odooEditor.execCommand('insert', content);
                this.odooEditor.historyUnpauseSteps();
                this.notification.add(_t('Your content was successfully generated.'), {
                    title: _t('Content generated'),
                    type: 'success',
                });
                this.odooEditor.historyStep();
                // Add a frame around the inserted content to highlight it for 2
                // seconds.
                const start = insertedNodes?.length && closestElement(insertedNodes[0]);
                const end = insertedNodes?.length && closestElement(insertedNodes[insertedNodes.length - 1]);
                if (start && end) {
                    const divContainer = this.odooEditor.editable.parentElement;
                    let [parent, left, top] = [start.offsetParent, start.offsetLeft, start.offsetTop - start.scrollTop];
                    while (parent && !parent.contains(divContainer)) {
                        left += parent.offsetLeft;
                        top += parent.offsetTop - parent.scrollTop;
                        parent = parent.offsetParent;
                    }
                    let [endParent, endTop] = [end.offsetParent, end.offsetTop - end.scrollTop];
                    while (endParent && !endParent.contains(divContainer)) {
                        endTop += endParent.offsetTop - endParent.scrollTop;
                        endParent = endParent.offsetParent;
                    }
                    const div = document.createElement('div');
                    div.classList.add('o-chatgpt-content');
                    const FRAME_PADDING = 3;
                    div.style.left = `${left - FRAME_PADDING}px`;
                    div.style.top = `${top - FRAME_PADDING}px`;
                    div.style.width = `${Math.max(start.offsetWidth, end.offsetWidth) + (FRAME_PADDING * 2)}px`;
                    div.style.height = `${endTop + end.offsetHeight - top + (FRAME_PADDING * 2)}px`;
                    divContainer.prepend(div);
                    setTimeout(() => div.remove(), 2000);
                }
            },
        };
        if (mode === 'alternatives') {
            params.originalText = this.odooEditor.document.getSelection().toString() || '';
        }
        // If systray options are provided in the component's props, they are included
        // in the parameters for opening the dialog.
        if (this.props.options.systray){
            params.systray = this.props.options.systray
        }
        this.odooEditor.document.getSelection().collapseToEnd();
        this.env.services.dialog.add(
            mode === 'prompt' ? ChatGPTPromptDialog : ChatGPTAlternativesDialog,
            params,
            { onClose: restore },
        );
    }
})
