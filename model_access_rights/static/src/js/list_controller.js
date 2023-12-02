/** @odoo-module */
/**
 * This file will used to hide the selected options from the list view
 */
import ListController from 'web.ListController';
import { patch } from "@web/core/utils/patch";
import rpc from 'web.rpc';
patch(ListController.prototype, 'model_access_rights/static/src/js/list_controller.js.ListController', {
/**
* This function will used to hide the selected options from the list view
*/
    async willStart() {
        var self = this;
        var user_id = self.initialState.context.uid;
        var model = self.modelName;
        await rpc.query({model: 'access.right', method: 'hide_buttons',
            args: [[user_id, model]],
        }).then(function(data) {
            if(data){
                if(data['is_create_or_update']){
                    self.activeActions.create = false;
                    self.activeActions.edit = false;
                }
                if(data['is_delete']){
                    self.activeActions.delete = false;
                }
                if(data['is_archive']){
                    self.archiveEnabled = false;
                }
                if(data['is_export']){
                    self.isExportEnable = false;
                }
            }
        });
    },
});
