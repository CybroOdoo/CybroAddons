odoo.define("point_of_sale_logo.image", function (require) {
    "use strict";
    var PosBaseWidget = require('point_of_sale.chrome');
    var screens = require('point_of_sale.screens');
    var core = require('web.core');

    var QWeb = core.qweb;
    console.log("PosBaseWidget", PosBaseWidget)
    screens.ReceiptScreenWidget.include({
        render_receipt: function () {
            this._super(this);
            var order = this.pos.get_order()
            this.$('.pos-receipt-container').html(QWeb.render('PosTicket',{
                    widget:this,
                    a2 : window.location.origin + '/web/image?model=pos.config&field=image&id='+this.pos.config.id,
                    order: order,
                    receipt: order.export_for_printing(),
                    orderlines: order.get_orderlines(),
                    paymentlines: order.get_paymentlines(),
                }));
        },
    });
    PosBaseWidget.Chrome.include({
        renderElement:function () {

            var self = this;
            console.log("self:", self)

            if(self.pos.config){
                if(self.pos.config.image){
                    this.flag = 1
                    this.a3 = window.location.origin + '/web/image?model=pos.config&field=image&id='+self.pos.config.id;
                }
            }
            this._super(this);
        }
    });
});