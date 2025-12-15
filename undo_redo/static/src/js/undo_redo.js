/** @odoo-module **/

import { FormController } from '@web/views/form/form_controller';
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
const { useState, onWillStart } = owl;

patch(FormController.prototype, {
// Setup function initializes services and state
     setup() {
            super.setup();
            this.orm = useService('orm')
            this.state = useState({
                ...this.state,
                undo: [],
                redo: [],
            })
            onWillStart(async () => {
                await this.setData();
            })
     },
// Fetch undo and redo IDs for the current record
     async setData(){
        this.state.undo = await this.getData('undo');
        this.state.redo = await this.getData('redo');
     },
// Perform undo by deleting the most recent undo record
    async undo() {
        this.state.count = await this.orm.call("undo.redo", "unlink", [this.state.undo[0]]);
        await this.setData();
        await this.env.searchModel._notify();
    },
// Perform redo by deleting the most recent redo record
    async redo() {
        this.state.count = await this.orm.call("undo.redo", "unlink", [this.state.redo[0]]);
        await this.setData();
        await this.env.searchModel._notify();
    },
    getData(mode){
        return this.orm.call("undo.redo", "get_data",[this.props.resModel, this.props.resId, mode]);
    },
// Override save to refresh undo/redo data after save
    async save(params = {}) {
        const result = await super.save(params)
        await this.setData();
        return result;
    },
// Hook to refresh data if the user tries to leave without saving
    beforeUnload() {
        const result = super.beforeUnload();
        if (!result) {
            this.setData();
        }
        return result;
    }
});