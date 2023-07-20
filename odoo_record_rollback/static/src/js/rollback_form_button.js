/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { FormController } from "@web/views/form/form_controller";
import { useService } from "@web/core/utils/hooks";
var rpc = require('web.rpc');
const { onWillStart, useState } = owl;
patch(FormController.prototype, "rollback", {
     // Patched the form controller to control the rollback button in every record.
        setup(){
           this._super.apply();
           this.action = useService("action")
           this.values = useState({
                 val: []
           })
           onWillStart(async () => {
            var self = this
            await rpc.query({
            model: 'rollback.record',
            method: 'get_models',
            args: [[this.props.resModel]]
           }).then(result => {
                const val = result;
                self.values.val = val;
                })
        });
        },
        rollbackButtonClicked(){
        //  To show the history of edited record
            const resId = this.__owl__.component.props.resId
            const resModel = this.__owl__.component.props.resModel
            this.action.doAction({
                type: 'ir.actions.act_window',
                name: 'Roll Back Records',
                view_mode: 'list',
                views:[[false,"list"]],
                res_model: 'rollback.record',
                target: 'new',
                context: "{'create' : False}",
                domain: [["record", "=", resId], ["res_model", "=", resModel]]
            })
        }
});