/** @odoo-module */
import { browser } from "@web/core/browser/browser";
import { Dialog } from "@web/core/dialog/dialog";
import { BarcodeDialog } from "./barcode_dialog.js";
import { _t } from "@web/core/l10n/translation";
import { useChildRef, useService } from "@web/core/utils/hooks";
import { Component, onWillUnmount, EventBus } from "@odoo/owl";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";

export class PosProductBarcode extends Component {
    static template = "ProductBarcodePos";
     setup() {
        this.bus = new EventBus();
        this.modalRef = useChildRef();
        this.isProcess = false;
        this.dialog = useService("dialog");
        onWillUnmount(() => {
            if (this.stream) {
                this.stream.getTracks().forEach((track) => track.stop());
                this.stream = null;
            }
        });
        super.setup();
    }
    async onClick() {
            // Opens a Dialog box for scanning barcode
            var self = this;
            const constraints = {
                video: { facingMode: this.props.facingMode },
                audio: false,
            };
            try {
                this.dialog.add(BarcodeDialog, {
                    title: _t("Barcode Scanner"),
                    body: _t("An administrator needs to configure Google Synchronization before you can use it!"),
                    size: 'medium',
                    close: true,
                });
            } catch (err) {
                window.alert('Failed to detect webcam.Please ensure that your browser has the required permissions to access your webcam.')
            }
    }
}
PosProductBarcode.components = { BarcodeDialog };
ProductScreen.addControlButton({
    component: PosProductBarcode,
    condition: function () {
        return true
    },
});
