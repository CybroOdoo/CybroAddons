odoo.define('barcode_capturing_sale_purchase.purchase_barcode', function (require) {
	var Widget= require('web.Widget');
	var widgetRegistry = require('web.widget_registry');
	var FieldManagerMixin = require('web.FieldManagerMixin');
	const Dialog = require('web.Dialog');
	var core = require('web.core');
	const _t = core._t;
	var rpc = require('web.rpc');
	var beep = new Audio('/barcode_capturing_sale_purchase/static/src/audio/beep_scan.mp3');

    var PurchaseOrderBarcode = Widget.extend(FieldManagerMixin, {
        init: function (parent, model, context) {
            this._super(parent);
            FieldManagerMixin.init.call(this);
            this._super.apply(this, arguments);
            document.addEventListener('click', this._onClickGlobal.bind(this));
        },
        /**
        * Function will be executed when the barcode icon is clicked from the purchase form view and camera is opened to scan the barcode
        * through camera.
        *
        * @param {ev} it contains the target when mouse is clicked and it checks in function if barcode icon is clicked.
        */
        _onClickGlobal(ev){
            var self = this;
            var target = ev.target;
            if(target.id == 'purchase_barcode_btn'){
                var video = document.createElement('video');
                video.setAttribute('id', 'barcode_id')
                navigator.mediaDevices.getUserMedia({ video: true })
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
                        var order_id = self.__parentedParent.allFieldWidgets['purchase.order_1'][0].res_id
                        rpc.query({model: "purchase.order", method: "barcode_search", args: [[last_code, order_id]]
                        })
                        .then(function (data) {
                            if(data == true){
                                alert("Product with the scanned Barcode Not Found in the system")
                                return;
                            }
                        });
                    });
                });
            }
        },
    });
    widgetRegistry.add(
        'purchase_barcode', PurchaseOrderBarcode
    );
});