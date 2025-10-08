/** @odoo-module **/
import { ViewButton } from '@web/views/view_button/view_button';
import { patch } from "@web/core/utils/patch";
import { DROPDOWN } from "@web/core/dropdown/dropdown";
import { pick } from "@web/core/utils/objects";

patch(ViewButton.prototype,'@web/views/view_button/view_button', {
    setup() {
     this._super(...arguments);
    },
    //This is used to edit the sticky notes
    onClick(ev) {
        var view_id = this.env.config.viewId
        if(ev.target.name == 'edit_notes'){
            var id = this.env.model.__bm_load_params__.res_id
            var res_model = this.env.model.__bm_load_params__.modelName
            var str = ev.target.parentElement.parentElement.textContent.trim()
            const heading = str.slice(0, str.indexOf(' '));
            const notes = str.slice(str.indexOf(' ')+ 1);
            var styleString = ev.target.parentElement.parentElement.getAttribute('style')
            var propertyIndex = styleString.indexOf('background-color');
            if (propertyIndex !== -1) {
                        var startIndex = styleString.indexOf(':', propertyIndex) + 1;
                        var endIndex = styleString.indexOf(';', startIndex);
                        if (endIndex === -1) {
                        endIndex = styleString.length;
                    }
            }
            var propertyIndexTextcolor = styleString.indexOf('text-color');
            var startIndexTextcolor = styleString.indexOf(':', propertyIndexTextcolor) + 1;
            var endIndexTextcolor = styleString.indexOf(';', startIndexTextcolor);
            var action = this.env.model.actionService.doAction({
                type: 'ir.actions.act_window',
                res_model: 'sticky.notes.update',
                view_mode: 'form',
                view_type: 'form',
                views: [[false, 'form']],
                target: 'new',
                context: {
                    'default_background_color': (styleString.substring(startIndex, endIndex)).trim(),
                    'default_text_color': (styleString.substring(startIndexTextcolor, endIndexTextcolor)).trim(),
                    'default_heading':heading,
                    'default_note':notes,
                    'default_prev_heading':heading,
                    'default_prev_notes':notes,
                    'view_id': view_id,
                    'default_active_model': id,
                    'default_active_model_name':res_model,
                },
            });
        }
//        delete the sticky notes
        else if(ev.target.name == 'delete_notes'){
            var id = this.env.model.__bm_load_params__.res_id
            var res_model = this.env.model.__bm_load_params__.modelName
            var action = this.env.model.actionService.doAction({
                type: 'ir.actions.act_window',
                res_model: 'sticky.notes.delete',
                view_mode: 'form',
                view_type: 'form',
                views: [[false, 'form']],
                target: 'new',
                context: {
                    'default_note':ev.target.parentElement.parentElement.textContent,
                    'default_active_model': id,
                    'default_active_model_name':res_model,
                    'view_id': view_id,
                },
            });
            this.env.model.load()
        }
        else{
             if (this.props.tag === "a") {
                ev.preventDefault();
            }
            if (this.props.onClick) {
                return this.props.onClick();
            }
            this.env.onClickViewButton({
                clickParams: this.clickParams,
                getResParams: () =>
                    pick(this.props.record, "context", "evalContext", "resModel", "resId", "resIds"),
                beforeExecute: () => {
                    if (this.env[DROPDOWN]) {
                        this.env[DROPDOWN].close();
                    }
                },
                disableAction: this.props.disable,
                enableAction: this.props.enable,
            });
        }
    }
});
