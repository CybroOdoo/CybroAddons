/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { FormController } from "@web/views/form/form_controller";
import { useService } from "@web/core/utils/hooks";
import { jsonrpc } from "@web/core/network/rpc_service";
import {onRendered,useState} from "@odoo/owl";

patch(FormController.prototype, {
     // Patched the form controller to control the rollback button in every record.
        setup() {
        super.setup(...arguments);
           this.action = useService("action")
           this.values = useState({
                 val: []
           })
           onRendered(async() => {
            var self = this
            const data = await jsonrpc('/web/dataset/call_kw', {
            model: 'rollback.record',
            method: 'get_models',
            args: [[this.props.resModel]],
             kwargs: {},
           }).then(result => {
                const val = result;
                self.values.val = val;
                })
        });
        },
        rollbackButtonClicked(){
        //  To show the history of edited record
            const resId = this.model.config.resId
            const resModel = this.props.resModel
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