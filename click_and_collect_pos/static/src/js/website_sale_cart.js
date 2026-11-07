import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";

export class ClickAndCollect extends Interaction {
    static selector = ".oe_cart";

    dynamicContent = {
        ".clickandecollect": {
            "t-on-click": this._onClickClickAndCollect,
        },
        ".session_values": {
            "t-on-change": this._onClickPosConfig,
        },
    };

    _onClickClickAndCollect(ev) {
        const orderLineId = ev.target.dataset.id;
        const sessionContainer = ev.currentTarget.closest(".click_and_collect_td");
        const sessionElement = sessionContainer?.querySelector('.oe_session');
        const sessionSelect = sessionContainer?.querySelector('select.session_values');

        if (ev.target.checked) {
            sessionElement?.classList.remove('d-none');
            let posConfigId = sessionSelect ? sessionSelect.value : null;
            if (sessionSelect && posConfigId === 'select') {
                const validOptions = Array.from(sessionSelect.options).filter(o => o.value !== 'select');
                if (validOptions.length === 1) {
                    sessionSelect.value = validOptions[0].value;
                    posConfigId = validOptions[0].value;
                } else {
                    posConfigId = null;
                }
            }
            rpc('/shop/cart/update_click_and_collect', {
                line_id: parseInt(orderLineId, 10),
                is_click_and_collect: true,
                pos_config_id: posConfigId,
            });
        } else {
            sessionElement?.classList.add('d-none');
            rpc('/shop/cart/update_click_and_collect', {
                line_id: parseInt(orderLineId, 10),
                is_click_and_collect: false,
                pos_config_id: false,
            });
        }
    }

    _onClickPosConfig(ev) {
        const orderLineId = ev.target.dataset.lineId;
        const sessionId = ev.target.value;

        rpc('/shop/cart/update_click_and_collect', {
            line_id: parseInt(orderLineId, 10),
            pos_config_id: sessionId,
        });
    }
}

registry.category("public.interactions").add("click_and_collect_pos.click_and_collect", ClickAndCollect);