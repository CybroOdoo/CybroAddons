/** @odoo-module */

import { Component } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { usePos } from "@point_of_sale/app/store/pos_hook";

export class ShortcutPopup extends Component {
    static template = "pos_keyboard_shortcut.ShortcutPopup";
    static components = { Dialog };
    static props = {
        close: Function,
        title: { type: String, optional: true },
    };

    setup() {
        this.pos = usePos();
    }
}
