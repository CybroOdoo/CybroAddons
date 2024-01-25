/** @odoo-module */
/**
 * This file will used to hide the selected options from the list view
 */
import { ListController} from '@web/views/list/list_controller';
import { patch} from "@web/core/utils/patch";
const {onWillStart} = owl;
patch(ListController.prototype, {
/**
 * This function will used to hide the selected options from the list view
 */
    setup() {
        super.setup(...arguments);
        this.rpc = this.env.services.rpc
        onWillStart(async () => {
            var self = this
            var result;
            result = await this.env.services.orm.silent.call(
                "access.right",
                "hide_buttons",
            );
            for (var i = 0; i < result.length; i++) {
                var group = result[i].module + "." + result[i].group_name
                if (self.props.resModel == result[i].model) {
                    if (await self.userService.hasGroup(group)) {
                        if (!this.userService.isAdmin) {
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
        });
    }
});
