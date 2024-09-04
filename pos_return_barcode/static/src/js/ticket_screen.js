/** @odoo-module **/
import { TicketScreen } from "@point_of_sale/app/screens/ticket_screen/ticket_screen";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
patch(TicketScreen.prototype, {
    _getSearchFields() {
        return Object.assign({}, super._getSearchFields(...arguments), {
            BARCODE: {
               repr: (order) => order.barcode,
                displayName: _t("Barcode"),
                modelField: "barcode",
            },
        });
    }
})
