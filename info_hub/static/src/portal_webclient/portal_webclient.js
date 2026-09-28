/** @odoo-module **/

import { router, routerBus } from "@web/core/browser/router";
import { useBus, useService } from '@web/core/utils/hooks';
import { ActionContainer } from '@web/webclient/actions/action_container';
import { MainComponentsContainer } from "@web/core/main_components_container";
import { useOwnDebugContext } from "@web/core/debug/debug_context";
import { Component, onMounted, useExternalListener } from "@odoo/owl";

export class InfoPortalWebClient extends Component {
    static props = {};
    static components = { ActionContainer, MainComponentsContainer };
    static template = "info_hub.InfoPortalWebClient";

    setup() {
        window.parent.document.body.style.margin = "0"; // remove margin in parent body
        this.actionService = useService("action");
        useOwnDebugContext({ categories: ["default"] });
        useBus(routerBus, "ROUTE_CHANGE", this._showView);
        onMounted(() => { this._showView(); });
        useExternalListener(window, "keydown", this.onGlobalKeyDown, { capture: true });
    }

    async _showView() {
        const isOnInfoFormView = () => {
            if (this.actionService.currentController) {
                const { action } = this.actionService.currentController;
                return action && action.tag === "info_hub.InfoApp";
            }
            return false;
        };

        if (isOnInfoFormView()) {
            return;
        }

        await this.actionService.doAction("info_hub.action_info_client", {
            additionalContext: router.current.article_id
                ? { active_id: router.current.article_id }
                : {},
            stackPosition: "replaceCurrentAction",
        });
    }

    onGlobalKeyDown(event) {
        if (event.key === 'k' && (event.ctrlKey || event.metaKey)) {
            event.stopPropagation();
        }
    }
}
