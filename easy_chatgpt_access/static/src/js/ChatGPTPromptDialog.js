/** @odoo-module **/
import { ChatGPTPromptDialog } from '@web_editor/js/wysiwyg/widgets/chatgpt_prompt_dialog';
//Default props are extended to include a 'systray' object with an 'insert' property set to true.
ChatGPTPromptDialog.defaultProps = {
    ...ChatGPTPromptDialog.defaultProps,
    systray: {
        insert: true,
    }
}
ChatGPTPromptDialog.props = {
    ...ChatGPTPromptDialog.props,
    systray: { type: Object, optional: true },
}
