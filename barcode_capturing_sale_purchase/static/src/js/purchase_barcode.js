/** @odoo-module **/
import { FormController } from "@web/views/form/form_controller";
import { Dialog } from "@web/core/dialog/dialog";
import { BarcodeDialog } from "./barcode_dialog.js";
import { useChildRef, useService } from "@web/core/utils/hooks";
import { Component, onWillUnmount, EventBus } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";

var beep = new Audio('/barcode_capturing_sale_purchase/static/src/audio/beep_scan.mp3');
// Extends FormController for rendering the purchase order form with barcode scanning functionality.
export class ComPurchaseOrderRender extends FormController {
   setup() {
        this.bus = new EventBus();
        this.modalRef = useChildRef();
        this.isProcess = false;
        this.dialog = useService("dialog");
        this.notificationService = useService("notification");
        onWillUnmount(() => {
            if (this.stream) {
                this.stream.getTracks().forEach((track) => track.stop());
                this.stream = null;
            }
        });
        super.setup();
    }
    //    Opens a dialog for barcode scanning.
   async PurchaseBarcodeDialog() {
        var self = this;
        var load_params = self.model.config;
        var model = this.props.resModel
        if(load_params.resId){
            var order_id = load_params.resId;
        }
        else{
            if(load_params.resIds[0]){
                var order_id = load_params.resIds[0];
            }
            else{
                    this.notificationService.add(_t("Create or Save Purchase Order to start barcode scan"), {
                    title: _t("Create/save Order"),
                    type: "danger",
                });
                return
            }
        }
       // Opens a Dialog box for scanning barcode
        const constraints = {
            video: { facingMode: this.props.facingMode },
            audio: false,
        };
        try {
            this.dialog.add(BarcodeDialog, {
                title: _t("Barcode Scanner"),
                body: _t("An administrator needs to configure Google Synchronization before you can use it!"),
                close: true,
                order_id: order_id,
                model: model,
            });
        } catch (err) {
            window.alert('Failed to detect webcam.Please ensure that your browser has the required permissions to access your webcam.')
        }
   }
}
ComPurchaseOrderRender.template = "barcode_capturing_sale_purchase.purchase_scanner";
