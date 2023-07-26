//@odoo-module
import { PosGlobalState} from 'point_of_sale.models';
import Registries from 'point_of_sale.Registries';
const StockLotGlobalState = (PosGlobalState) => class StockLotGlobalState extends PosGlobalState {
    async _processData(loadedData) {
        await super._processData(...arguments);
        this.db.product_by_lot = loadedData['multi.barcode.products'];
        this.db.product_by_lot_id = loadedData['multi_barcode']
    }
}
Registries.Model.extend(PosGlobalState, StockLotGlobalState);