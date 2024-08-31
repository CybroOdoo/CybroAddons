/** @odoo-module **/
import { jsonrpc } from "@web/core/network/rpc_service";
import PublicWidget from "@web/legacy/js/public/public_widget";

PublicWidget.registry.WebsiteCart = PublicWidget.Widget.extend({
    selector: '.o_wsale_products_main_row',
    events: {
        'click .confirm_check': '_onClickCartQuantity',
    },
    //Function will work when click Add button
    _onClickCartQuantity: function(ev) {
        let self = this;
        let selectedProducts = [];
        let checkBoxes = self.$el[0].querySelectorAll('.mycheckbox');
        checkBoxes.forEach(item => {
            if (item.checked) {
                selectedProducts.push(item.value);
            }
        });
        if (selectedProducts.length > 0) {
            jsonrpc('/shop/cart/add_multi_product', { 'product_ids': selectedProducts }).then(function(response) {
                // Update cart quantity in the cart icon
                let totalQty = response.total_qty;
                sessionStorage.setItem('website_sale_cart_quantity', totalQty);
                self.$el.find(".my_cart_quantity").text(totalQty);

                // Optionally, reload the page or redirect to the cart page
                window.location.reload();
            });
        }
    },
});
