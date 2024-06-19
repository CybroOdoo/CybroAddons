odoo.define('all_in_one_website_kit.sale_barcode', function(require) {
    'use strict';
    var publicWidget = require('web.public.widget');
    var ajax = require('web.ajax');
      /** Extends the public widget class to add the events
    */
    publicWidget.registry.WebsiteSaleBarcode = publicWidget.Widget.extend({
        selector: '.oe_website_sale',
        disabledInEditableMode: false,
        events: {
            'click .o_wsale_apply_barcode ': 'load_quagga',
            'click .close-website-barcode-modal ': '_onClickCloseModal',
        },
        _onClickCloseModal: function() {
            // Get the stream tracks
            var tracks = this.el.querySelector('video').srcObject.getTracks()
            this.el.querySelector('#mapModal').style.display = 'none'
            // Stop track
            tracks.forEach(function(track) {
                track.stop();
            });
        },
        /**
        while clicking scanner button lading the quagga lib
        */
        load_quagga: function(ev) {
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
                }, function(err) {
                    if (err) {
                        return
                    }
                    Quagga.start();
                });
                var last_result = [];
                /**
                while detecting the barcode searching for corresponding product
                */
                Quagga.onDetected(function(result) {
                    var last_code = result.codeResult.code;
                    last_result.push(last_code);
                    last_result = [];
                    Quagga.stop();
                    // Get the stream tracks
                    var tracks = video.srcObject.getTracks();
                    // Stop track
                    tracks.forEach(function(track) {
                        track.stop();
                    });
                    ajax.jsonRpc('/shop/barcodeproduct', 'call', {
                        'last_code': last_code
                    }).then(function(result) {
                        if (result == false) {
                            alert('No Product is available for this barcode.')
                        } else {
                            window.location.href = result['url'];
                        }
                    });
                });
            }
        },
    });
});