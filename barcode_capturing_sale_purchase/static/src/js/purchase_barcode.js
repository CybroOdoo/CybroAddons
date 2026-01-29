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
        },
        start: function () {
            this._super.apply(this, arguments);
            const iElement = document.createElement('i')
            iElement.classList.add("fa", "fa-barcode",  "i_class_barcode")
            this.el.append(iElement)
            const buttonEl = document.createElement('button')
            buttonEl.classList.add('purchase_barcode_btn_new')
            buttonEl.innerText = 'Scan Barcode'
            this.el.append(buttonEl)
            buttonEl.addEventListener('click', this._onClickGlobal.bind(this))
        },
        /*  Onclick of the barcode button this function is executed which creates a new window with video capture using
        /*    quagga function, which will capture barcode shown to it.
        /*    The result of barcode will be added to the corresponding purchase order.
        */
        _onClickGlobal(ev){
            var self = this;
            var target = ev.target;
            if(true){
                var allFieldWidget = this.__parentedParent.allFieldWidgets;
                var key=Object.keys(allFieldWidget)
                var res_key = key[0]
                var res_id = this.__parentedParent.allFieldWidgets[res_key][0].res_id
                if(!res_id)
                {
                  alert("Save the order before scanning the product")
                  return;
                }
                else
                {
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
                            rpc.query({model: "purchase.order", method: "barcode_search", args: [[last_code, res_id]]
                            })
                            .then(function (data) {
                                if(data == true){
                                    alert("Product with the scanned Barcode Not Found in the system")
                                    return;
                                }
                                else{
                                    window.location.reload();
                                }
                            });
                        });
                    });
                }
            }
        },
    });
    widgetRegistry.add(
        'purchase_barcode', PurchaseOrderBarcode
    );
});
