/** @odoo-module **/

import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { Component } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { _t } from "@web/core/l10n/translation";

export class AlternativeProduct extends AbstractAwaitablePopup {
        static template = "pos_alternative_products.AlternativeProduct";
        static defaultProps = {
            cancelText: 'Cancel',
            title: 'Alternative Product',
            body: '',
        };
	    setup() {
            super.setup();
            this.pos = usePos();
            this.orm = useService("orm");
            this.popup = useService("popup");

	    }
        async clickProduct(item){
            var response = await this.orm.call("stock.quant", "pos_alternative_product", [item.id, item.default_code,]);
            if (response.length!=0)
                {
                  var product = await this.pos.db.get_product_by_id(parseInt(response));
                  this.pos.get_order().add_product(product);
                  super.confirm();
               }
           else{
                await this.popup.add(ErrorPopup, {
                        title: _t("Product Missing"),
                        body: _t("Make sure that the product is available in pos."),
                });
            }
        }
        cancel() {
            super.cancel();
        }
}
