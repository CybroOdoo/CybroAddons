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
    // Existing list view styles
    this.$('#best_products').css({
        'display': 'block'
    });

    this.$('.b_product').css({
        'display': 'block',
        'width': '1080px'
    });

    this.$('.b_product .wrapper').css({
        'display': 'flex'
    });
    this.$('.img_wrapper').css({
        'margin-right': '20px',  // Adjust this value as needed
        'flex-shrink': '0'      // Prevents the image from shrinking
    });

    // Ensure the product info container takes remaining space
    this.$('.product_info').css({
        'flex-grow': '1'
    });

    // If you're using flexbox for the wrapper (as seen in your code)
    this.$('.b_product .wrapper').css({
        'display': 'flex',
        'align-items': 'center',  // Vertically center items
        'gap': '20px'             // Modern way to add gaps between flex items
    });

    this.$('.img_wrapper img').css({
        'max-width': '120px',
        'max-height': '120px',
        'width': 'auto',
        'height': 'auto',
        'object-fit': 'contain'
    });

    this.$('.p_name').css({
        'display': 'block',
        'font-weight': 'bold',
        'font-size': '16px',
        'margin-bottom': '8px'
    });

    this.$('.product_info').css({
        'display': 'flex',
        'align-items': 'center',
        'width': '100%'
    });

    this.$('.product_meta').css({
        'display': 'flex',
        'flex-direction': 'column'
    });

    this.$('.p_price').css({
        'margin-left': 'auto',
        'white-space': 'nowrap',
        'font-weight': 'bold'
    });

    // Add these new styles for cart and wishlist icons
    this.$('.oe_product_cart, .o_add_wishlist').css({
        'font-size': '0.8em',  // Reduce icon size
        'padding': '0.3em',    // Reduce padding around icons
        'margin': '0.2em'      // Reduce margin around icons
    });

    // If the icons are images, you might need to target them directly
    this.$('.oe_product_cart img, .o_add_wishlist img').css({
        'width': '16px',       // Set specific width
        'height': '16px'       // Set specific height
    });

     this.$('.oe_product_cart, .o_add_wishlist, .a-submit, .btn-add-to-cart, .js_add_cart').css({
        'font-size': '1.0em',      // Reduce icon size
        'transform': 'scale(0.8)', // Alternative way to scale
        'padding': '0.3em',        // Reduce padding
        'margin': '0.2em'          // Reduce margin
    });

    // For font icons (like Font Awesome)
    this.$('.oe_product_cart i, .o_add_wishlist i, .fa-shopping-cart, .fa-heart').css({
        'font-size': '14px !important'
    });

    // For icon images
    this.$('.oe_product_cart img, .o_add_wishlist img, .cart-icon-img, .wishlist-icon-img').css({
        'width': '16px !important',
        'height': '16px !important',
        'max-width': '16px !important',
        'max-height': '16px !important'
    });
},
    _setGridView() {
    // Restore main grid layout

    this.$('#best_products').css({
        'display': 'grid',
      'grid-template-columns': 'repeat(4, 1fr)',
      'grid-column-gap': '20px',
      'grid-row-gap': '30px',
      'margin-bottom': '40px'
    });

    this.$('.oe_product_cart, .o_add_wishlist, .a-submit, .btn-add-to-cart, .js_add_cart').css({
        'font-size': '1.7em',      // Reduce icon size
    });


    // Product wrapper
    this.$('.b_product').css({
        'display': 'block',
        'width': '',
        'padding': '0',
        'border': 'none'
    });

    this.$('.b_product .wrapper').css({
        'display': 'block'
    });

    // Reset image styles
    this.$('.img_wrapper img').css({
        'max-width': '100%',
        'max-height': '',
        'width': '100%',
        'height': 'auto',
        'object-fit': 'cover'
    });

    // Product info layout
    this.$('.product_info').css({
        'margin-left': '0',
        'margin-top': '10px'
    });

    // Product name
    this.$('.p_name').css({
        'display': '',
        'font-weight': '',
        'font-size': '',
        'margin-bottom': ''
    });
}
,
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