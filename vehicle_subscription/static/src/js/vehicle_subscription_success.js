odoo.define('vehicle_subscription.form_page', function (require) {
    "use strict";
var publicWidget = require('web.public.widget');
publicWidget.registry.form_page = publicWidget.Widget.extend({
    selector: '#subscription_form_page',
    events: {
        'click .redirect_back_with_data':'_onClickBack',
    },
        _onClickBack:function(ev){ //Previous page
            window.history.back();
        }
})
})
odoo.define('vehicle_subscription.missing_page', function (require) {
    "use strict";
var publicWidget = require('web.public.widget');
publicWidget.registry.missing_page = publicWidget.Widget.extend({
    selector: '#subscription_missing_page',
    events: {
        'click .redirect_back_with_data':'_onClickBack',
    },
        _onClickBack:function(ev){ //Previous page
            window.history.back();
        }
})
})
odoo.define('vehicle_subscription.cancellation_page', function (require) {
    "use strict";
var publicWidget = require('web.public.widget');
publicWidget.registry.cancellation_page = publicWidget.Widget.extend({
    selector: '#subscription_cancellation_page',
    events: {
        'click .redirect_back_with_data':'_onClickBack',
    },
        _onClickBack:function(ev){ //Previous page
            window.history.back();
        }
})
})
odoo.define('vehicle_subscription.boolean_false', function (require) {
    "use strict";
var publicWidget = require('web.public.widget');
publicWidget.registry.boolean_false = publicWidget.Widget.extend({
    selector: '#boolean_false',
    events: {
        'click .redirect_back_with_data':'_onClickBack',
    },
        _onClickBack:function(ev){ //Previous page
            window.history.back();
        }
})
})
odoo.define('vehicle_subscription.boolean_true', function (require) {
    "use strict";
var publicWidget = require('web.public.widget');
publicWidget.registry.boolean_true = publicWidget.Widget.extend({
    selector: '#boolean_true',
    events: {
        'click .redirect_back_with_data':'_onClickBack',
    },
        _onClickBack:function(ev){ //Previous page
            window.history.back();
        }
})
})
odoo.define('vehicle_subscription.change_subscription_on', function (require) {
    "use strict";
var publicWidget = require('web.public.widget');
publicWidget.registry.change_subscription_on = publicWidget.Widget.extend({
    selector: '#change_subscription_on',
    events: {
        'click .redirect_back_with_data':'_onClickBack',
    },
        _onClickBack:function(ev){ //Previous page
            window.history.back();
        }
})
})
