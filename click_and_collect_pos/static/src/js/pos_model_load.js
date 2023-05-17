odoo.define('click_and_collect_pos.StockPicking', function(require) {
	"use strict";

	var { PosGlobalState } = require('point_of_sale.models');
	const Registries = require('point_of_sale.Registries');

	const StockPicking = (PosGlobalState) => class StockPicking extends PosGlobalState {
		async _processData(loadedData) {
			super._processData(...arguments)
			let stock_picking = []
			this.stock_picking = loadedData['stock.picking']
			loadedData['stock.picking'].forEach((data) => {
				data.move_ids_without_package = loadedData['stock.move'].filter((stock) => data.move_ids_without_package.includes(stock.id))
				stock_picking.push(data)
			})
			this.stock_picking = stock_picking
		}
	}
	Registries.Model.extend(PosGlobalState, StockPicking);
});