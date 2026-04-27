/** @odoo-module */
import { Orderline } from "@point_of_sale/app/generic_components/orderline/orderline";
import { useRef, useState, onWillUpdateProps } from "@odoo/owl";
import { patch } from "@web/core/utils/patch";
import { usePos } from "@point_of_sale/app/store/pos_hook";

patch(Orderline.prototype, {
    setup() {
        super.setup(...arguments);
        this.inputRef = useRef("uom_value");
        this.pos = usePos();
        this.state = useState({
            unit: this.props.line.unit_display || this.props.line.unit || "",
        });
        onWillUpdateProps((nextProps) => {
            this.state.unit = nextProps.line.unit_display || nextProps.line.unit || "";
        });
    },

    onRandomChange(event) {
        const order = this.pos.get_order()
        let line = this.props.line;
        const order_line = order.get_orderlines().find(
            l => l.uuid === line.uuid
        );

        const selectElement = event.target.selectedOptions[0];
        if (!selectElement) return;

         // Update the line only if it exists
        if (line && order_line) {
            const newPrice = parseFloat(selectElement.dataset.price);
            const uomId = parseInt(selectElement.dataset.uom_id);
            const uomName = selectElement.dataset.name;


            // Set price using the correct method for Odoo 18
            if (newPrice && uomId) {
                order_line.set_unit_price(newPrice);
                order_line.price_type = "manual";
                order_line.raw.uom_id = uomId;
                line.uom_id = uomId;
                this.state.unit = uomName;
            }
        }
    },

    onReset(event) {
        let line = this.props.line;
        const order = this.pos.get_order()
        const order_line = order.get_selected_orderline()
        if (order_line?.product_id) {
            const originalPrice = order_line.product_id.lst_price || order_line.product_id.price;

            // Reset price using the correct method
            if (originalPrice) {
                order_line.set_unit_price(originalPrice);
                order_line.price_type = "original";
                order_line.raw.uom_id = order_line.product_id.uom_id.id;
                line.uom_id = order_line.product_id.uom_id.id;
                this.state.unit = order_line.product_id.uom_id.name;
            }

        }

        // Reset the select element
        const selectElement = this.inputRef.el;
        if (selectElement) {
            selectElement.selectedIndex = 0;
        }
    },
});


patch(Orderline, {
    props: {
        ...Orderline.props,
        line: {
            ...Orderline.props.line,
            shape: {
                ...Orderline.props.line.shape,
                getUom: { type: Array, optional: true },
                uom_id: { type: [String, Number], optional: true },
                unit_display: { type: String, optional: true },
                uom_name: { type: String, optional: true },
                uuid: { type: String, optional: true },
            },
        },
    },
});
