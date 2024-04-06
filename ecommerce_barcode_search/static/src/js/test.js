/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";
var ajax = require('web.ajax');
var rpc = require('web.rpc');


publicWidget.registry.WebsiteSaleBarcode = publicWidget.Widget.extend({
    selector: '.oe_website_sale',
    disabledInEditableMode: false,
    events: {
        'click .o_wsale_apply_barcode ': 'load_quagga',
    },

        load_quagga: function (ev) {
             if ($('#barcode_id').length > 0 && navigator.mediaDevices && typeof navigator.mediaDevices.getUserMedia === 'function'){
             console.log(document.querySelector('#barcode_id'))
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
                    target : document.querySelector('#barcode_id')
                },
                decoder: {
                   readers : ['code_128_reader']
                }
                },function(err){
                    if(err){
                    console.log(err);
                    return
                    }
                    Quagga.start();
                });
                var last_result=[];
                var self = this;
                Quagga.onDetected(function(result){
                console.log(result)
                    var last_code = result.codeResult.code;
                    last_result.push(last_code);
                    last_result=[];
                    Quagga.stop();
                   ajax.jsonRpc("/shop/barcodeproduct", 'call',{
                            'last_code':last_code
                            })
                            .then(function(result){
                                if(result == false){
                                    alert('Barcode is not detected.')
                                      }
                                else {
                                 window.location.href=result['url'];
                                 }
                            });
                });
             }
        },
});
