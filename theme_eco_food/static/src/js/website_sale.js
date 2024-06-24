/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.WebsiteSaleLayout = publicWidget.Widget.extend({
    selector: '.oe_website_sale',
    events: {
        'click #listview': '_setListView',
        'click #gridview': '_setGridView',
        'click .all_products': '_setAllProducts',
        'click .category_wise': '_setProductCategory',
    },
    start() {
        this.orm = this.bindService("orm");
    },
    _setListView() {
        // Function to set the shop page to list view.
        this.$('#best_products').css({'display':'flex','flex-wrap':'wrap'})
        this.$('.product_info').css({'margin-left':'360px','margin-top':'-200px'})
    },
    _setGridView() {
        // Function to set the shop page to grid view.
        this.$('#best_products').css({'display':'grid','margin-top':'0px'})
        this.$('.product_info').css({'margin-left':'0px','margin-top':'0px'})
    },
    _setAllProducts() {
        var checked = document.querySelectorAll('.all_products_checkbox')[0].checked
        if (checked) {
            this.orm.call('product.template','get_product_selections',[{'all' : checked, 'category': false}])
            .then(function () {
                location.reload();
            })
        }
    },
    _setProductCategory() {
        var fieldId = document.getElementById('category_wise');
        var checkboxes = fieldId.querySelectorAll('input[type="checkbox"]');
        var productId = document.querySelectorAll('.productId')
        var category = [];
        checkboxes.forEach((checkbox) => {
            if (checkbox.checked == true) {
                category.push(parseInt(checkbox.getAttribute('data-id')))
            }
        })
        this.orm.call('product.template','get_product_selections',[{
            'all' : false,
            'category': category
        }]).then(() => {
            location.reload();
        })
    }
})