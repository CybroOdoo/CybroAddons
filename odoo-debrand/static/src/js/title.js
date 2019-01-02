odoo.define('odoo-debrand-11.title', function(require) {
"use strict";

var core = require('web.core');
var utils = require('web.utils');
var ajax = require('web.ajax');
var Dialog = require('web.Dialog');
var WebClient = require('web.AbstractWebClient');
var CrashManager = require('web.CrashManager'); // We can import crash_manager also

console.log("CrashManager",CrashManager)
var concurrency = require('web.concurrency');
var mixins = require('web.mixins');
var session = require('web.session');

var QWeb = core.qweb;
var _t = core._t;
var _lt = core._lt;
var name = " ";


var map_title ={
    user_error: _lt('Warning'),
    warning: _lt('Warning'),
    access_error: _lt('Access Error'),
    missing_error: _lt('Missing Record'),
    validation_error: _lt('Validation Error'),
    except_orm: _lt('Global Business Error'),
    access_denied: _lt('Access Denied'),
};

var myWebClient =  WebClient.include({
init: function (parent) {
        this._super();
        var obj = this
        this._rpc({
            fields: ['name',],
            domain: [],
            model: 'website',
            method: 'search_read',
            limit: 1,
            context: session.user_context,
            }).done(function(result){
                  obj.set('title_part', {"zopenerp": result[0].name});
                });
    },
});

var ExceptionHandler = {
    /**
     * @param parent The parent.
     * @param error The error object as returned by the JSON-RPC implementation.
     */
    init: function(parent, error) {},
    /**
     * Called to inform to display the widget, if necessary. A typical way would be to implement
     * this interface in a class extending instance.web.Dialog and simply display the dialog in this
     * method.
     */
    display: function() {},
};

var RedirectWarningHandler = Dialog.extend(ExceptionHandler, {
    init: function(parent, error) {
        this._super(parent);
        this.error = error;
    },
    display: function() {
        var self = this;
        var error = this.error;
        error.data.message = error.data.arguments[0];

        new Dialog(this, {
            size: 'medium',
            title: _.str.capitalize(error.type) || _t("Warning"),
            buttons: [
                {text: error.data.arguments[2], classes : "btn-primary", click: function() {
                    window.location.href = '#action='+error.data.arguments[1];
                    self.destroy();
                }},
                {text: _t("Cancel"), click: function() { self.destroy(); }, close: true}
            ],
            $content: QWeb.render('CrashManager.warning', {error: error}),
        }).open();
    }
});
core.crash_registry.add('odoo.exceptions.RedirectWarning', RedirectWarningHandler);

function session_expired(cm) {
    return {
        display: function () {
            cm.show_warning({type: _t("Session Expired"), data: {message: _t("Your Odoo session expired. Please refresh the current web page.")}});
        }
    }
}
core.crash_registry.add('odoo.http.SessionExpiredException', session_expired);


});
