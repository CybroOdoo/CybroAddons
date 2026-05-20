/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";
import { loadJS } from "@web/core/assets";
import { rpc } from "@web/core/network/rpc";

publicWidget.registry.WebsiteSaleBarcode = publicWidget.Widget.extend({
    selector: ".oe_website_sale",
    disabledInEditableMode: false,
    events: {
        "click .o_wsale_apply_barcode": "load_quagga",
    },
    init() {
        this._super(...arguments);
        loadJS("https://cdn.jsdelivr.net/npm/@ericblade/quagga2@1.8.4/dist/quagga.min.js");
    },
    load_quagga: function (ev) {
        if (
            $("#barcode_id").length > 0 &&
            navigator.mediaDevices &&
            typeof navigator.mediaDevices.getUserMedia === "function"
        ) {
            Quagga.init(
                {
                    inputStream: {
                        name: "Live",
                        type: "LiveStream",
                        constraints: {
                            video: {
                                facingMode: {
                                    exact: "environment",
                                },
                            },
                        },
                        numOfWorkers: navigator.hardwareConcurrency,
                        target: document.querySelector("#barcode_id"),
                    },
                    decoder: {
                        readers: ["code_128_reader"],
                    },
                },
                function (err) {
                    if (err) {
                        console.log(err);
                        return;
                    }
                    Quagga.start();
                }
            );
            let last_result = [];
            let self = this;
            Quagga.onDetected(function (result) {
                let last_code = result.codeResult.code;
                last_result.push(last_code);
                last_result = [];
                Quagga.stop();
                rpc("/shop/barcode/product", { last_code: last_code }).then(function (result) {
                    $("#barcodeModal").modal("hide"); // Close the barcode modal
                    if (!result) {
                    // If no product is found, show the new modal
                        $("#noProductModal").modal("show");
                    } else {
                        window.location.href = result["url"];
                    }
                });
            });
        }
    },
});
