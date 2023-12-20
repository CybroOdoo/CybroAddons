odoo.define('theme_autofly.search', function(require){
    'use strict';
    const publicWidget = require('web.public.widget');
    const rpc = require('web.rpc');
    const { qweb } = require('web.core');

    publicWidget.registry.search = publicWidget.Widget.extend({
        selector : '.search',
        willStart: async function(){
            await rpc.query({
//                route: '/get_searched_car'
                model: 'car.brand',
                method: 'get_brands'
            }).then(function(result) {
                var car_name = result[0].car_name // Add data values to array
                var car_id = result[0].car_id
                var j = 0;
                for (var c in car_name) {
                          $('#search_sel_box').append('<option value="'+car_id[c]+'">'+car_name[c]+'</option>')
                };
                var type_name = result[1].car_type
                var type_id = result[1].type_id
                for (var t in type_name) {
                    $('#search_car_type_sel_box').append('<option value="'+type_id[t]+'">'+type_name[t]+'</option>')
                };
            })
        },
        slug: function(rec) {
            return rec[1].split(' ').join('-') + '-' + rec[0]
       },
        start: function(){
        },
    });
});

