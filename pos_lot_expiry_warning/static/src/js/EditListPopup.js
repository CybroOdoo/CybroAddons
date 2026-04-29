/** @odoo-module */
import { Dialog } from "@web/core/dialog/dialog";
import { _t } from "@web/core/l10n/translation";
import { Component, useState } from "@odoo/owl";

export class LotListPopup extends Component {
    static components = { Dialog };
    static template = "pos_lot_expiry_warning.LotListPopup";
    static props = {
        title: String,
        name: String,
        lotStock: { type: Array, optional: true },
        getPayload: Function,
        close: Function,
        isSingleItem: { type: Boolean, optional: true },
    };
    static defaultProps = {
        lotStock: [],
        isSingleItem: false,
    };
    setup() {
        this.state = useState({
            lot_id: false
        })
    }
    confirm() {
        this.props.getPayload({
            newArray: [{ text: this.state.lot_id, _id: 0 }]
        });
        this.props.close();
    }
    cancel() {
        this.props.close();
    }
};
