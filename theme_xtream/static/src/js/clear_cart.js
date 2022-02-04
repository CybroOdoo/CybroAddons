odoo.define('theme_xtream.clear_cart', function (require) {
	"use strict";

	require('web.dom_ready');
	var ajax = require('web.ajax');
    $(document).ready(function(){
        $("body").on('click','#clear_cart_button',function (ev){
            ev.preventDefault();
            ajax.jsonRpc("/shop/clear_cart", 'call', {}).then(function(data){
                location.reload();
                return;
            });
        return false;
        });
    });
})
