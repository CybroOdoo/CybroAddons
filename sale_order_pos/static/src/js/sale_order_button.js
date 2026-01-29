odoo.define('sale_order_pos.CreateSaleOrder', function(require) {
'use strict';
   var rpc = require('web.rpc');
   const PosComponent = require('point_of_sale.PosComponent');
   const ProductScreen = require('point_of_sale.ProductScreen');
   const { useListener } = require('web.custom_hooks');
   const Registries = require('point_of_sale.Registries');
   const PaymentScreen = require('point_of_sale.PaymentScreen');
   var core = require('web.core');
   const { Gui } = require('point_of_sale.Gui');
   const _t = core._t;

   class PosSaleOrder extends PosComponent {
       constructor() {
           super(...arguments);
           useListener('click', this.onClick);
       }
      async onClick() {
//            for creating sale order from pos throgh a button
            var cus = this.env.pos.get_client()
            const order = this.env.pos.get_order();
            var lines = order.get_orderlines()
            if (lines.length === 0 ){
                Gui.showPopup("ErrorPopup", {
                'title': _t("Please select a product"),
                'body':  _t("You cannot create sales order without selecting a product."),
                });
                return;}
            else if(!cus){
                Gui.showPopup("ErrorPopup", {
                'title': _t("Please select a customer"),
                'body':  _t("You cannot create sales order without selecting a customer."),
                });
                return;}

            else {
                 const { confirmed} = await this.showPopup("ConfirmPopup", {
                      title: this.env._t('Confirmation'),
                      body: this.env._t('Are you sure you want to create sale order?'),
                   });
                if(confirmed){
                    var temp_list = []
                    for(var i=0; i < lines.length ; i++){
                    const dict = { quantity:lines[i].quantity, price:lines[i].get_display_price(), discount:lines[i].get_discount(),product:lines[i].product.id}
                    temp_list.push(dict)
                    }
                    rpc.query({
                    model: 'sale.order',
                    method: 'create_sale_order',
                    args: [,temp_list,cus]
                })
                }
            }
       }
   }
   PosSaleOrder.template = 'PosSaleOrder';
   ProductScreen.addControlButton({
       component: PosSaleOrder,
       condition: function() {
           return this.env.pos;
       },
   });
   Registries.Component.add(PosSaleOrder);
   return PosSaleOrder;
});
