/** @odoo-module **/
import { TicketScreen } from "@point_of_sale/app/screens/ticket_screen/ticket_screen";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { usePos } from "@point_of_sale/app/store/pos_hook";


patch(TicketScreen.prototype, {

    setup() {
        super.setup();
        this.pos = usePos()
        this.searchDetails = this.pos.searchDetails;
    },

    _getSearchFields() {
        return Object.assign({}, super._getSearchFields(...arguments), {
            BARCODE: {
                repr: (order) => order.barcode || "",
                displayName: _t("Barcode"),
                modelField: "barcode",
            },
        });
    }
})
