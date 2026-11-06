
import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";

export class WebsiteSaleLayout extends Interaction {
    static selector = '.oe_website_sale';
    dynamicContent = {
        "#listview": { "t-on-click": this._setListView },
        "#gridview": { "t-on-click": this._setGridView },
        ".all_products_checkbox": { "t-on-change": this._setAllProducts },
        ".category_checkbox": { "t-on-change": this._setProductCategory },
    };
    _setListView() {
        this.el.classList.add("eco-food-list-view");
    }

    _setGridView() {
        this.el.classList.remove("eco-food-list-view");
    }

    _setAllProducts() {
        const checked = this.el.querySelector('.all_products_checkbox').checked
        if (checked) {
            this.waitFor(rpc('/theme_eco_food/product_selections', {all_products: checked, category_ids: []}))
            .then(function () {
                location.reload();
            })
        }
    }
    _setProductCategory() {
        const fieldId = this.el.querySelector('#category_wise');
        var checkboxes = fieldId.querySelectorAll('input[type="checkbox"]');
        var category = [];
        checkboxes.forEach((checkbox) => {
            if (checkbox.checked == true) {
                category.push(parseInt(checkbox.getAttribute('data-id')))
            }
        })
        this.waitFor(rpc('/theme_eco_food/product_selections', {
            all_products: false,
            category_ids: category,
        })).then(() => {
            location.reload();
        })
    }
}

registry.category("public.interactions").add("theme_eco_food.WebsiteSaleLayout", WebsiteSaleLayout);
