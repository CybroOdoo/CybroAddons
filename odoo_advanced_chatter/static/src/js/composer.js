/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { Composer } from "@mail/components/composer/composer";
import { _t } from 'web.core';
import { useService } from "@web/core/utils/hooks";
patch(Composer.prototype, 'chatter_recipients',{
    setup() {
    this._super();
        this.orm = useService('orm')
        var userId = this.env.searchModel.userService.userId
        this.orm.call(
        'mail.wizard.recipient',
        'get_user',
        [userId]
    )
    },
    replyTo() {
        var userId = this.env.searchModel.userService.userId
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
                default_partner_id:userId,
            },
        }
            this.env.services.action.doAction(action, {})
    }
})
