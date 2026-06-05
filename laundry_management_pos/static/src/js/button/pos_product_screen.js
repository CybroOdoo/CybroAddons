/** @odoo-module **/
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { useService } from "@web/core/utils/hooks";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { _t } from "@web/core/l10n/translation";
import { CreateProductDialog } from "../popup/product_create_popup";
import { patch } from "@web/core/utils/patch";
patch(ControlButtons.prototype, {
    setup() {
        super.setup(...arguments);
        this.pos = usePos();
        this.dialog = useService("dialog");
    },
    onClick() {
        this.dialog.add(CreateProductDialog, {
            title: _t("Create Product"),
        });
    }

});
