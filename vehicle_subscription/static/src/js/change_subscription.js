/** @odoo-module **/

import publicWidget from 'web.public.widget';
//Change subscription redirect to back page
publicWidget.registry.change_subscription_on = publicWidget.Widget.extend({
    selector: '#change_subscription_on',
    events: {
        'click .redirect_back_with_data':'_onClickBack',
    },
     //Previous page
    _onClickBack:function(ev){
        window.history.back();
    }
})
