import { registry } from "@web/core/registry";
import { Interaction } from "@web/public/interaction";

export class CtsThemeNewArrivalProduct extends Interaction {

   static selector = ".cts-new-arrivals";

   async willStart() {
       this.el.querySelector('.alert-info').style.display = 'none'
       this.products = await this.services.orm.searchRead(
           "product.product",
           [["is_published", "=", true]],
           ["id", "name", "description_sale", "lst_price"],
           { limit: 9 },
           { order: "create_date desc" }
       );
   }

   start() {
       this.renderAt("cts_theme_perfume.CtsThemeNewArrivalProduct", {
           products: this.products,
       }, this.el.querySelector('.new_arrival_dynamic_section'));
   }

   destroy() {
      this.el.querySelector('.alert-info').style.display = 'block'
   }
}

registry.category("public.interactions").add("cts_theme_perfume.CtsThemeNewArrivalProduct", CtsThemeNewArrivalProduct);