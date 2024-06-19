/** @odoo-module **/
/**
     * This file is used register a popup for transferring the stock of selected products
     */
   import AbstractAwaitablePopup from 'point_of_sale.AbstractAwaitablePopup';
   import Registries from 'point_of_sale.Registries';
   const rpc = require('web.rpc');

   class CreateTransferPopup extends AbstractAwaitablePopup {

       _clickPicking(ev){
       // This hide and show destination and source location based on the picking type selected
           var type = ev.target.selectedOptions[0].dataset.type
           this.el.querySelector('#dest_tr').show();
           this.el.querySelector('#source_tr').show();
           if (type == 'incoming') {
              this.el.querySelector('#source_tr').hide()
           }
           else if (type == 'outgoing') {
                   this.el.querySelector('#dest_tr').hide()
           }
       }
        async Create(){
        // This get all the values you selected in the popup and transfer the stock by passing data backend.
                var pick_id = this.el.querySelector('#picking' ).value;
                var source_id = this.el.querySelector('#source_loc' ).value;
                var dest_id = this.el.querySelector('#dest_loc' ).value;
                var state   = this.el.querySelector('#state' ).value;
                var line = this.env.pos.get_order().orderlines;
                var product = {'pro_id':[],'qty':[]}
                for(var i=0; i<line.length;i++){
                     product['pro_id'].push(line[i].product.id)
                     product['qty'].push(line[i].quantity)
                }
                var self = this;
                await rpc.query({
                          model:'pos.config',
                          method:'create_transfer',
                          args:[pick_id,source_id,dest_id,state,product ]
                          }).then(function(result){
                             self.showPopup("TransferRefPopup", {
                                data : result,
                             });
                          });
               this.cancel();

        }
    }
   CreateTransferPopup.template = 'CreateTransferPopup';
   Registries.Component.add(CreateTransferPopup);