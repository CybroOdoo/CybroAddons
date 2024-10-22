/** @odoo-module */

/*
Machine repair barcode scanner.
*/
import { jsonrpc } from "@web/core/network/rpc_service";
import { Component } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { useRef } from "@odoo/owl";
var beep = new Audio('/machine_repair_barcode_scanner/static/src/audio/beep_scan.mp3');
var scanSuccessful = false;

class barcode_scanner extends Component {
/*
    Open barcode scanner Window
*/
       setup() {
        super.setup();
        this.scanModal = useRef("barcode_id");
        this.barcode = useRef("barcode");
        }
       openModal(ev){
            this.scanModal.el.style.visibility = 'visible';
            var self = this;
            var params = this.props.action.context;
            if (params && params.active_id) {
                var order_id = this.props.action.context.active_id
                var product = document.getElementById('product').checked ? "machine" : "parts";
                 if (navigator.mediaDevices && typeof navigator.mediaDevices.getUserMedia === 'function'){
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
                    return
                    }
                    Quagga.start();
                }
                );
                var last_result=[];
                Quagga.onDetected(function(result){
                    if (scanSuccessful) {
                        return;  // Stop processing if a successful scan has already occurred
                    }
                    var last_code = result.codeResult.code;
                    console.log(result,'ooooooooooooooooo')
                    console.log(result.codeResult,'ooooooooooooooooo')
                    beep.play();
                    Quagga.stop();
                    self.scanModal.el.style.visibility = 'hidden';
                    if(product){
                    jsonrpc('/barcode_search/machine', {
                    'last_code': last_code,
                    'order_id': order_id,
                    'product': product,
                    }).then(function (data) {
                        if(data== false){
                            self.env.services.action.doAction({
                                'type': 'ir.actions.client',
                                'tag': 'display_notification',
                                'params': {
                                    'title': 'Barcode is not detected.Scan again!',
                                    'message': "Barcode",
                                    'type': 'danger',
                                    'sticky': false,
                                }
                            });
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
                 self.env.services.action.doAction({
                                'type': 'ir.actions.client',
                                'tag': 'display_notification',
                                'params': {
                                    'title': 'Try agai!',
                                    'message': "Barcode",
                                    'type': 'danger',
                                    'sticky': false,
                                }
                            });
                  location.reload();
            }
        }
        /* Close Scanner */
        closeButton(ev){
            Quagga.stop();
            this.scanModal.el.style.visibility = 'hidden';
        }
    }
barcode_scanner.template = 'BarCodeScanner';
registry.category("actions").add("scan_barcode", barcode_scanner);
