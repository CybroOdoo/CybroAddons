/** @odoo-module */
import { rpc } from "@web/core/network/rpc";
import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useRef } from "@odoo/owl";

var beep = new Audio('/machine_repair_barcode_scanner/static/src/audio/beep_scan.mp3');
var scanSuccessful = false;
var quaggaRunning = false;

class barcode_scanner extends Component {
    setup() {
        super.setup();
        this.rpc = rpc;
        this.scanModal = useRef("barcode_id");
        this.scannerTarget = useRef("scanner_target");
    }

    async openModal(ev) {
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
        const productCheckbox = document.getElementById("product");
        const product = productCheckbox && productCheckbox.checked ? "machine" : "parts";

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
        if (!Quagga) {
            console.error("Quagga is not loaded.");
            return;
        }

        if (quaggaRunning) {
            try {
                Quagga.offDetected();
                Quagga.stop();
            } catch (e) {}
            quaggaRunning = false;
        }

        const targetEl = self.scannerTarget.el;
        targetEl.innerHTML = "";
        self.scanModal.el.style.display = "block";

        scanSuccessful = false;
        const votes = {};

        Quagga.init({
            inputStream: {
                name: "Live",
                type: "LiveStream",
                target: targetEl,
                constraints: {
                    facingMode: "environment",
                    width: { ideal: 1280 },
                    height: { ideal: 720 }
                }
            },
            locate: true,
            numOfWorkers: navigator.hardwareConcurrency || 4,
            frequency: 10,  // process 10 frames/sec
            decoder: {
                readers: [
                    "ean_reader",
                    "ean_8_reader",
                    "code_128_reader",
                    "code_39_reader",
                    "upc_reader",
                ]
            },
            locator: {
                patchSize: "medium",
                halfSample: true,
            },
        }, function(err) {
            if (err) {
                console.error("Quagga init error:", err);
                self.env.services.action.doAction({
                    type: "ir.actions.client",
                    tag: "display_notification",
                    params: {
                        title: "Camera Error",
                        message: err.message || "Could not start camera",
                        type: "danger",
                    }
                });
                self.scanModal.el.style.display = "none";
                return;
            }
            Quagga.start();
            quaggaRunning = true;
        });

        Quagga.offDetected();

        // Draw detection boxes so you can see if Quagga finds the barcode region
        Quagga.onProcessed(function(result) {
            const drawingCtx = Quagga.canvas.ctx.overlay;
            const drawingCanvas = Quagga.canvas.dom.overlay;
            if (!drawingCtx || !drawingCanvas) return;

            drawingCtx.clearRect(
                0, 0,
                parseInt(drawingCanvas.getAttribute("width")),
                parseInt(drawingCanvas.getAttribute("height"))
            );

            if (result) {
                if (result.boxes) {
                    result.boxes
                        .filter(box => box !== result.box)
                        .forEach(box => {
                            Quagga.ImageDebug.drawPath(box, { x: 0, y: 1 }, drawingCtx, {
                                color: "green",
                                lineWidth: 2,
                            });
                        });
                }
                if (result.box) {
                    Quagga.ImageDebug.drawPath(result.box, { x: 0, y: 1 }, drawingCtx, {
                        color: "#00F",
                        lineWidth: 2,
                    });
                }
                if (result.codeResult && result.codeResult.code) {
                    Quagga.ImageDebug.drawPath(result.line, { x: "x", y: "y" }, drawingCtx, {
                        color: "red",
                        lineWidth: 3,
                    });
                }
            }
        });

        Quagga.onDetected(function(result) {
            if (scanSuccessful) return;

            const cr = result.codeResult;
            if (!cr || !cr.code) return;

            // Relaxed error threshold
            const decoded = cr.decodedCodes || [];
            if (decoded.length > 0) {
                const avgError = decoded
                    .filter(d => d.error !== undefined)
                    .reduce((s, d) => s + d.error, 0) / decoded.length;
                if (avgError > 0.25) return;  // relaxed from 0.15 → 0.25
            }

            const code = cr.code;
            votes[code] = (votes[code] || 0) + 1;
            console.log("Candidate:", code, "votes:", votes[code]);  // debug

            if (votes[code] < 2) return;  // reduced from 3 → 2

            scanSuccessful = true;
            quaggaRunning = false;
            Quagga.offDetected();
            Quagga.offProcessed();
            Quagga.stop();
            beep.play();
            self.scanModal.el.style.display = "none";

            rpc("/barcode_search/machine", {
                last_code: code,
                order_id: order_id,
                product: product,
            }).then(function(data) {
                if (!data) {
                    self.env.services.action.doAction({
                        type: "ir.actions.client",
                        tag: "display_notification",
                        params: {
                            title: "Barcode not found. Scan again!",
                            message: "Code: " + code,
                            type: "warning",
                        }
                    });
                    scanSuccessful = false;
                    votes[code] = 0;
                    self.openModal(ev);
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
                    setTimeout(() => location.reload(), 700);
                }
            }).catch(function(err) {
                console.error("RPC Error:", err);
                scanSuccessful = false;
                quaggaRunning = false;
            });
        });
    }

    closeButton(ev) {
        const Quagga = window.Quagga;
        if (Quagga && quaggaRunning) {
            try {
                Quagga.offDetected();
                Quagga.offProcessed();
                Quagga.stop();
            } catch (e) {}
            quaggaRunning = false;
        }
        this.scanModal.el.style.display = "none";
        scanSuccessful = false;
    }
}

barcode_scanner.template = 'BarCodeScanner';
registry.category("actions").add("scan_barcode", barcode_scanner);
