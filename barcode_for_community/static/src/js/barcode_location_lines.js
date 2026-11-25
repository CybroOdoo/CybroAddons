/** @odoo-module */
import {Component, useRef, useState, useEffect, onPatched} from "@odoo/owl";
import {useService} from "@web/core/utils/hooks";
import {Dropdown} from "@web/core/dropdown/dropdown";
import {DropdownItem} from "@web/core/dropdown/dropdown_item";

export class CustomBarcodeLocationLines extends Component {
    setup() {
        this.state = useState({
            transfer: [],
            move_lines: [],
            destination: "",
            quantity_to_add: false,
            overall_qty: 0,
        })
        this.actionService = useService("action")
        this.orm = useService("orm")
        useEffect((props) => {
            this.updateState(props)
        }, () => [this.props])
    }

    updateState(props) {
        Object.assign(this.state, {
            transfer: props.transfer,
            move_lines: props.transfer.move_line_ids,
            destination: props.destination,
            quantity_to_add: props.transfer.product_uom_qty,
            overall_qty: props.transfer.overall_qty,
        })
    }

    /**
     * Function trigger 'barcode-cancel-stock-quantity' bus for removing data from the Barcode product view c
     */
    _onclickCancel() {
        this.env.bus.trigger('barcode-cancel-stock-move', {
            id: this.state.transfer.id,
            resModel:  this.state.transfer.res_model,
        });
    }

    /**
     * Function for increment or decrement the quantity of the record by 1
     */
    async _onClickExternalOperation(operation) {
        if (this.props.transfer.res_model === "stock.move.line") {
            const newQuantity = operation === 'minus'
                ? this.state.transfer.line_quantity - 1 // Ensure the quantity doesn't go below 1
                : this.state.transfer.line_quantity + 1;
            await this.orm.write('stock.move.line', [this.state.transfer.id], {
                'quantity': newQuantity,
            });
            this.state.transfer.line_quantity = newQuantity;
            await this.props.notify()
        } else {
           if (operation === "add") {
                await this.orm.call("barcode.management", "add_move_line_by_one", [this.state.transfer.id])
                await this.props.notify()
           }
           else{
                this.props.showNotification("Quantity cannot be negative")
           }
        }

    }

    handleEditLine() {
        this.actionService.doAction({
            type: 'ir.actions.act_window',
            name: 'Stock Move Line',
            target: 'new',
            res_model: "stock.move.line",
            res_id: this.props.transfer.id,
            views: [
                [false, 'form']
            ],
        }, {
            onClose: async () => await this.props.notify()
        })
    }

}

CustomBarcodeLocationLines.components = {
    Dropdown, DropdownItem
}
CustomBarcodeLocationLines.template = "barcode_for_community.BarcodeLocationLines";