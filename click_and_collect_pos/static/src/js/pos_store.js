/** @odoo-module */
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { patch } from "@web/core/utils/patch";
patch(PosStore.prototype, {
         /**
         *Override PosGlobalState to load fields in pos session
         */
     async _processData(loadedData) {
        await super._processData(...arguments);
        let stock_picking = []
			this.stock_picking = loadedData['stock.picking']
			loadedData['stock.picking'].forEach((data) => {
				data.move_ids_without_package = loadedData['stock.move'].filter((stock) => data.move_ids_without_package.includes(stock.id))
				stock_picking.push(data)
			})
			this.stock_picking = stock_picking
     }
   })
