/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";

/** Extends the public widget class to add the events
*/
const WebsiteSaleBarcode = publicWidget.Widget.extend({
    selector: '.oe_website_sale',
    disabledInEditableMode: false,
    events: {
        'click .o_wsale_apply_barcode ': 'load_quagga',
        'click .close-website-barcode-modal ': '_onClickCloseModal',
    },
    _onClickCloseModal: function () {
        // Get the stream tracks
        var tracks = this.el.querySelector('video').srcObject.getTracks()
        this.el.querySelector('#mapModal').style.display = 'none'
        // Stop track
        tracks.forEach(function (track) {
            track.stop();
        });
    },
    /**
    while clicking scanner button lading the quagga lib
    */
    load_quagga: function (ev) {
        if (this.$el.find('#barcode_id').length > 0 && navigator.mediaDevices && typeof navigator.mediaDevices.getUserMedia === 'function') {
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
                    target: this.el.querySelector('#barcode_id')
                },
                decoder: {
                    readers: ['code_128_reader']
                }
            }, function (err) {
                if (err) {
                    return
                }
                Quagga.start();
            });
            var last_result = [];
            /**
            while detecting the barcode searching for corresponding product
            */
            Quagga.onDetected(function (result) {
                var last_code = result.codeResult.code;
                last_result.push(last_code);
                last_result = [];
                Quagga.stop();
                // Get the stream tracks
                var video = document.querySelector('#barcode_id video');
                if (video && video.srcObject) {
                    var tracks = video.srcObject.getTracks();
                    tracks.forEach(function (track) {
                        track.stop();
                    });
                }

                rpc('/shop/barcodeproduct', {
                    'last_code': result.codeResult.code
                }).then(function (data) {
                    if (data) {
                        if (data.type === 'ir.actions.act_url') {
                            window.location.href = data.url;
                        } else if (data === false) {
                            alert('No Product is available for this barcode.');
                        }
                    } else {
                        alert('No Product is available for this barcode.');
                    }
                });
            });
        }
    },
});

publicWidget.registry.WebsiteSaleBarcode = WebsiteSaleBarcode;
export default WebsiteSaleBarcode;