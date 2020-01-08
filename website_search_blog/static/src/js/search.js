odoo.define('website_sale_advanced_search.blog_search', function (require) {
"use strict";
var ajax = require('web.ajax');
$(function() {
    $(".search_query").autocomplete({
        source: function(request, response) {
            console.log("sadsad");
            $.ajax({
            url: "/blog/search",
            method: "POST",
            dataType: "json",
            data: { name: request.term},
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
            window.location.href= "/blog/our-blog-1/post/"+term.item.id
        },
        minLength: 1
    });

});
});