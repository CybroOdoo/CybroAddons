/** @odoo-module **/

import publicWidget from 'web.public.widget';
//Redirect from subscription_change_boolean_false to Previous page
publicWidget.registry.boolean_false = publicWidget.Widget.extend({
    selector: '#boolean_false',
    events: {
        'click .redirect_back_with_data':'_onClickBack',
    },
     //Previous page
    _onClickBack:function(ev){
        window.history.back();
    }
})
