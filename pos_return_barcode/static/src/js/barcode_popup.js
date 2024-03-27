/** @odoo-module **/
/**
 * Defines BarcodePopup  extending from AbstractAwaitablePopup for scanning barcode
 */
import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
import { _lt } from '@web/core/l10n/translation';
import  { onMounted, useRef, useState } from "@odoo/owl";


class BarcodePopup extends AbstractAwaitablePopup {
    setup() {
        super.setup();
        this.state = useState({
            barcodeValue:this.props.startingValue
        });
        this.barcode = useRef('barcode');
        onMounted(this.onMounted);
    }
    onMounted() {
        this.barcode.el.focus();
    }
    getPayload() {
        return {
            barcodeValue: this.state.barcodeValue,
        };
    }
}
BarcodePopup.template = 'BarcodePopup';
BarcodePopup.defaultProps = {
    confirmText: _lt('Confirm'),
    cancelText: _lt('Cancel'),
    title: '',
    body: '',
};
export default BarcodePopup;
