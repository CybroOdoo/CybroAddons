/** @odoo-module */
import { _t } from "@web/core/l10n/translation";
import { Component, useRef, onMounted, useState, reactive } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
/**
* This class represents a custom popup in the Point of Sale.
*/
export class CrossProduct extends Component {
    static components = { Dialog };
    static template = "pos_pro_cross_selling.CrossProduct";
    static defaultProps = {
        closePopup: _t("Cancel"),
        confirmPopup: _t("Confirm"),
    };
    setup() {
        super.setup();
        this.state = useState({
            // duration is expected to be given in minutes
            Products: this.props.product,
        });
    }
    async confirm() {
        // Adding Products into the order line
        var products = this.state.Products;
        const pos = this.env.services.pos;

        for (var i = 0; i < products.length; i++) {
            if (products[i].selected == true) {
                // Get the product variant from POS models
                var SelectedProduct = pos.models["product.product"].get(products[i].id);

                if (SelectedProduct && SelectedProduct.product_tmpl_id) {
                    // addLineToCurrentOrder expects product_tmpl_id (template), not product_id (variant)
                    // Pass both product_tmpl_id and product_id for correct behavior
                    await pos.addLineToCurrentOrder({
                        product_tmpl_id: SelectedProduct.product_tmpl_id,
                        product_id: SelectedProduct
                    }, {});
                } else {
                    console.warn(`Cross-selling product with ID ${products[i].id} not found in POS product cache. Please ensure it is available in POS.`);
                }
            }
        }
        this.props.close();
    }
    async _onClickOrder(event, product) {
        //Selecting the cross products
        var id = product.id
        var products = this.state.Products
        var lines = []
        for (var i = 0; i < products.length; i++) {
            if (products[i].id == id) {
                if (products[i].selected == false) {
                    products[i].selected = true;
                }
                else if (products[i].selected == true) {
                    products[i].selected = false;
                }
                lines.push(products[i].name)
            }
        }
    }
}
