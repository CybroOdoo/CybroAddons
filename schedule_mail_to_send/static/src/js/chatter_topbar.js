import { Chatter } from "@mail/chatter/web_portal_project/chatter";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";

patch(Chatter.prototype, {
    /**
     * @override
     * @param {Event} ev
     */
    async onClickScheduleMail(ev) {
        let thread = this.thread?.() || this.state?.thread;
        if (!thread?.id) {
            if (this.webChatterProps?.saveRecord) {
                const saved = await this.webChatterProps.saveRecord();
                if (!saved) {
                    return;
                }
                if (this.webChatterProps.record) {
                    await this.webChatterProps.record.load?.();
                }
            }
            thread = this.thread?.() || this.state?.thread;
        }

        const threadId =
            thread?.id ||
            this.threadId?.() ||
            this.props?.threadId ||
            this.webChatterProps?.record?.resId;
        const threadModel =
            thread?.model ||
            this.threadModel?.() ||
            this.props?.threadModel ||
            this.webChatterProps?.record?.resModel;

        const parsedId = parseInt(threadId, 10);
        if (!parsedId || isNaN(parsedId) || !threadModel) {
            return;
        }

        const followersList = (thread?.followers || [])
            .map((follower) => follower.partner?.id)
            .filter(Boolean);

        const action = {
            type: "ir.actions.act_window",
            res_model: "mail.compose.message",
            view_mode: "form",
            views: [[false, "form"]],
            name: _t("Schedule Mail"),
            target: "new",
            context: {
                default_model: threadModel,
                default_res_model: threadModel,
                default_res_id: parsedId,
                default_res_ids: [parsedId],
                default_partner_ids: followersList,
                default_composition_mode: "comment",
                active_model: threadModel,
                active_id: parsedId,
                active_ids: [parsedId],
            },
        };
        this.env.services.action.doAction(action);
    },
});
