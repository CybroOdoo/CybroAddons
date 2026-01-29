/** @odoo-module **/

import publicWidget from 'web.public.widget';
const rpc = require('web.rpc');

publicWidget.registry.search = publicWidget.Widget.extend({
    selector : '.search .search_bar',
    async start () {
        const $brand = this.$el.find('.search_sel_box');
        const $type = this.$el.find('.search_car_type_sel_box');
        var data = await rpc.query({
                model: 'car.brand',
                method: 'get_brands'
            })
        $brand.empty().append('<option>select brand</option>')
        data?.brand?.forEach(function(brand) {
            $('.search_sel_box').append('<option value="'+brand.brand_id+'">'+brand.brand_name+'</option>')
        })
        $('.search_car_type_sel_box').empty().append('<option>select type</option>')
        data?.type?.forEach(function(type) {
            $('.search_car_type_sel_box').append('<option value="'+type.type_id+'">'+type.car_type+'</option>')
        })
    }
});

