/** @odoo-module */
/**
 * This file will used to hide the selected options from the kanban view
 */
import KanbanController from 'web.KanbanController';
import { patch } from "@web/core/utils/patch";
import rpc from 'web.rpc';
import session from 'web.session';
patch(KanbanController.prototype, 'model_access_rights/static/src/js/kanban_controller.js.KanbanController', {
/**
* This function will used to hide the selected options from the kanban view
*/

    async willStart() {
        var self = this;
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
//                                    self.props.archInfo.activeActions.create = false
//                                    self.props.archInfo.activeActions.edit = false
                                    this.is_action_enabled('edit')= false
                                    this.is_action_enabled('create')= false
                                }
                                if (result[i].is_delete) {
                                    self.props.archInfo.activeActions.delete = false
                                }
                            }
                        }
                    } else {
                        if (user_id == result[i].user[0]) {
                            if (!self.user.isAdmin) {
                                if (result[i].is_create_or_update) {
                                    self.props.archInfo.activeActions.create = false
                                    self.props.archInfo.activeActions.edit = false
                                }
                                if (result[i].is_delete) {
                                    self.props.archInfo.activeActions.delete = false
                                }
                            }
                        }
                    }

                }
            }
        });
    },
});
