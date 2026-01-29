odoo.define('franchise_management.portal_sign', function (require) {
'use strict';

var core = require('web.core');
var publicWidget = require('web.public.widget');
var NameAndSignature = require('web.name_and_signature').NameAndSignature;
const _t = core._t;
const qweb = core.qweb;

//Submitting the signature

const SignatureForm = publicWidget.Widget.extend({
    template: 'portal.portal_signature',
    events: {
        'click .o_portal_sign_submit': 'async _onClickSignSubmit',
    },
    custom_events: {
        'signature_changed': '_onChangeSignature',
    },
    init: function (parent, options) {
        this._super.apply(this, arguments);
        this.csrf_token = odoo.csrf_token;
        this.callUrl = options.callUrl || '';
        this.rpcParams = options.rpcParams || {};
        this.sendLabel = options.sendLabel || _t("Accept & Sign");
        this.nameAndSignature = new NameAndSignature(this,
            options.nameAndSignatureOptions || {});
    },
    start: function () {
        var self = this;
        this.$confirm_btn = this.$('.o_portal_sign_submit');
        this.$controls = this.$('.o_portal_sign_controls');
        var subWidgetStart = this.nameAndSignature.replace(this.$('.o_web_sign_name_and_signature'));
        return Promise.all([subWidgetStart, this._super.apply(this, arguments)]).then(function () {
            self.nameAndSignature.resetSignature();
        });
    },
    focusName: function () {
        this.nameAndSignature.focusName();
    },
//    Resetting the signature
    resetSignature: function () {
        return this.nameAndSignature.resetSignature();
    },
//    Submitting the event handler for the signature image
    _onClickSignSubmit: function (ev) {
        var self = this;
        ev.preventDefault();
        if (!this.nameAndSignature.validateSignature()) {
            return;
        }
        var name = this.nameAndSignature.getName();
        var signature = this.nameAndSignature.getSignatureImage()[1];
        return this._rpc({
            route: this.callUrl,
            params: _.extend(this.rpcParams, {
                'name': name,
                'signature': signature,
            }),
        }).then(function (data) {
            if (data.error) {
                self.$('.o_portal_sign_error_msg').remove();
                self.$controls.prepend(qweb.render('portal.portal_signature_error', {widget: data}));
            } else if (data.success) {
                var $success = qweb.render('portal.portal_signature_success', {widget: data});
                self.$el.empty().append($success);
            }
            if (data.force_refresh) {
                if (data.redirect_url) {
                    window.location = data.redirect_url;
                } else {
                    window.location.reload();
                }
                // No resolve if we reload the page
                return new Promise(function () { });
            }
        });
    },
//    Changing the signature of the template
    _onChangeSignature: function () {
        var isEmpty = this.nameAndSignature.isSignatureEmpty();
        this.$confirm_btn.prop('disabled', isEmpty);
    },
});
});
