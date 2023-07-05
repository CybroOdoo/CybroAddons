/** @odoo-module **/
const { useListener } = require("@web/core/utils/hooks");
const Dialog = require('web.Dialog');
import { _t } from 'web.core';
import PosComponent from 'point_of_sale.PosComponent';
import Registries from 'point_of_sale.Registries';
import ProductScreen from 'point_of_sale.ProductScreen';
import { Gui } from 'point_of_sale.Gui';
class PosProductBarcode extends PosComponent {
    setup() {
        super.setup();
        useListener('click', this.onClick);
    }
//    Click function of barcode button
    async onClick() {
        var video = document.createElement('video');
        var product;
        var self = this
        video.setAttribute('id', 'barcode_id')
        document.body.appendChild(video);
        try{
        await navigator.mediaDevices.getUserMedia({ video: true }).then(function (stream) {
            video.srcObject = stream;
            video.play();
            //Create a new dialog box and open.
            const dialog = new Dialog(this, {
                title: 'Barcode Scanner',
                buttons:
                    [{
                        text: _t('Close'), close: true, click: function () {
                            Quagga.stop();
                            dialog.close();
                            var tracks = video.srcObject.getTracks();
                            // Stop tracking
                            tracks.forEach(function (track) {
                                track.stop();
                            });
                        }
                    }],
                size: 'medium',
                $content: video,
            });
//            opening dialog box
            dialog.open();
//            initialising quagga
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
                    target: video,
                },
                decoder: {
                    readers: ['code_128_reader']
                }
            },function (err) {
                if (err) {
                    console.log(err);
                    return
                }
                Quagga.start();
            });
//            quagga barcode detection function
            Quagga.onDetected(function (result) {
                var barcode = result.codeResult.code;
                Quagga.offDetected();
                Quagga.stop();
                self.scan_product(barcode)
                dialog.close();
                // Get the stream tracks
                var tracks = video.srcObject.getTracks();
                // Stop track
                tracks.forEach(function (track) {
                    track.stop();
                });
            });
        });
        }
//        popup to show if browser has no camera access
        catch(ex){
            this.showPopup('ConfirmPopup', {
                'title': ('Access Denied'),
                'body': ('Failed to detect webcam.Please ensure that your browser has the required permissions to access your webcam.'),
            });
        }
    }
//    Add scanned product into order line
    scan_product(barcode) {
        var product = this.env.pos.db.get_product_by_barcode(barcode);
        var order = this.env.pos.get_order();
        if (product) {
            order.add_product(product);
        } else {
            Gui.showPopup('ConfirmPopup', {
                'title': ('Product Not found'),
                'body': ('No Product with this Barcode.'),
            });
        }
    }
}
PosProductBarcode.template = 'ProductBarcodePos';
ProductScreen.addControlButton({
    component: PosProductBarcode,
    condition: () => true,
});
Registries.Component.add(PosProductBarcode);