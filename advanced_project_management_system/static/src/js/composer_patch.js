/* @odoo-module */
import { Composer } from "@mail/core/common/composer";
import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";

patch(Composer.prototype, {
    get placeholder() {
        if (this.thread && this.thread.model !== "discuss.channel" && !this.props.placeholder) {
            if (this.props.type === "message") {
                return _t("Send a message to followers…");
            }else if(this.props.type === "comment") {
                return _t("Add a comment here…");
            } else {
                return _t("Log an internal note…");
            }
        }
        return super.placeholder;
    },
    get SEND_TEXT() {
        return this.props.type === "note" ? _t("Log") : this.props.type === "message" ? _t("Send") : _t("Comment");
    },
    async sendMessage() {
        await this.processMessage(async (value) => {
            const postData = {
                attachments: this.props.composer.attachments,
                isNote: this.props.type === "note" || this.props.type === "comment",
                mentionedChannels: this.props.composer.mentionedChannels,
                mentionedPartners: this.props.composer.mentionedPartners,
                cannedResponseIds: this.props.composer.cannedResponses.map((c) => c.id),
                parentId: this.props.messageToReplyTo?.message?.id,
            };
            await this._sendMessage(value, postData);
        });
    }
});
