/** @odoo-module */
import { rpc } from "@web/core/network/rpc";
import { Component } from "@odoo/owl";
import { loadJS } from "@web/core/assets";
import { registry } from "@web/core/registry";
import { useRef } from "@odoo/owl";

var beep = new Audio('/machine_repair_barcode_scanner/static/src/audio/beep_scan.mp3');
var scanSuccessful = false;

class barcode_scanner extends Component {
    setup() {
        super.setup();
        this.quaggaPromise = loadJS(
            "/machine_repair_barcode_scanner/static/src/js/quagga.js"
        );
        this.rpc = rpc;
        this.scanModal = useRef("barcode_id");
        this.barcode = useRef("barcode");
    }
    openModal(ev) {
        const self = this;
        const params = this.props.action.context;

        if (!params || !params.active_id) {
            self.env.services.action.doAction({
                type: "ir.actions.client",
                tag: "display_notification",
                params: {
                    title: "No active order!",
                    message: "Select an order first",
                    type: "danger",
                }
            });
            return;
        }

        const order_id = params.active_id;
        const product = document.getElementById("product").checked ? "machine" : "parts";

        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            self.env.services.action.doAction({
                type: "ir.actions.client",
                tag: "display_notification",
                params: {
                    title: "Camera not available",
                    message: "Check browser permissions",
                    type: "warning",
                }
            });
            return;
        }

        const Quagga = window.Quagga;

        Quagga.init({
            inputStream: {
                name: "Live",
                type: "LiveStream",
                target: document.querySelector("#barcode_id"),
                constraints: {
                    facingMode: "environment",
                    width: { ideal: 1280 },
                    height: { ideal: 720 }
                }
            },
            locate: true,
            decoder: {
                readers: [
                    "code_128_reader",
                    "ean_reader"
                ]
            }
        }, function (err) {
            if (err) {
                console.error("Quagga init error:", err);
                return;
            }
            Quagga.start();
        });

        const votes = {};
        const REQUIRED_MATCHES = 3;
        scanSuccessful = false;

        Quagga.onDetected(function (result) {
            if (scanSuccessful) return;
            const cr = result.codeResult;
            if (!cr || !cr.code) return;
            if (cr.format === "code_128" && cr.direction === -1) return;
            if (cr.format === "code_128" && cr.code.length < 6) return;
            const decoded = cr.decodedCodes || [];
            const dataSymbols = decoded.filter(d => ![103, 104, 105, 106].includes(d.code));
            if (dataSymbols.length < 3) return;
            const avgError = decoded.reduce((s, d) => s + (d.error || 0), 0) / decoded.length;
            if (avgError > 0.15) return;
            const code = cr.code;
            votes[code] = (votes[code] || 0) + 1;
            beep.play();
            if (votes[code] < REQUIRED_MATCHES) return;
            scanSuccessful = true;
            Quagga.stop();
            self.scanModal.el.style.visibility = "hidden";
            rpc("/barcode_search/machine", {
                last_code: code,
                order_id: order_id,
                product: product,
            }).then(function (data) {
                if (!data) {
                    self.env.services.action.doAction({
                        type: "ir.actions.client",
                        tag: "display_notification",
                        params: {
                            title: "Barcode not detected. Scan again!",
                            message: "Code: " + code,
                            type: "warning",
                        }
                    });
                    scanSuccessful = false;
                    votes[code] = 0;
                    Quagga.start();
                    self.scanModal.el.style.visibility = "visible";
                } else {
                    self.env.services.action.doAction({
                        type: "ir.actions.client",
                        tag: "display_notification",
                        params: {
                            title: "Barcode Scanned Successfully!",
                            message: "Code: " + code,
                            type: "success",
                        }
                    });
                    setTimeout(() => {
                        location.reload();
                    }, 700);
                }
            }).catch(function (err) {
                console.error("RPC Error:", err);
                scanSuccessful = false;
            });
        });
    }
    closeButton(ev) {
        if (window.Quagga) {
            window.Quagga.stop();
        }
        this.scanModal.el.style.visibility = 'hidden';
        scanSuccessful = false;
    }
}

barcode_scanner.template = 'BarCodeScanner';
registry.category("actions").add("scan_barcode", barcode_scanner);
