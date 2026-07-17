/** @odoo-module **/
import {DropdownItem} from "@web/core/dropdown/dropdown_item";
import {patch} from "@web/core/utils/patch";
import {rpc} from "@web/core/network/rpc";

patch(DropdownItem.prototype, {
    onClick(ev) {
        super.onClick(ev);
        if (ev.currentTarget.classList.contains('o_app')) {
            let app = {'appId': ev.currentTarget.dataset.section};
            rpc('/theme_studio/add_recent_app', {
                method: 'call',
                args: [app]
            }).then(() => {
                this.env.bus.trigger('INFINITO:RECENT_APPS_UPDATED');
            });
        }
    }
});
