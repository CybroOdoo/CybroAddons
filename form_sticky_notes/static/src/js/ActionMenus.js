/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { ActionMenus } from "@web/search/action_menus/action_menus";

patch(ActionMenus.prototype, 'sticky_notes_odoo/js/action_menus', {
    setup() {
    this._super(...arguments);
    },
    //The function is used to do an action for creating the sticky notes.
    StickyButton() {
        var view_id = this.env.config.viewId
        var res_model = this.props.resModel
        var id = this.actionService.currentController.props.resId
        this.actionService.doAction({
            type: 'ir.actions.act_window',
            res_model: 'sticky.notes',
            view_mode: 'form',
            view_type: 'form',
            views: [[false, 'form']],
            target: 'new',
            context: {
                'default_active_model': id,
                'default_active_model_name': res_model,
                'default_active_view':view_id,
            },
        });
    },
});
