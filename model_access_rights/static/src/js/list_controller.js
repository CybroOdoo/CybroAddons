/** @odoo-module */
/**
 * This file will used to hide the selected options from the list view
 */
import ListController from 'web.ListController';
import { patch } from "@web/core/utils/patch";
import rpc from 'web.rpc';
import { useService } from "@web/core/utils/hooks";
import session from 'web.session';

patch(ListController.prototype, 'model_access_rights/static/src/js/list_controller.js.ListController', {
/**
* This function will used to hide the selected options from the list view
*/
    async willStart() {
        var self = this;
        var user_id = self.initialState.context.uid;
        var model = self.modelName;
        await rpc.query({model: 'access.right', method: 'hide_buttons',
            args: [],
        }).then(function(result) {
            for (var i = 0; i < result.length; i++) {
                var group = result[i].module + "." + result[i].group_name
                if (self.modelName == result[i].model) {
                    if (result[i].restriction_type == "group") {
                        if (session.user_has_group(group)) {
                            if (!session.is_admin) {
                                if (result[i].is_create_or_update) {
                                    self.activeActions.create = false;
                                }
                                if (result[i].is_export) {
                                    self.isExportEnable = false
                                    self.isExportEnable = false
                                }
                                if (result[i].is_delete) {
                                    self.activeActions.delete = false;
                                }
                            }
                        }
                    } else {
                        if (user_id == result[i].user[0]) {
                            if (!this.user.isAdmin) {
                                if (result[i].is_create_or_update) {
                                    self.activeActions.create = false;
                                }
                                if (result[i].is_export) {
                                    self.isExportEnable = false
                                    self.isExportEnable = false
                                }
                                if (result[i].is_delete) {
                                    self.activeActions.delete = false;
                                }
                            }
                        }
                    }
                }
            }
        });
    },
});
