/** @odoo-module */
import {Component, useRef, useState, useEffect} from "@odoo/owl";
import {useService} from "@web/core/utils/hooks";
import {Dropdown} from "@web/core/dropdown/dropdown";
import {DropdownItem} from "@web/core/dropdown/dropdown_item";


export const truncateText = (text, letterCount = 15) => {
    if (text.length > 2 * letterCount) {
        const firstPart = text.slice(0, letterCount);          // First few characters
        const lastPart = text.slice(-letterCount);             // Last few characters
        return `${firstPart} ... ${lastPart}`;                 // Concatenate first, ellipsis, and last part
    } else {
        return text;  // If the text is short, return it as-is
    }
}

export class CustomBarcodeAdjustmentLines extends Component {
    setup() {
        this.root = useRef('root-AdjustmentLines')
        this.state = useState({
            stock: this.props.stock,
            className: ""
        })
        this.actionService = useService("action")
        this.orm = useService("orm")
        let firstTime = true;
        useEffect(() => {
            if (!firstTime) {
                this.state.className = "barcode-qty-change"
                setTimeout(() => {
                    this.state.className = ""
                }, 500)
            }
            firstTime = false;
        }, () => [this.props.stock.inv_quantity])
    }

    get getClassName() {
        return this.state.className
    }

    /**
     * Function trigger 'barcode-cancel-stock-quantity' bus for removing data from the Barcode product view c
     */
    _onclickCancel(ev) {
        // ev.stopPropagation();
        this.env.bus.trigger('barcode-cancel-stock-quantity', [this.state.stock.id])
    }

    /**
     * While double clicking the card removing applying the custom style and passing id using bus
     */
    _onSelectCards() {
        this.state.stock.value = !this.state.stock.value
        if (this.state.stock.value) {
            this.root.el.classList.add("barcode-card-active");
        } else {
            this.root.el.classList.remove("barcode-card-active");
        }
        this.env.bus.trigger('barcode-applying-multi-stock-quantity', {
            id: this.state.stock.id,
            value: this.state.stock.value
        })
    }

    /**
     * Function for invisible the modal
     */
    _onClickDiscardChanges() {
        this.root.el.querySelector('#AdjustmentLinesModal').style.display = 'none'
        this.root.el.querySelector('.input_for_quantity').value = this.state.stock.inv_quantity
        this.is_float = false;
    }

    /**
     * Function for apply button in the modal for changing the quantity of the record
     */
    _onClickApplyChanges(value) {
        this.state.stock.inv_quantity = value
        this.orm.write('stock.quant', [this.state.stock.id], {
            'inventory_quantity': Number(value)
        })
        this.root.el.querySelector('#AdjustmentLinesModal').style.display = 'none'
        this.is_float = false;
    }

    /**
     * Function for increment or decrement the quantity of the record by 1
     */
    _onClickExternalOperation(operation) {
        if (operation === 'minus') {
            this.state.stock.inv_quantity--
        } else {
            this.state.stock.inv_quantity++
        }
        this.orm.write('stock.quant', [this.state.stock.id], {
            'inventory_quantity': this.state.stock.inv_quantity
        })
    }

    _onClickOpenEdit(ev) {
        this.root.el.querySelector('#AdjustmentLinesModal').style.display = 'block'
    }

    /**
     * Function for increment or decrement the quantity of the record by 1
     */
    _onClickDialOperation(operation) {
        if (operation == 'add') {
            this.root.el.querySelector('.input_for_quantity').value = Number(this.root.el.querySelector('.input_for_quantity').value) + 1
        } else {
            this.root.el.querySelector('.input_for_quantity').value = Number(this.root.el.querySelector('.input_for_quantity').value) - 1
        }
        this.is_float = false;
    }

    /**
     * Function for removing the last value from input value
     */
    _onClickDialRemove() {
        var value = this.root.el.querySelector('.input_for_quantity').value
        if (value) {
            if (value.charAt(value.length - 2) == '.') {
                this.root.el.querySelector('.input_for_quantity').value = value.slice(0, -2);
            } else {
                this.root.el.querySelector('.input_for_quantity').value = value.slice(0, -1);
            }
        }
        this.is_float = false;
    }

    /**
     * Function for adding number to value of the input box
     */
    _onclickNumber(number) {
        if (!this.is_float) {
            this.root.el.querySelector('.input_for_quantity').value = this.root.el.querySelector('.input_for_quantity').value + number
        } else {
            this.root.el.querySelector('.input_for_quantity').value = Number(this.root.el.querySelector('.input_for_quantity').value) + "." + Number(number)
            this.is_float = false;
        }
    }

    /**
     * Function for applying the decimal value in the quantity
     */
    _onClickDialDecimal() {
        if (this.root.el.querySelector('.input_for_quantity').value.indexOf('.') === -1) {
            this.is_float = true;
        }
    }

    /**
     * Function for opening the wizard
     */
    _onClickOpenWizard(model, id) {
        this.actionService.doAction({
            type: 'ir.actions.act_window',
            name: 'Product',
            target: 'current',
            res_model: model,
            res_id: Number(id),
            views: [
                [false, 'form']
            ],
        })
    }

    get displayName() {
        return truncateText(this.state.stock?.product_name || "")
    }

    handleEdit() {
        const modal = this.root.el.querySelector('#AdjustmentLinesModal')
        modal.style.display = this.env.isSmall ? 'flex' : 'block';
        if (this.env.isSmall) {
            modal.classList.add("mobile-view")
            modal.querySelector(".input_for_quantity").focus()

        }

    }
}

CustomBarcodeAdjustmentLines.components = {
    Dropdown, DropdownItem
}
CustomBarcodeAdjustmentLines.template = "barcode_for_community.BarcodeAdjustmentLines";
