/** Extended the receipt-screen and added popup */
odoo.define('pos_invoice_in_whatsapp.ReceiptScreen', function(require) {
    'use strict';
    var core = require('web.core');
    var rpc = require('web.rpc');
    var self=this;
    const ReceiptScreen = require('point_of_sale.ReceiptScreen');
    const Registries = require('point_of_sale.Registries');
    const PosReceiptScreenExtend = ReceiptScreen =>
        class extends ReceiptScreen {
//        Displaying popup to display message type
      async click_whatsapp(event) {
                     this.env.pos.CurrentOrder=this.currentOrder;
                    this.showPopup('WtspMessagePopup', {
                   confirmText: 'Ok',
                   cancelText: 'Cancel',
                   title: 'Choose Your Message Type',
                   body:'' ,
               });
               event.preventDefault();
                }
           };
    Registries.Component.extend(ReceiptScreen, PosReceiptScreenExtend);
    return ReceiptScreen;
});
