odoo.define('theme_eco_food.eco_food_recently_added', function(require) {
    'use strict';

    var Animation = require('website.content.snippets.animation');
    var ajax = require('web.ajax');
    var core = require('web.core');

    var rpc = require('web.rpc')
    var arr = [];
    var check;
    $('#listview').click(function(){
        $('#best_products').css({'display':'flex','flex-wrap':'wrap'})
        $('.product_info').css({'margin-left':'360px','margin-top':'-200px'})
    });
    $('#gridview').click(function(){
        $('#best_products').css({'display':'grid','margin-top':'0px'})
        $('.product_info').css({'margin-left':'0px','margin-top':'0px'})
    });
    $('.goi').click(function(event) {
    var checks = this.querySelectorAll('input[type="checkbox"]');
         for (var i = 0; i < checks.length; i++) {
            if (checks[i].checked == true) {check=-1}
          else{ check=-2}
    }
     rpc.query({
            model: 'product.template',
            method: 'get_product_selections',
            args: [{
                 'product_ids':arr,
                'checked': check,
            }],
        }).then(function(data) {
        location.reload();
        });
    });
    $('.gpp').on('click', function() {
        var elements = this.querySelectorAll('input[type="hidden"]');
        var checks = this.querySelectorAll('input[type="checkbox"]');
        for (var i = 0; i < checks.length; i++) {
            if (checks[i].checked == true) {
            check=0
                for (var i = 0; i < elements.length; i++) {
                    if (arr.includes(parseInt(elements[i].value)) == false) {

                        arr.push(parseInt(elements[i].value));
                    }
                }

            } else {
                        check=1
            if (arr.length==0){
             for (var i = 0; i < elements.length; i++) {
                    if (arr.includes(parseInt(elements[i].value)) == false) {
                        arr.push(parseInt(elements[i].value));
                    }
                }
            }
                else if (arr.includes(parseInt(elements[i].value)) == true) {
                                                arr.length=0;
                    for (var i = 0; i < elements.length; i++) {
                                arr.push(parseInt(elements[i].value));
                    }
                }
            }
        }
        rpc.query({
            model: 'product.template',
            method: 'get_product_selections',
            args: [{
                'product_ids': arr,
                'checked': check
            }],
        }).then(function(data) {
        location.reload();
        });
    });


    Animation.registry.get_recently_added_products = Animation.Class.extend({
            xmlDependencies: ['/theme_eco_food/static/src/xml/snippets/recently_added.xml'],
        selector: '.recent_product',
        start: function() {
            var self = this;
            var QWeb = core.qweb;
            ajax.jsonRpc('/get_recently_added_products', 'call', {})
                .then(function(data) {
                    if (data) {
                        self.$el.html(QWeb.render('theme_eco_food.eco_food_recently_added_products1',{
                  slide1: data.slide1,
                  slide2: data.slide2,
                  }));
                        self.product_carousel();
                    }
                });
        },
        product_carousel: function(autoplay = false, items = 2, slider_timing = 5000) {
            var self = this;
            $("#demo_recent_product").owlCarousel({
                items: 1,
                loop: true,
                margin: 30,
                stagePadding: 30,
                smartSpeed: 450,
                autoplay: true,
                autoPlaySpeed: 1000,
                autoPlayTimeout: 1000,
                autoplayHoverPause: true,
                dots: false,
                nav: true,
            });
        },
    });
});