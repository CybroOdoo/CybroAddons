/** @odoo-module **/
/**
     * This file is used to register the a popup for viewing reference number of  transferred stock
*/
import AbstractAwaitablePopup from 'point_of_sale.AbstractAwaitablePopup';
import Registries from 'point_of_sale.Registries';

class TransferRefPopup extends AbstractAwaitablePopup {
   stock_view() {
   // This will used to redirect the page to corresponding stock transfer
     var ref_id = this.props.data.id
     location.href = '/web#id='+ ref_id +'&&model=stock.picking&view_type=form'
   }
    }
TransferRefPopup.template = 'TransferRefPopup';
Registries.Component.add(TransferRefPopup);
