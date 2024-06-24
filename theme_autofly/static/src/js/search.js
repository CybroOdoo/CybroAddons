/** @odoo-module **/

import publicWidget from '@web/legacy/js/public/public_widget';
import { jsonrpc } from "@web/core/network/rpc_service";

publicWidget.registry.search = publicWidget.Widget.extend({
    selector : '.search .search_bar',
    async start () {
        const data = await jsonrpc('/get_searched_car')
        $('.search_sel_box').empty().append('<option/>')
        data?.brand?.forEach(function(brand) {
            $('.search_sel_box').append('<option value="'+brand.id+'">'+brand.name+'</option>')
        })
        $('.search_car_type_sel_box').empty().append('<option/>')
        data?.type?.forEach(function(type) {
            $('.search_car_type_sel_box').append('<option value="'+type.id+'">'+type.name+'</option>')
        })
    }
});