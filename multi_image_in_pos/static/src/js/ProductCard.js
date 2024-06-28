/** @odoo-module **/

import { ProductCard } from "@point_of_sale/app/generic_components/product_card/product_card";
import { patch } from "@web/core/utils/patch";
import { MultiImagePopup } from "./MultiImagePopup"
import { onMounted } from "@odoo/owl";
//Patching ProductCard component
patch(ProductCard.prototype, {
   async setup(){
       super.setup(...arguments);
       onMounted(this.loadProductData)
   },
//   Loading product data
   async loadProductData(){
       this.product = this.props.productId;
       this.data = await this.env.services.orm.searchRead('product.product',[['id', '=', this.product]], ['image_ids']);
       this.props.imageIDS = this.data[0].image_ids
   },
//   function to show multiple images in a popup
   async onClickImageIcon() {
        var imageList = [];
        for (let i = 0; i < this.data[0].image_ids.length; i++) {
            var image = await this.env.services.orm.searchRead('multi.image',[['id', '=', this.data[0].image_ids[i]]], ['image']);
            imageList.push(image[0].image);
        }
        this.imageList = imageList
        await this.env.services.popup.add(MultiImagePopup, {
             product: this.product,
             data: imageList
        });
   }
})
