/** @odoo-module **/

import { FormRenderer } from "@web/views/form/form_renderer";
const Dialog = require('web.Dialog');
import { useService } from "@web/core/utils/hooks";
import rpc from 'web.rpc';
import core from 'web.core';
const _t = core._t;
var beep = new Audio('/barcode_capturing_sale_purchase/static/src/audio/beep_scan.mp3');
export class ComPurchaseOrderRender extends FormRenderer {
    setup() {
        this.notification = useService("notification");
        super.setup();
    }
//    Onclick of the barcode button this function is executed which creates a new window with video capture using
//    quagga function, which will capture barcode shown to it.
//    The result of barcode will be added to the corresponding purchase order.
    async PurchaseBarcodeDialog(){
        var self = this;
        var load_params = self.props.record.__bm_load_params__;
        if(load_params.res_id){
            var order_id = load_params.res_id;
        }
        else{
            if(load_params.res_ids[0]){
                var order_id = load_params.res_ids[0];
            }
            else{
                this.notification.add(this.env._t("Create or Save Purchase Order to start barcode scan"), {
                    title: this.env._t("Create/save Order"),
                    type: "danger",
                });
                return
            }
        }
        var video = document.createElement('video');
        video.setAttribute('id', 'barcode_id')
        await navigator.mediaDevices.getUserMedia({ video: true })
        .then(function (stream) {
            video.srcObject = stream;
            video.play();
            const dialog = new Dialog(this, {
            title: 'Barcode Scanner',
            buttons:
                [{
                    text: _t('close'), classes: 'btn-primary', close: true, click: function () {
                        Quagga.stop();
                        dialog.close();
                        var tracks = video.srcObject.getTracks();
                            tracks.forEach(function(track) {
                                track.stop();
                            });
                    }
                }],
            size: 'medium',
            $content: video,
            });
            dialog.open();
            Quagga.init({
                inputStream : {
                    name : "Live",
                    type : "LiveStream",
                    constraints: {
                        video: {
                            facingMode: {
                              exact: "environment"
                            }
                        }
                    },
                    numOfWorkers : navigator.hardwareConcurrency,
                    target : video
                },
                decoder: {
                   readers : ['code_128_reader']
                }
            },
                function(err){
                    if(err){
                    console.log(err);
                    return
                    }
                    Quagga.start();
                }
            );
            var last_result=[];
            Quagga.onDetected(function(result){
                var last_code = result.codeResult.code;
                last_result.push(last_code);
                last_result=[];
                beep.play();
                Quagga.stop();
                dialog.close();
                var tracks = video.srcObject.getTracks();
                    tracks.forEach(function(track) {
                    track.stop();
                });
                rpc.query({model: "purchase.order", method: "barcode_search", args: [[last_code, order_id]]
                })
                .then(function (data) {
                    if(data == true){
                        self.notification.add(self.env._t("Product with the scanned Barcode Not Found in the system"), {
                            title: self.env._t("Product Not Found!"),
                            type: "danger",
                        });
                    }
                });
            });
        });
    }
}
