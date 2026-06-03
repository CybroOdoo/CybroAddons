odoo.define('website_sale_advanced_search.product_search', function (require) {
"use strict";
var ajax = require('web.ajax');


$(function() {
    $('.search-panel .dropdown-menu').find('a').click(function(e) {
		e.preventDefault();
		var param = $(this).attr("href").replace("#","");

		var concept = $(this).text();
		$('.search-panel span#search_concept').text(concept);
		$('.input-group #search_param').val(param);
	});
    $(".oe_search_box").autocomplete({
        source: function(request, response) {
            $.ajax({
            url: "/shop/search",
            method: "POST",
            dataType: "json",
            data: { name: request.term, category: $('.input-group #search_param').val()},
            success: function( data ) {
                response( $.map( data, function( item ) {
                    return {
                        label: item.name,
                        value: item.name,
                        id: item.res_id,
                    }
                }));
            },
            error: function (error) {
               alert('error: ' + error);
            }
            });
        },
        select:function(suggestion,term,item){
            window.location.href= "/shop/product/"+term.item.id
        },
        minLength: 1
    });
});
});