odoo.define('theme_eco_food.website_layout', function(require) {
    'use strict';

    var publicWidget = require('web.public.widget');
    var arr = [];
    var check;
    require('website_sale.website_sale');
    /** include website sale for getting the list view of website sale and
    alter it**/
    publicWidget.registry.WebsiteSaleLayout.include({
    events: {
        'click #listview': 'listView',
        'click #gridview': 'gridView',
        'click .goi': 'selectedProduct',
        'click .gpp': 'checkedProducts',
    },
    /**
    List view style of the products in theme eco food eCommerce
    **/
     listView: function () {
        this.$('#best_products').css({'display':'flex','flex-wrap':'wrap'})
        this.$('.product_info').css({'margin-left':'360px', 'margin-top':'-200px'})
        this.$('.img_wrapper').css({'width':'200px','height':'200px', 'display':'flex','align-items':'center','justify-content': 'center'})
        this.$('.product_bottom').css({'left':'350px','width':'200px'})
     },
     /**
     Grid view style of the products in theme eco food eCommerce
     **/
      gridView: function () {
        this.$('#best_products').css({'display':'grid','margin-top':'0px'})
        this.$('.product_info').css({'margin-left':'0px','margin-top':'0px'})
        this.$('.img_wrapper').css({'width':'','height':'','display':'', 'align-items':'','justify-content': ''})
        this.$('.product_bottom').css({'left':'','width':''})
    },
    /**
    To get selected product and already selected product is marked as checks
    **/
    selectedProduct: function (event) {
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
    },
    /**
    To get all input type hidden and checkbox of ecommerce
    in theme eco food
    **/
    checkedProducts: function () {
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
    },
    });
    return publicWidget;
});
