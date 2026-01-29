/** @odoo-module **/

import publicWidget from 'web.public.widget';
//Booking cancellation redirect to back page
publicWidget.registry.cancellation_page = publicWidget.Widget.extend({
    selector: '#subscription_cancellation_page',
    events: {
        'click .redirect_back_with_data':'_onClickBack',
    },
     //Previous page
    _onClickBack:function(ev){
        window.history.back();
    }
})
