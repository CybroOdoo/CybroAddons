odoo.define('odoo-debrand-14.title', function(require) {
"use strict";

var core = require('web.core');
var session = require('web.session');
var _t = core._t;
var _lt = core._lt;
var name = " ";
var Widget = require('web.Widget');
var WebClient = require('web.WebClient');

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
        this._super.apply(this, arguments);
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

var RedirectWarningHandler = Widget.extend(ExceptionHandler, {   // Odoo warning removed
    init: function(parent, error) {
        this._super(parent);
        this.error = error;
    },
    display: function() {
        var self = this;
        var error = this.error;
        var additional_context = _.extend({}, this.context, error.data.arguments[3]);

        new WarningDialog(this, {
            title: _.str.capitalize(error.type) || _t("Warning"),
            buttons: [
                {text: error.data.arguments[2], classes : "btn-primary", click: function() {
                    self.do_action(
                        error.data.arguments[1],
                        {
                            additional_context: additional_context,
                        });
                        self.destroy();
                }, close: true},
                {text: _t("Cancel"), click: function() { self.destroy(); }, close: true}
            ]
        }, {
            message: error.data.arguments[0],
        }).open();
    }
});

core.crash_registry.add('odoo.exceptions.RedirectWarning', RedirectWarningHandler);


function session_expired(cm) {   // Odoo session expired message
    return {
        display: function () {
            const notif = {
                type: _t("Session Expired"),
                message: _t("Your session expired. The current page is about to be refreshed."),
            };
            const options = {
                buttons: [{
                    text: _t("Ok"),
                    click: () => window.location.reload(true),
                    close: true
                }],
            };
            cm.show_warning(notif, options);
        }
    };
}


core.crash_registry.add('odoo.http.SessionExpiredException', session_expired);
core.crash_registry.add('werkzeug.exceptions.Forbidden', session_expired);

});
