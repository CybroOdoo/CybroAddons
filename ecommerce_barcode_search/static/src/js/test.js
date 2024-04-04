/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.WebsiteSaleBarcode = publicWidget.Widget.extend({
    selector: '.oe_website_sale',
    disabledInEditableMode: false,
    events: {
        'click .o_wsale_apply_barcode ': 'load_quagga',
    },
    init() {
        this._super(...arguments)
        this.rpc = this.bindService("rpc");
         },
        load_quagga: function (ev) {
             if ($('#barcode_id').length > 0 && navigator.mediaDevices && typeof navigator.mediaDevices.getUserMedia === 'function'){
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
                    var last_code = result.codeResult.code;
                    last_result.push(last_code);
                    last_result=[];
                    Quagga.stop();
                   self.rpc("/shop/barcodeproduct", {
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
