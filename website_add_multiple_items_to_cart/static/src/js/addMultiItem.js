/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";  // ✅ Correct way to use RPC in Odoo 18

publicWidget.registry.WebsiteCart = publicWidget.Widget.extend({
    selector: ".o_wsale_products_main_row",
    events: {
        "click .confirm_check": "_onClickCartQuantity",
    },

    async _onClickCartQuantity(ev) {
        let self = this;
        let selectedProducts = [];
        let checkBoxes = self.el.querySelectorAll(".mycheckbox");

        checkBoxes.forEach((item) => {
            if (item.checked) {
                selectedProducts.push(item.value);
            }
        });

        if (selectedProducts.length > 0) {
            try {
                // ✅ Correct way to call RPC in Odoo 18
                const response = await rpc("/shop/cart/add_multi_product", {
                    product_ids: selectedProducts,
                });

                // ✅ Ensure `response` is valid before using it
                if (response && response.total_qty !== undefined) {
                    let totalQty = response.total_qty;
                    sessionStorage.setItem("website_sale_cart_quantity", totalQty);

                    let cartQuantityElement = self.el.querySelector(".my_cart_quantity");
                    if (cartQuantityElement) {
                        cartQuantityElement.textContent = totalQty;
                    }

                    // Optionally, reload the page or redirect to the cart page
                    window.location.reload();
                } else {
                    console.error("Error: Invalid response from RPC", response);
                }
            } catch (error) {
                console.error("RPC Error:", error);
            }
        }
    },
});