odoo.define('website_pre_loader_style.payment_post_processing', function(require) {
    'use strict';
    /**
     * Module for customizing payment post-processing behavior.
     */
    var PaymentPostProcessing = require('payment.post_processing');
    var _t = require('web.core')._t;
    const rpc = require('web.rpc');
    PaymentPostProcessing.include({
        /**
         * Overrides the displayLoading method to show a custom loading message with a pre-loader image.
         */
        displayLoading: function() {
            var msg = _t("We are processing your payment, please wait ...");
            rpc.query({
                model: 'ir.config_parameter',
                method: 'get_param',
                args: ['website_pre_loader_style.loader_style'],
            }).then(function(result) {
                console.log(result)
                var imgSrc = '/website_pre_loader_style/static/src/img/' + result + '.png';
                console.log(imgSrc)
                $.blockUI({
                    'message': '<h2 class="text-white"><img src="' + imgSrc + '"/>' +
                        '    <br />' + msg +
                        '</h2>'
                });
            })
        },
    });
    return PaymentPostProcessing;
});
