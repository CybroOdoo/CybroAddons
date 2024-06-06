/** @odoo-module */
import { registry} from '@web/core/registry';
import { useRef } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
const { Component, useState } = owl
import {Dropdown} from "@web/core/dropdown/dropdown";
import {DropdownItem} from "@web/core/dropdown/dropdown_item";
import { _t } from "@web/core/l10n/translation";
    var currency=0;
export class PharmacyOrderLines extends Component {
    setup() {
        super.setup(...arguments);
        this.ref = useRef('root')
        this.orm = useService('orm')
        this.user = useService("user");
        this.actionService = useService("action");
        this.state = useState({
              product_lst :[],
              medicines :[],
              units :[],
              medicine :[],
              table_row: [{}]
        });
        this.lineState = useState({
            product: this.props.line.product,
            qty: this.props.line.qty,
            uom: this.props.line.uom,
            price: this.props.line.price,
            sub_total: this.props.line.sub_total,
        })
        this.fetch_product();
        this.fetch_uom();
        this.fetch_tax();
    }
//  Fetch product details
    async fetch_product() {
        var product_lst= [];
        var domain = [['medicine_ok', '=', true]]; // Define the search domain as a list of lists
        var result =await this.orm.call('product.template', 'search_read', [domain]);
        this.product_lst=result
        this.create_order()
    }
//   Fetch UOM of selected product
    async fetch_uom (){
        var uom_lst= [];
        var result= await this.orm.call( 'uom.uom','search_read',)
        this.uom_lst=result
    }
//  Fetch tax amount of product.
    async fetch_tax(){
        var tax_lst= [];
        var result= await this.orm.call( 'account.tax','search_read',)
        this.tax_lst=result
    }
//  Method for creating sale order
    async create_order() {
        await this.orm.call('hospital.pharmacy','company_currency',
        ).then(function (result){
           $('#symbol'+ currency).text(result || '');
           $('#symbol').text(result || '');
        })
        this.state.medicines = await this.product_lst;
        this.state.units = await this.uom_lst;
    }
// To calculate the subtotal of the medicine
    calculateSubtotal(qty, price) {
        return qty *price
    }
//  Method on changing the product in the sale order
    async _onChange_prod_price (med_id) {
        this.lineState.product = med_id
        const medicine = this.state.medicines.filter(med => med.id === med_id)[0]
        this.lineState.price = medicine.list_price
        this.lineState.sub_total = this.calculateSubtotal(this.lineState.qty, medicine.list_price)
        this.props.updateOrderLine(this.lineState, this.props.id)
     }
//  Calculation of sub total based on product quantity
    async _onChange_prod_qty () {
        var self = this;
        this.lineState.sub_total = this.calculateSubtotal(this.lineState.qty, this.lineState.price)
        this.props.updateOrderLine(this.lineState, this.props.id)
    }
//  To remove the added line
    async remove_line () {
        this.props.removeLine(this.props.id)
    }
}
PharmacyOrderLines.template = "PharmacyOrderLines"
PharmacyOrderLines.components = { Dropdown, DropdownItem }
