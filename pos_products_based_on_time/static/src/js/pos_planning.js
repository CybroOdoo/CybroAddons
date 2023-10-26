odoo.define('pos_products_based_on_time.ProductsPlanning', function(require) {
	'use strict';

	const ProductsWidget = require('point_of_sale.ProductsWidget');
	const Registries = require('point_of_sale.Registries');
		// Define a new class that extends ProductsWidget
	const ProductsPlanning = (ProductsWidget) => class extends ProductsWidget {
//	    Override the setup method to perform any additional setup logic.
		setup() {
			super.setup(...arguments);
		}
		/**
		 * Override the productsToDisplay getter method to filter the list of products
		 * based on the current time and the meals planning data.
		 */
		get productsToDisplay() {
			let allProducts = [];
			if (this.searchWord !== '') {
				allProducts = this.env.pos.db.search_product_in_category(
					this.selectedCategoryId,
					this.searchWord
				);
			} else {
				allProducts = this.env.pos.db.get_product_by_category(this.selectedCategoryId);
			}
			const date = new Date();
			let hoursMin = date.getHours() + '.' + date.getMinutes();
			let time = Number(hoursMin)
			let currentProducts = [];
			this.env.pos.meals_planning.forEach(function(object) {
				if (object.time_from < time && time < object.time_to) {
					currentProducts = object.product_ids.flat(1)
				}
			})
			// Filter the list of products to only include products that are part of the
			// Available menu products for the current time.
			if (currentProducts.length) {
				allProducts = allProducts.filter(product => currentProducts.flat(1).includes(product.id))
			}
			// Sort the list of products by display name and return the sorted list.
			return allProducts.sort(function(firstProduct, secondProduct) {
				return firstProduct.display_name.localeCompare(secondProduct.display_name)
			});
		}
	}
	Registries.Component.extend(ProductsWidget, ProductsPlanning);
	return ProductsPlanning;
});
