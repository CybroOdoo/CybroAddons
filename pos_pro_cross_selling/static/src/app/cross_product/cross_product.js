/** @odoo-module */
import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
import { _t } from "@web/core/l10n/translation";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { useRef, onMounted } from "@odoo/owl";
/**
* This class represents a custom popup in the Point of Sale.
* It extends the AbstractAwaitablePopup class.
*/
export class CrossProduct extends AbstractAwaitablePopup {
    static template = "pos_pro_cross_selling.CrossProduct";
    static defaultProps = {
        closePopup: _t("Cancel"),
        confirmPopup: _t("Confirm"),
        title: _t("Cross Selling Products"),
    };
    setup() {
        super.setup();
    }
    async confirm() {
        // Adding  Products into the order line
        super.confirm();
        var product = this.props.product
        for(var i = 0; i < product.length; i++){
            if (product[i].selected == true){
                this.env.services.pos.get_order().add_product(this.env.services.pos.db.product_by_id[product[i].id]);
            }
        }
    }
    async _onClickOrder(event, product){
        //Selecting the cross products
        var id = product.id
        var product = this.props.product
        var lines = []
        for(var i = 0; i < product.length; i++){
            if (product[i].id == id){
                if (product[i].selected == false){
                    product[i].selected = true;
                }
                else if (product[i].selected == true){
                    product[i].selected = false;
                }
                lines.push(product[i].name)
            }
        }
    }
}