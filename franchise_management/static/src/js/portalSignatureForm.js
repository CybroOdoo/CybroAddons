/** @odoo-module */

import { registry } from '@web/core/registry';
import core from 'web.core';
import publicWidget from 'web.public.widget';
import { NameAndSignature } from 'web.name_and_signature';
import { SignatureForm } from '@franchise_management/js/portalSignature';

//extending the public widget for adding signature form and sign the contract
publicWidget.registry.SignatureForm = publicWidget.Widget.extend({
    selector: '.o_portal_signature_form',
    start: function () {
        var hasBeenReset = false;
        var callUrl = this.$el.data('call-url');
        var nameAndSignatureOptions = {
            defaultName: this.$el.data('default-name'),
            mode: this.$el.data('mode'),
            displaySignatureRatio: this.$el.data('signature-ratio'),
            signatureType: this.$el.data('signature-type'),
            fontColor: this.$el.data('font-color')  || 'black',
        };
        var sendLabel = this.$el.data('send-label');
        var form = new SignatureForm(this, {
            callUrl: callUrl,
            nameAndSignatureOptions: nameAndSignatureOptions,
            sendLabel: sendLabel,
        });
        // Correctly set up the signature area if it is inside a modal
        this.$el.closest('.modal').on('shown.bs.modal', function (ev) {
            if (!hasBeenReset) {
                // Reset it only the first time it is open to get correct
                // size. After we want to keep its content on reopen.
                hasBeenReset = true;
                form.resetSignature();
            } else {
                form.focusName();
            }
        });
        return Promise.all([
            this._super.apply(this, arguments),
            form.appendTo(this.$el)
        ]);
    },
});
