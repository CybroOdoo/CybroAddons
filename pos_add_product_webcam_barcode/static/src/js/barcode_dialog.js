/** @odoo-module */

import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { browser } from "@web/core/browser/browser";
import { Dialog } from "@web/core/dialog/dialog";
import { _t } from "@web/core/l10n/translation";
import { useChildRef } from "@web/core/utils/hooks";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { Component, useRef } from "@odoo/owl";
export class BarcodeDialog extends Component {
    async setup() {
          super.setup();
                this.env.dialogData.dismiss = () => this._cancel();
                this.pos = usePos();
                this.modalRef = useChildRef();
                this.videoPreviewRef = useRef("videoPreview")
                this.stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
                this.videoPreviewRef.el.srcObject = this.stream;
                var self = this
                this.videoPreviewRef.el.play()
                  Quagga.init({
                    inputStream: {
                        name: "Live",
                        type: "LiveStream",
                        constraints: {
                            video: {
                                facingMode: {
                                    exact: "environment"
                                }
                            }
                        },
                        numOfWorkers: navigator.hardwareConcurrency,
                        target: this.videoPreviewRef.el,
                    },
                    decoder: {
                        readers: ['code_128_reader']
                    }
                }, function(err) {
                    if (err) {
                        return
                    }
                    Quagga.start();
                })
                Quagga.onDetected(function(result) {
                    var barcode = result.codeResult.code;
                    Quagga.offDetected();
                    Quagga.stop();
                    self.scan_product(barcode)
                });
    }
     /**
     * Handle the cancel action.
     */
    async _cancel() {
        return this.execButton(this.props.cancel);
    }
     /**
     * Handle the onClick event for the Confirm button in the dialog.
     */
    async _dialogConfirm() {
        return this.execButton(this.props.confirm);
    }
    scan_product(barcode) {
        // Scan the barcode and adding in to the order line
        var product = this.pos.db.get_product_by_barcode(barcode);
        var order = this.pos.get_order();
        if (product) {
          order.add_product(product);
        }
        else {
             this.pos.popup.add(ErrorPopup, {
                 'title': ('Product Not found'),
                 'body': ('No Product with this Barcode'),
             });
        }
        var video = this.videoPreviewRef.el
        var tracks = video.srcObject.getTracks();
        tracks.forEach(function(track) {
            track.stop();
        });
        this.props.close();
    }
    /**
     * Set the disabled state of buttons in the dialog footer.
     */
     setButtonsDisabled(disabled) {
        this.isProcess = disabled;
        if (!this.modalRef.el) {
            return;
        }
        for (const button of [...this.modalRef.el.querySelectorAll(".modal-footer button")]) {
            button.disabled = disabled;
        }
    }
     /**
     * Execute a button callback, handle the disabled state, and close the dialog if needed.
     */
    async execButton(callback) {
        if (this.isProcess) {
            return;
        }
        this.setButtonsDisabled(true);
        if (callback) {
            let shouldClose;
            try {
                shouldClose = await callback();
            } catch (e) {
                this.props.close();
                throw e;
            }
            if (shouldClose === false) {
                this.setButtonsDisabled(false);
                return;
            }
        }
        this.props.close();
    }
}
BarcodeDialog.template = "BarcodeDialog";
BarcodeDialog.components = { Dialog };
BarcodeDialog.props = {
    close: Function,
    title: {
        validate: (m) => {
            return (
                typeof m === "string" || (typeof m === "object" && typeof m.toString === "function")
            );
        },
        optional: true,
    },
    body: String,
    confirm: { type: Function, optional: true },
    confirmLabel: { type: String, optional: true },
    confirmClass: { type: String, optional: true },
    cancel: { type: Function, optional: true },
    cancelLabel: { type: String, optional: true },
};
BarcodeDialog.defaultProps = {
    confirmLabel: _t("Ok"),
    cancelLabel: _t("Cancel"),
    confirmClass: "btn-primary",
    title: _t("Confirmation"),
};
