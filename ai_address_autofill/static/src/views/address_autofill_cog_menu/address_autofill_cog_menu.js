import { Component } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { STATIC_ACTIONS_GROUP_NUMBER } from "@web/search/action_menus/action_menus";

const cogMenuRegistry = registry.category("cogMenu");

export class AddressAutofillCogMenu extends Component {
    static template = "ai_address_autofill.AddressAutofillCogMenu";
    static components = { DropdownItem };

    setup() {
        this.actionService = useService("action");
    }

    openAddressExtractor() {
        const selection = this.env.model?.root?.selection;
        const activeId = selection && selection.length ? selection[0].resId : (this.env.model?.root?.resId || false);

        const context = {};
        if (activeId) {
            context.default_partner_id = activeId;
            context.active_id = activeId;
            context.active_model = "res.partner";
        }

        return this.actionService.doAction("ai_address_autofill.action_address_extraction_wizard", {
            additionalContext: context,
            onClose: () => {
                if (this.env.model?.root?.load) {
                    this.env.model.root.load();
                }
            },
        });
    }
}

export const addressAutofillCogMenuItem = {
    Component: AddressAutofillCogMenu,
    groupNumber: STATIC_ACTIONS_GROUP_NUMBER,
    isDisplayed: async (env) => {
        const searchModel = env?.searchModel;
        const config = env?.config;
        if (searchModel?.resModel !== "res.partner" || !["list", "kanban"].includes(config?.viewType)) {
            return false;
        }
        try {
            const orm = env?.services?.orm || searchModel?.orm;
            if (orm) {
                const isEnabled = await orm.call("res.partner", "check_address_extraction_list_enabled", []);
                return Boolean(isEnabled);
            }
        } catch {
            return false;
        }
        return false;
    },
};

cogMenuRegistry.add("address-autofill-cog-menu", addressAutofillCogMenuItem, { sequence: 20 });
