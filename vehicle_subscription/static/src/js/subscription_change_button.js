/** @odoo-module **/

import publicWidget from 'web.public.widget';
//Redirect from subscription_change_button to previous page
publicWidget.registry.boolean_true = publicWidget.Widget.extend({
    selector: '#boolean_true',
    events: {
        'click .redirect_back_with_data':'_onClickBack',
    },
     //Previous page
    _onClickBack:function(ev){
        window.history.back();
    }
})
