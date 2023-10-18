odoo.define('product_multi_uom_pos.multi_uom_pos', function(require) {
    'use strict';
    var OrderLine = require('point_of_sale.Orderline');
    const Registries = require('point_of_sale.Registries');
    const { useListener } = require("@web/core/utils/hooks");
    const OrderLineExtend = (OrderLine) => class extends OrderLine {
        setup(){
            super.setup();
            useListener('click', '#select_uom', this.onClickUom);
            useListener('click', '#reset_uom', this.resetUom);
        }

        // Retrieve the available unit of measure options based on the product's multi_uom_ids
        getUom() {
            const filteredData = this.props.line.pos.pos_multi_uom.filter(obj => this.props.line.product.pos_multi_uom_ids.includes(obj.id));
            return filteredData
        }

        // Handle click event on the unit of measure options
        onClickUom(ev) {
            var splitTargetValue = ev.target.value.split(',')
            var price = splitTargetValue[0]
            var uomId = splitTargetValue[1]
            var uomName = splitTargetValue[2]
            // Set the selected unit of measure on the order line
            this.props.line.set_uom({0:uomId,1:uomName})

            // Set the price_manually_set flag to indicate that the price was manually set
            this.props.line.price_manually_set = true;

            // Set the unit price of selected UoM on the order line
            this.props.line.set_unit_price(price);
        }

        // Reset the unit of measure to the default uom_id of the product
        resetUom(ev) {
            var lineId = this.props.line.id
            console.log(this)
            this.el.querySelector('#change_uom').disabled = false;
            this.el.querySelector('#select_uom').value = 'change_uom';
            this.el.querySelector('#change_uom').disabled = true;
            this.props.line.set_uom({0:this.props.line.product.uom_id[0],1:this.props.line.product.uom_id[1]})
            this.props.line.set_unit_price(this.props.line.product.lst_price);
        }
    };
    Registries.Component.extend(OrderLine, OrderLineExtend);
    return OrderLine;
});
