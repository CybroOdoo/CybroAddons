odoo.define('pos_pro_cross_selling.CrossProducts', function(require) {
    'use strict';

    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const Registries = require('point_of_sale.Registries');
    const { useListener } = require("@web/core/utils/hooks");
    // Class for cross products
    class CrossProducts extends AbstractAwaitablePopup {
        setup() {
            super.setup();
            useListener('click-product', this._onClickOrder);
        }
        async confirm() {
            // Adding  Products into the order line
            super.confirm();
            var product = this.props.product
            for(var i = 0; i < product.length; i++){
                if (product[i].selected == true){
                    this.env.pos.get_order().add_product(this.env.pos.db.product_by_id[product[i].id]);
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
    CrossProducts.template = 'CrossProducts';
    CrossProducts.defaultProps = { cancelKey: false };
    Registries.Component.add(CrossProducts);
    return CrossProducts;
});
