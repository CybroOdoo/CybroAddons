/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { ProductsWidget } from "@point_of_sale/app/screens/product_screen/product_list/product_list";

patch(ProductsWidget.prototype, {
		/**
		 * Override the productsToDisplay getter method to filter the list of products
		 * based on the current time and the meals planning data.
		 * @returns {Array} A sorted array of product objects to be displayed.
		 */
		get productsToDisplay() {
		const { db } = this.pos;
			let list = [];
			var res_list = new Array();
			if (this.searchWord !== '') {
				list = db.search_product_in_category(
					this.selectedCategoryId,
					this.searchWord
				);
			} else {
				list = db.get_product_by_category(this.selectedCategoryId);
			}
			const date = new Date();
			let hoursMin = date.getHours() + '.' + date.getMinutes();
			let time = Number(hoursMin)
			let data = [];
			 this.env.services.pos.meals_planning.forEach(object => {
			 if (object.time_from <= time && time < object.time_to) {
			 }
			  const plan_arr = object.menu_product_ids.flat(1);
              data.push(plan_arr.map(meal => meal.id));
              })
			if (data.length) {
				list = list.filter(product => data[0].includes(product.id))
			}
			return list.sort(function(a, b) {
				return a.display_name.localeCompare(b.display_name)
			});
		}
});
