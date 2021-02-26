odoo.define("point_of_sale_logo.pos_receipt_image", function (require) {
    "use strict";
    const Registries = require('point_of_sale.Registries');
    const OrderReceipt = require('point_of_sale.OrderReceipt');
    const PosReceiptLogoChrome = (OrderReceipt) =>
        class extends OrderReceipt {
            get imageUrl() {
                if (this.env.pos){
                    if (this.env.pos.config){
                            if (this.env.pos.config.image != false){
                                return `/web/image?model=pos.config&field=image&id=${this.env.pos.config_id}&unique=1`;


                            }else{
                                return false
                            }
                    }
                }
            }
        };
    Registries.Component.extend(OrderReceipt, PosReceiptLogoChrome);
    return OrderReceipt;
});