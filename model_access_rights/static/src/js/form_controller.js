/** @odoo-module */
/**
 * This file will used to hide the selected options from the form view
 */
import { FormController} from "@web/views/form/form_controller";
import { patch} from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
var rpc = require('web.rpc');
const { onWillStart} = owl;
patch(FormController.prototype, 'model_access_rights/static/src/js/form_controller.js.FormController', {
/**
 * This function will used to hide the selected options from the form view
 */
    setup() {
        this._super();
        this.user = useService("user");
        onWillStart(async () => {
            var self = this
            var result;
            await rpc.query({
                model: 'access.right',
                method: 'hide_buttons',
            }).then(function(data) {
                result = data;
            });
            for (var i = 0; i < result.length; i++) {
                var group = result[i].module + "." + result[i].group_name
                if (self.props.resModel == result[i].model) {
                    if (result[i].restriction_type == "group") {
                        if (await self.user.hasGroup(group)) {
                            if (!this.user.isAdmin) {
                                if (result[i].is_create_or_update) {
                                    self.canCreate = false
                                }
                                if (result[i].is_delete) {
                                    this.archInfo.activeActions.delete = false
                                }
                            }
                        }
                    } else {
                        if (await self.user.userId == result[i].user[0]) {
                            if (!this.user.isAdmin) {
                                if (result[i].is_create_or_update) {
                                    self.canCreate = false
                                }
                                if (result[i].is_delete) {
                                    this.archInfo.activeActions.delete = false
                                }
                            }
                        }
                    }
                }
            }
        });
    }
});
