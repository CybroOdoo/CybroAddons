odoo.define('pos_products_based_on_time.ProductsPlanning', function(require) {
	'use strict';
	const ProductsWidget = require('point_of_sale.ProductsWidget');
	const Registries = require('point_of_sale.Registries');
		// Define a new class that extends ProductsWidget
	const ProductsPlanning = (ProductsWidget) => class extends ProductsWidget {
		 // Override the setup method to perform any additional setup logic.
		setup() {
			super.setup(...arguments);
		}
		/**
		 * Override the productsToDisplay getter method to filter the list of products
		 * based on the current time and the meals planning data.
		 * @returns {Array} A sorted array of product objects to be displayed.
		 */
		get productsToDisplay() {
			let list = [];
			if (this.searchWord !== '') {
				list = this.env.pos.db.search_product_in_category(
					this.selectedCategoryId,
					this.searchWord
				);
			} else {
				list = this.env.pos.db.get_product_by_category(this.selectedCategoryId);
			}
			// Get the current time in hours and minutes.
			const date = new Date();
			let time = Number(date.getHours() + '.' + date.getMinutes())
			// Filter the meals planning data to find the menu products that are available
			// for the current time.
			let data = [];
			this.env.pos.meals_planning.forEach(function(object) {
				if (object.time_from < time && time < object.time_to) {
					let plan_arr = null;
					plan_arr = object.product_ids.flat(1)
					data.push(plan_arr.map((meal) => meal.id))
				}
			})
			// Filter the list of products to only include products that are part of the
			// available menu products for the current time.
			if (data.length) {
				list = list.filter(product => data.flat(1).includes(product.id))
			}
			// Sort the list of products by display name and return the sorted list.
			return list.sort(function(a, b) {
				return a.display_name.localeCompare(b.display_name)
			});
		}
	}
	// Register the new ProductsPlanning component with the POS registry.
	Registries.Component.extend(ProductsWidget, ProductsPlanning);
	// Export the new ProductsPlanning class.
	return ProductsPlanning;
});
