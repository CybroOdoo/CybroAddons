/** @odoo-module **/
/**
* This file is used register a popup for transferring the stock of selected products
*/
import AbstractAwaitablePopup from 'point_of_sale.AbstractAwaitablePopup';
import Registries from 'point_of_sale.Registries';
const rpc = require('web.rpc');

class CreateTransferPopup extends AbstractAwaitablePopup {
    // This function hides and displays destination and source locations based on the picking type selected
    _clickPicking(ev){
        var type = ev.target.selectedOptions[0].dataset.type
        this.el.querySelector('#dest_tr').style.display = '';
        this.el.querySelector('#source_tr').style.display = '';
        if (type == 'incoming') {
            this.el.querySelector('#source_tr').style.display = 'none';
            this.el.querySelector('#source_loc').value = this.props.data.location[1].id;
            this.el.querySelector('#dest_loc').value = this.props.data['wh_stock'];
        }
        else if (type == 'outgoing') {
            this.el.querySelector('#dest_tr').style.display = 'none';
            this.el.querySelector('#source_loc').value = this.props.data['wh_stock'];
            this.el.querySelector('#dest_loc').value = this.props.data.location[1].id;
        }
    }
    // This function get all the values you selected in the popup and transfer the stock by passing data backend.
    async Create(){
        var pick_id = this.el.querySelector('#picking').value;
        var source_id = this.el.querySelector('#source_loc').value;
        var dest_id = this.el.querySelector('#dest_loc').value;
        var state   = this.el.querySelector('#state').value;
        var line = this.env.pos.get_order().orderlines;
        var product = {'pro_id':[],'qty':[], 'uom':[]}
        for(var i=0; i<line.length;i++){
            product['pro_id'].push(line.models[i].product['id'])
            product['qty'].push(line.models[i].quantity)
            product['uom'].push(line.models[i].product['uom_id'][0])
        }
        var self = this;
        await rpc.query({
            model:'pos.config',
            method:'create_transfer',
            args:[pick_id,source_id,dest_id,state,product]
        }).then(function(result){
            self.showPopup("TransferRefPopup", {
                data : result,
            });
        });
    }
}
CreateTransferPopup.template = 'CreateTransferPopup';
Registries.Component.add(CreateTransferPopup);
