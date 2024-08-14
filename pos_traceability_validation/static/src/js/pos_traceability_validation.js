/** @odoo-module */
import { EditListPopup } from "@point_of_sale/app/store/select_lot_popup/select_lot_popup"
import { Orderline } from "@point_of_sale/app/store/models"
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { _t } from "@web/core/l10n/translation";


patch(EditListPopup.prototype, {
    setup() {
    /**Updating the orm and popup**/
        this.pos = usePos();
        this.orm = useService("orm");
        this.popup = useService("popup");
        super.setup(...arguments);
    },
    async confirm() {
    /**Checking the lot and serial and raising the error popup**/
        if (this.props.title === 'Lot/Serial Number(s) Required'){
            var lot_string = this.state.array
            var lot_names = [];
            for (var i = 0; i < lot_string.length; i++) {
                if (lot_string[i].text != ""){
                    lot_names.push(lot_string[i].text);
                }
            }
            const result = await this.orm.call(
                "stock.lot", "validate_lots", [lot_names], {}
            )
            if(result != true){
                if(result[0] == 'no_stock'){
                    this.env.services.popup.add(ErrorPopup, {
                        title: _t("Insufficient stock"),
                        body: _t(
                            "Insufficient stock for " + result[1]
                        ),
                    });
                }
                else if(result[0] == 'duplicate'){
                    this.env.services.popup.add(ErrorPopup, {
                        title: _t("Duplicate entry"),
                        body: _t(
                            "Duplicate entry for " + result[1]
                        ),
                    });
                }
                else if(result[0] == 'except'){
                    alert("Exception occurred with " + result[1])
                    this.env.services.popup.add(ErrorPopup, {
                        title: _t("Exception"),
                        body: _t(
                            "Exception occurred with" + result[1]
                        ),
                    });
                }
            }
            else{
                this.props.resolve({ confirmed: true, payload: await this.getPayload() });
                this.pos.closeTempScreen();
                this.props.close();
            }
        }
        else{
            this.props.resolve({ confirmed: true, payload: await this.getPayload() });
            this.pos.closeTempScreen();
            this.props.close();
        }
    }
});
