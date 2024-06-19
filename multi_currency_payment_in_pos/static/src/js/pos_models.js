/** @odoo-module */
/** Loading all currencies and its parameters.*/
import Registries from 'point_of_sale.Registries';
import { PosGlobalState } from "point_of_sale.models";
const NewPosGlobalState = (PosGlobalState) => class NewPosGlobalState extends PosGlobalState {
   async _processData(loadedData) {
 await super._processData(...arguments);
 this.your_model = loadedData['res.currency'];
 }
}
Registries.Model.extend(PosGlobalState, NewPosGlobalState);
