/** @odoo-module **/

import { MovePlugin } from "@html_builder/core/move_plugin";
import { patch } from "@web/core/utils/patch";

patch(MovePlugin.prototype, {
    areArrowsHidden() {
        if (!this.overlayTarget || !this.overlayTarget.parentNode) {
            return true;
        }
        return super.areArrowsHidden(...arguments);
    },
    isMovable(el) {
        if (!el || !el.parentNode) {
            return false;
        }
        return super.isMovable(...arguments);
    },
});
