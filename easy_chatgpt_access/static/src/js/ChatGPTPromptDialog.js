/** @odoo-module */
import { ChatGPTTranslateDialog } from "@html_editor/main/chatgpt/chatgpt_translate_dialog";

// Default props are extended to include a 'systray' object with an 'insert' property set to true.
ChatGPTTranslateDialog.props = {
    ...ChatGPTTranslateDialog.props,
    systray: { type: Object, optional: true },
};

ChatGPTTranslateDialog.defaultProps = {
    ...ChatGPTTranslateDialog.defaultProps,
    systray: {
        insert: true,
    },
};
