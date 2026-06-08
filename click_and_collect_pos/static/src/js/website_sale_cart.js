/** @odoo-module */
import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";

publicWidget.registry.ClickAndCollect = publicWidget.Widget.extend({
    selector: '.oe_cart',
    events: {
        'click .clickandecollect': '_onClickClickAndCollect',
        'change .session_values': '_onClickPosConfig',
    },

    /**
     * @override
     */
    start: function () {

        // Log all found elements
        const checkboxes = this.el.querySelectorAll('.clickandecollect');
        const sessions = this.el.querySelectorAll('.oe_session');

        checkboxes.forEach((checkbox, index) => {
            console.log(`Checkbox ${index + 1}:`, {
                id: checkbox.dataset.id,
                checked: checkbox.checked,
                lineId: checkbox.dataset.id
            });
        });

        sessions.forEach((session, index) => {
            console.log(`Session ${index + 1}:`, {
                lineId: session.dataset.lineId,
                hidden: session.classList.contains('d-none')
            });
        });

        return this._super.apply(this, arguments);
    },

    _onClickClickAndCollect(ev) {

        const orderLineId = ev.target.dataset.id;

        // Find the corresponding session select for this specific line
        const sessionElement =  $(ev.currentTarget.parentElement.parentElement).find('.oe_session');

        if (!sessionElement) {
            document.querySelectorAll('.oe_session').forEach(el => {
                console.log(' - ', el.dataset.lineId, el);
            });
            return;
        }

        if (ev.target.checked) {
            sessionElement.removeClass('d-none');
        } else {
            sessionElement.addClass('d-none');
        }

        rpc('/web/dataset/call_kw', {
            model: 'sale.order.line',
            method: 'write',
            args: [
                [parseInt(orderLineId)],
                {'is_click_and_collect': ev.target.checked},
            ],
            kwargs: {},
        }).then(function(result) {
            console.log('RPC call successful - Click and collect updated:', result);
        }).catch(function(error) {
            console.error('RPC call failed:', error);
        });
    },

    _onClickPosConfig(ev) {
        console.log('POS Config selection changed', ev.target);
        console.log('Selected value:', ev.target.value);

        const orderLineId = ev.target.dataset.lineId;
        console.log('Order Line ID from select:', orderLineId);

        const sessionId = ev.target.value;
        console.log('Session ID to update:', sessionId);

        if (!sessionId) {
            console.log('No session selected, skipping update');
            return;
        }

        console.log('Making RPC call to update POS config');
        rpc('/web/dataset/call_kw', {
            model: 'sale.order.line',
            method: 'write',
            args: [
                [parseInt(orderLineId)],
                {'pos_config_id': parseInt(sessionId)},
            ],
            kwargs: {},
        }).then(function(result) {
            console.log('RPC call successful - POS config updated:', result);
        }).catch(function(error) {
            console.error('RPC call failed:', error);
        });
    },
});