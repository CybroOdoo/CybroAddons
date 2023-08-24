/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { FormController } from "@web/views/form/form_controller";
import { Component, onWillStart, useEffect, useRef, onRendered, useState, toRaw } from "@odoo/owl";
import { useBus, useService } from "@web/core/utils/hooks";
import { useModel } from "@web/views/model";
import { SIZES } from "@web/core/ui/ui_service";

import { useViewButtons } from "@web/views/view_button/view_button_hook";
import { useSetupView } from "@web/views/view_hook";
import { useDebugCategory } from "@web/core/debug/debug_context";
import { usePager } from "@web/search/pager_hook";
import { isX2Many } from "@web/views/utils";
import { registry } from "@web/core/registry";
const viewRegistry = registry.category("views");


odoo.__DEBUG__ && console.log("Console log inside the patch function", FormController.prototype, "form_controller");
var data = false;

patch(FormController.prototype, "save",{
    setup() {
        this.props.preventEdit = !data
        this._super();
    },

    async edit(){
        this._super();
        data = true;
        await this.model.root.switchMode("edit");
    },
    async saveButtonClicked(params = {}){
        this._super();
        data = false;
        await this.model.root.switchMode("readonly");
    },
    async discard(){
        this._super();
        data = false;
        await this.model.root.switchMode("readonly");
    }
})

