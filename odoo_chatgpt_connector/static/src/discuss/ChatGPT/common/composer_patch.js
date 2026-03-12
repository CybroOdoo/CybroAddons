/** @odoo-module **/
import { registerComposerAction } from "@mail/core/common/composer_actions";
import { _t } from "@web/core/l10n/translation";
import { markEventHandled } from "@web/core/utils/misc";
import { ChatGPTPromptDialogBox } from "@odoo_chatgpt_connector/discuss/ChatGPT/common/chatgpt_prompt_dialog";

registerComposerAction("gpt-assist", {
    condition: ({ composer }) => !composer.message,
    icon: "fa fa-magic",
    name: _t("GPT Assist"),
    onSelected({ owner }, ev) {
        const dialogService = owner.env.services.dialog;
        dialogService.add(ChatGPTPromptDialogBox, {
            insert: (content) => {
                owner.props.composer.composerText += ` ${content.textContent}`;
            },
            sanitize: (fragment) => DOMPurify.sanitize(fragment, {
                IN_PLACE: true,
                ADD_TAGS: ["#document-fragment"],
                ADD_ATTR: ["contenteditable"],
            }),
        });
        markEventHandled(ev, "Composer.onClickGptAssist");
    },
    sequence:2,
    sequenceQuick: 2,
});