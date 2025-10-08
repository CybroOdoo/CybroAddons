odoo.define('machine_repair_barcode_scanner.scan_repair_barcode', function (require){
"Use strict";
/*
Machine repair barcode scanner.
*/
var core = require('web.core');
var rpc = require('web.rpc');
var AbstractAction = require('web.AbstractAction');
var beep = new Audio('/machine_repair_barcode_scanner/static/src/audio/beep_scan.mp3');
var scanSuccessful = false;
var BarcodeScanner = AbstractAction.extend({
/*
    Open barcode scanner Window
*/
 contentTemplate: 'BarCodeScanner',
        events: {
        'click #repair-barcode-scanner': 'load_qr',
        'click #close-button': 'closeButton',
        },
        load_qr: function (ev) {
        var self = this;
        var params = self.searchModel.config.context.params;
        if (params && params.id) {
        var order_id = self.searchModel.config.context.params.id
        var product = document.getElementById('product').checked ? "machine" : "parts";
         if (this.$el.find('#barcode_id').length > 0 && navigator.mediaDevices && typeof navigator.mediaDevices.getUserMedia === 'function'){
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
            Quagga.onDetected(function(result){
                if (scanSuccessful) {
                    return;  // Stop processing if a successful scan has already occurred
                }
                var last_code = result.codeResult.code;
                beep.play();
                Quagga.stop();
                self.$el.find('#mapModal').hide();
                if(product){
                rpc.query({model: "machine.repair", method: "barcode_search", args: [[last_code, order_id,product]]
                            }).then(function (data) {
                if(data== false){
                self.displayNotification({ title: 'Barcode is not detected.Scan again!', type: 'warning' });
                         }
                else{
                    scanSuccessful = true;
                    location.reload();
                    }
                });
                 }
            });
            }
         }
        else{
          self.displayNotification({ title: 'Try again', type: 'warning' });
          location.reload();
            }
        },
        /* Close Scanner */
        closeButton: function(ev){
        Quagga.stop();
        this.$el.find('#mapModal').hide();
        },
    });
    core.action_registry.add('scan_barcode', BarcodeScanner);
});
