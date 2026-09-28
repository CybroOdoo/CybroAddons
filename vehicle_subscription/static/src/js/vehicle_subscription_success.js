/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";
publicWidget.registry.missing_page = publicWidget.Widget.extend({
    selector: '#subscription_missing_page',
    events: {
        'click .redirect_back_with_data':'_onClickBack',
    },
      _onClickBack(ev){ //Previous page
            window.history.back();
        },
}),
publicWidget.registry.form_page = publicWidget.Widget.extend({
    selector: '#subscription_form_page',
    events: {
        'click .redirect_back_with_data':'_onClickBack',
    },
        _onClickBack(ev){ //Previous page
            window.history.back();
        },
}),

publicWidget.registry.cancellation_page = publicWidget.Widget.extend({
    selector: '#subscription_cancellation_page',
    events: {
        'click .redirect_back_with_data':'_onClickBack',
    },
        _onClickBack(ev){ //Previous page
            window.history.back();
        }
}),
publicWidget.registry.boolean_false = publicWidget.Widget.extend({
    selector: '#boolean_false',
    events: {
        'click .redirect_back_with_data':'_onClickBack',
    },
        _onClickBack(ev){ //Previous page
            window.history.back();
        }
}),
publicWidget.registry.boolean_true = publicWidget.Widget.extend({
    selector: '#boolean_true',
    events: {
        'click .redirect_back_with_data':'_onClickBack',
    },
        _onClickBack(ev){ //Previous page
            window.history.back();
        }
}),

publicWidget.registry.change_subscription_on = publicWidget.Widget.extend({
    selector: '#change_subscription_on',
    events: {
        'click .redirect_back_with_data':'_onClickBack',
    },
        _onClickBack(ev){ //Previous page
            window.history.back();
        }
})


