/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { ShortcutPopup } from "./shortcut_popup.js";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";

patch(ControlButtons.prototype, {
    async clickShortcut() {
        if (this.pos.config.select_shortcut_id) {
            this.dialog.add(ShortcutPopup, {
                title: _t("Pos Keyboard Shortcuts"),
            });
        } else {
            this.dialog.add(AlertDialog, {
                title: _t("Warning"),
                body: _t("Please select a shortcut first before proceeding"),
            });
        }
    }
});
