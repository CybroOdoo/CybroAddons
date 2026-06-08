/** @odoo-module **/

import { BuilderAction } from "@html_builder/core/builder_action";
import { Plugin } from "@html_editor/plugin";
import { registry } from "@web/core/registry";

class SetStockInfoAction extends BuilderAction {
    static id = "setStockInfo";

    apply({ editingElement, value }) {
        editingElement.setAttribute('data-show-stock-info', value ? "1" : "0");
    }

    getValue({ editingElement }) {
        return editingElement.getAttribute('data-show-stock-info') === "1";
    }
}

class ShopStockOptionPlugin extends Plugin {
    static id = "shopStockOptionPlugin";

    resources = {
        builder_actions: {
            setStockInfo: SetStockInfoAction,
        },
    };
}

registry.category("website-plugins")
    .add(ShopStockOptionPlugin.id, ShopStockOptionPlugin);