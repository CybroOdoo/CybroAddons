import { Component } from '@odoo/owl';

export class QuantityButtons extends Component {
    static template = 'purchase_product_configurator.QuantityButtons';
    static props = {
        quantity: Number,
        setQuantity: Function,
        isMinusButtonDisabled: { type: Boolean, optional: true },
        isPlusButtonDisabled: { type: Boolean, optional: true },
        btnClasses: { type: String, optional: true },
    };

    increaseQuantity() {
        this.props.setQuantity(this.props.quantity + 1);
    }

    decreaseQuantity() {
        this.props.setQuantity(this.props.quantity - 1);
    }

    async setQuantity(ev) {
        const quantity = parseFloat(ev.target.value);
        const didUpdateQuantity = await this.props.setQuantity(isNaN(quantity) ? 0 : quantity);
        if (!didUpdateQuantity) {
            this.render();
        }
    }
}
