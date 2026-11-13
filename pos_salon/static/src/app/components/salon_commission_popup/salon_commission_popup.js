import { Component, useState } from "@odoo/owl";

export class SalonCommissionPopup extends Component {
    static template = "pos_salon.SalonCommissionPopup";
    static props = { actions: Object };

    setup() {
        this.state = useState(this.props.actions.state);
    }
}