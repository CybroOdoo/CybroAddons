odoo.define('pos_alternative_products.AlternativeProductPopup', function (require) {
    'use strict';
    //Which is used to add pop up for alternative products.
    const { useListener } = require("@web/core/utils/hooks");
    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const Registries = require('point_of_sale.Registries');
    const { _t } = require('web.core');
    var rpc = require('web.rpc');
    //Alternative product pop up
    class AlternativeProduct extends AbstractAwaitablePopup {
	    setup() {
            super.setup();
                useListener('click-product', this._clickProduct);
	    }
        async _clickProduct(item){
            var response = await this.rpc({
                            model: 'stock.quant',
                            method: "pos_alternative_product",
                            args:[,item.detail.id,item.detail.default_code]
            })
            if (response!=0)
            {
              var product = await this.env.pos.db.get_product_by_id(parseInt(response));
              this.env.pos.get_order().add_product(product);
              this.env.posbus.trigger('close-popup', {
                        popupId: this.props.id,
                        response: { confirmed: true, payload: null},
              });
           }
           else{
            this.showPopup('ErrorPopup', {
                    title: this.env._t('Product Missing'),
                    body: this.env._t('Make sure that the product is available in pos'),
                });
           }
        }
	}
	    //Create AlternativeProduct popup
       AlternativeProduct.template = 'AlternativeProduct';
       AlternativeProduct.defaultProps = {
        cancelText: 'Cancel',
        title: 'Alternative Product',
        body: '',
       };
   Registries.Component.add(AlternativeProduct);
   return AlternativeProduct;
});
