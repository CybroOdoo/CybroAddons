/** @odoo-module */
import { browser } from "@web/core/browser/browser";
import { Dialog } from "@web/core/dialog/dialog";
import { _t } from "@web/core/l10n/translation";
import { useService } from '@web/core/utils/hooks';
import { useChildRef } from "@web/core/utils/hooks";
import { Component, onMounted, useRef, useState, onWillUnmount } from "@odoo/owl";
export class BarcodeDialog extends Component {
    setup() {
        this.videoPreviewRef = useRef("videoPreview")
        this.env.dialogData.dismiss = () => this._cancel();
        this.modalRef = useChildRef();
        this.isProcess = false;
        this.sound = useService("barcodeSound");
        this.state = useState({
            alert: ""
        })
        onWillUnmount(() => {
            try {
                Quagga.offDetected();
                Quagga.stop();
            } catch (err) {
                // Quagga may already be stopped; ignore the error gracefully
            }
            if (this.stream) {
                this.stream.getTracks().forEach((track) => track.stop());
                this.stream = null;
            }
        });
        onMounted(async () => {
            var self = this;
            var video = this.videoPreviewRef.el
            if (!browser.navigator?.mediaDevices?.getUserMedia) {
                this.sound.Danger.play().catch(() => { });
                if (video) {
                    video.remove();
                }
                this.state.alert = _t("Failed to detect webcam: MediaDevices API is not supported or the page is not served over HTTPS.");
                return;
            }
            const constraints = {
                video: {
                    facingMode: this.props.facingMode || "environment"
                },
                audio: false,
            };
            try {
                this.stream = await browser.navigator.mediaDevices.getUserMedia(constraints);
                if (video) {
                    video.srcObject = this.stream;
                    video.play().catch((playErr) => {
                        // Autoplay blocked: the video element stays paused without user interaction
                    });
                }
                Quagga.init({
                    inputStream: {
                        name: "Live",
                        type: "LiveStream",
                        constraints: {
                            video: {
                                facingMode: this.props.facingMode || "environment"
                            }
                        },
                        numOfWorkers: navigator.hardwareConcurrency,
                        target: video,
                    },
                    decoder: {
                        readers: [
                            'code_128_reader',
                            'ean_reader',
                            'ean_8_reader',
                            'code_39_reader',
                            'upc_reader',
                            'upc_e_reader'
                        ]
                    }
                }, function (err) {
                    if (err) {
                        return
                    }
                    Quagga.start();
                })
                Quagga.onDetected(function (result) {
                    var barcode = result.codeResult.code;
                    Quagga.offDetected();
                    Quagga.stop();
                    self.ReadBarcode(barcode)
                    // Get the stream tracks
                });
            } catch (err) {
                this.sound.Danger.play().catch(() => { });
                if (this.videoPreviewRef.el) {
                    this.videoPreviewRef.el.remove()
                }
                // Surface the camera error to the user via the alert state
                this.state.alert = _t("Failed to detect webcam (Error: ") + (err.name || "Unknown") + " - " + (err.message || "") + _t("). Please ensure that your webcam is connected, not in use by another app, and that your browser has permissions.");
            }
        })
    }

    /**
     * Function for passing code to the parent component
     */
    ReadBarcode(code) {
        if (this.stream) {
            this.stream.getTracks().forEach((track) => track.stop());
            this.stream = null;
        }
        const video = this.videoPreviewRef.el;
        if (video) {
            video.srcObject = null;
        }
        this.props.close();
        this.props.ReadBarcode(code);
    }
    /**
     * Function for dismiss dialogue
     */
    async _cancel() {
        return this.execButton(this.props.cancel);
    }
    /**
     * Function for dismiss dialogue
     */
    async OnclickConfirmDialogue() {
        return this.execButton(this.props.confirm);
    }
    /**
     * Function for disabling footer buttons
     */
    setButtonsDisabled(disabled) {
        this.isProcess = disabled;
        if (!this.modalRef.el) {
            return; // safety belt for stable versions
        }
        for (const button of [...this.modalRef.el.querySelectorAll(".modal-footer button")]) {
            button.disabled = disabled;
        }
    }
    /**
     * Function for dismiss dialogue
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
BarcodeDialog.components = {
    Dialog
};
BarcodeDialog.props = {
    close: {
        type: Function,
        optional: true
    },
    title: {
        validate: (m) => {
            return (
                typeof m === "string" || (typeof m === "object" && typeof m.toString === "function")
            );
        },
        optional: true,
    },
    confirm: {
        type: Function,
        optional: true
    },
    confirmLabel: {
        type: String,
        optional: true
    },
    ReadBarcode: {
        type: Function,
        optional: true
    },
    confirmClass: {
        type: String,
        optional: true
    },
    cancel: {
        type: Function,
        optional: true
    },
    cancelLabel: {
        type: String,
        optional: true
    },
};
BarcodeDialog.defaultProps = {
    confirmLabel: _t("Ok"),
    cancelLabel: _t("Cancel"),
    confirmClass: "btn-primary",
    title: _t("Confirmation"),
    ReadBarcode: () => { }
};