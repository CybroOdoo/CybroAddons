/** @odoo-module **/

import publicWidget from 'web.public.widget';
//Vehicle Missing redirect to back page
publicWidget.registry.subscription_missing_page = publicWidget.Widget.extend({
    selector: '#subscription_missing_page',
    events: {
        'click .redirect_back_with_data':'_onClickBack',
    },
     //Previous page
    _onClickBack:function(ev){
        window.history.back();
    }
})
