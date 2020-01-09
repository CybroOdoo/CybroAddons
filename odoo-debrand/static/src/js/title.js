odoo.define('odoo-debrand.title', function(require) {
"use strict";

var core = require('web.core');
var utils = require('web.utils');
var ajax = require('web.ajax');
var Dialog = require('web.Dialog');
var WebClient = require('web.AbstractWebClient');
var CrashManager = require('web.CrashManager'); // We can import crash_manager also
var concurrency = require('web.concurrency');
var mixins = require('web.mixins');
var session = require('web.session');
var Widget = require('web.Widget');
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
    
var myWebClient = WebClient.include({
    
    start: function () {
        this._super();
        var domain = session.user_context.allowed_company_ids;
        var obj = this;
        this._rpc({
            fields: ['name','id',],
            domain: [['id', 'in', domain]],
            model: 'res.company',
            method: 'search_read',
        })
            .then(function (result) {
                obj.set('title_part', {"zopenerp": result[0].name});  // Replacing the name 'Oodo' to selected company name near favicon
            });
    },
});

var ExceptionHandler = {
    init: function(parent, error) {},
    display: function() {},
};

var RedirectWarningHandler = Widget.extend(ExceptionHandler, {  // Rewriting the exception handler
    init: function(parent, error) {
        this._super(parent);
        this.error = error;
    },
    display: function() {
        var self = this;
        var error = this.error;

        new WarningDialog(this, {
            title: _.str.capitalize(error.type) || _t("Warning"),   // Replacing 'Odoo Warning' to 'Warning'
            buttons: [
                {text: error.data.arguments[2], classes : "btn-primary", click: function() {
                    $.bbq.pushState({
                        'action': error.data.arguments[1],
                        'cids': $.bbq.getState().cids,
                    }, 2);
                    self.destroy();
                    location.reload();
                }},
                {text: _t("Cancel"), click: function() { self.destroy(); }, close: true}
            ]
        }, {
            message: error.data.arguments[0],
        }).open();
    }
});

core.crash_registry.add('odoo.exceptions.RedirectWarning', RedirectWarningHandler);


function session_expired(cm) {
    return {
        display: function () {   // Replace 'Odoo session expired' to 'Session Expired'
            cm.show_warning({type: _t("Session Expired"), data: {message: _t("Your Session expired. Please refresh the current web page.")}});
        }
    };
}
core.crash_registry.add('odoo.http.SessionExpiredException', session_expired);

});
