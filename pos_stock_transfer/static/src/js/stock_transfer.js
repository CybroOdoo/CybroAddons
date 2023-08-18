/** @odoo-module **/
/**
     * This file is used to register the a new button for stock transfer
*/
import PosComponent from 'point_of_sale.PosComponent';
import Registries from 'point_of_sale.Registries';
import  ProductScreen  from 'point_of_sale.ProductScreen';
const { useListener } = require("@web/core/utils/hooks");
const rpc = require('web.rpc');

    class StockTransferButton extends PosComponent {
       async onClick(){
        // This will show a popup to transfer stock with selected products and customer
             var self = this
             if((this.env.pos.get_order().orderlines) == 0){
                  this.showPopup('ErrorPopup',{
                      'title': this.env._t('Select Products'),
                      'body': "Please Select at least one product for transferring",
                  });
             }
             else{
                 await rpc.query({
                      model:'pos.config',
                      method:'get_stock_transfer_list',
                      }).then(function(result){
                         self.showPopup("CreateTransferPopup", {
                               data : result,
                         });
                      });
             }
        }
    }
StockTransferButton.template = 'StockTransferButton';
        ProductScreen.addControlButton({
          component: StockTransferButton,
          condition: function() {
              return true;
          },
        });
Registries.Component.add(StockTransferButton);