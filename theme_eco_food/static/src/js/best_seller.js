
import { rpc } from "@web/core/network/rpc";
import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";
import { renderToElement } from "@web/core/utils/render";

export class ecoFoodBestSeller extends Interaction {
    static selector = '.best_seller_products';
    async willStart() {
        var data = await this.waitFor(rpc('/get_best_seller'))
        if (data) {
            this.removeChildren(this.el);
            this.insert(renderToElement('theme_eco_food.eco_food_best_seller_snippet', {
                best_seller: data
            }));
        }
     }
}

registry.category("public.interactions").add("theme_eco_food.ecoFoodBestSeller", ecoFoodBestSeller);
