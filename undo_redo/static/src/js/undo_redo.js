/** @odoo-module **/

import { FormController } from "@web/views/form/form_controller";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { proxy, effect, onMounted, onWillDestroy, onWillStart } from "@odoo/owl";

patch(FormController.prototype, {
    setup() {
        super.setup();
        this.orm = useService("orm");
        this.state = proxy({
            ...(this.state || {}),
            undo: [],
            redo: [],
        });

        onWillStart(async () => {
            await this.setData();
        });

        let disposeUndoEffect = () => {};
        onMounted(() => {
            disposeUndoEffect = effect(() => {
                const resId = this.model?.root?.resId;
                const resModel = this.model?.root?.resModel;
                if (resId && resModel) {
                    this.setData();
                } else {
                    this.state.undo = [];
                    this.state.redo = [];
                }
            });
        });
        onWillDestroy(() => {
            disposeUndoEffect();
        });
    },

    async setData() {
        this.state.undo = await this.getData("undo");
        this.state.redo = await this.getData("redo");
    },

    async undo() {
        if (!this.state.undo.length) {
            return;
        }
        await this.orm.call("undo.redo", "unlink", [this.state.undo[0]]);
        await this.setData();
        if (this.model) {
            await this.model.load();
        }
        this.env.searchModel?._notify?.();
    },

    async redo() {
        if (!this.state.redo.length) {
            return;
        }
        await this.orm.call("undo.redo", "unlink", [this.state.redo[0]]);
        await this.setData();
        if (this.model) {
            await this.model.load();
        }
        this.env.searchModel?._notify?.();
    },

    async getData(mode) {
        const resModel = this.model?.root?.resModel || this.props.resModel;
        const resId = this.model?.root?.resId || this.props.resId;
        if (!resModel || !resId) {
            return [];
        }
        return await this.orm.call("undo.redo", "get_data", [resModel, resId, mode]);
    },

    async save(params = {}) {
        const result = await super.save(...arguments);
        await this.setData();
        return result;
    },

    async beforeUnload(ev) {
        const result = super.beforeUnload ? await super.beforeUnload(...arguments) : undefined;
        if (!result) {
            await this.setData();
        }
        return result;
    },
});
