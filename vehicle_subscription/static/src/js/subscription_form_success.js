/** @odoo-module **/

import publicWidget from 'web.public.widget';
//Redirect from subscription_form_success to previous page
publicWidget.registry.form_page = publicWidget.Widget.extend({
    selector: '#subscription_form_page',
    events: {
        'click .redirect_back_with_data':'_onClickBack',
    },
     //Previous page
    _onClickBack:function(ev){
        window.history.back();
    }
})
