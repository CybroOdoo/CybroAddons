/** @odoo-module **/
import { Chatter } from "@mail/core/web/chatter";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";
//patch the class ChatterContainer to added the click function
patch(Chatter.prototype ,{
    setup() {
        super.setup();
        this.orm = useService("orm");
        this.orm.call(
            'mail.wizard.recipient',
            'get_user',
            [this.env.model.user.userId]
        );
    },
    replyTo(){
    //-----On clicking thr reply to icon a wizard is opened to select the recipient
        const action = {
            type: "ir.actions.act_window",
            res_model: "mail.wizard.recipient",
            view_mode: "form",
            views: [[false, "form"]],
            name: _t("Reply To"),
            target: "new",
            context: {
                default_model: this.props.threadModel,
                default_model_reference: this.props.threadId,
                default_partner_id:this.env.model.user.userId,
            },
        }
            this.action.doAction(action, {})
    }
});
