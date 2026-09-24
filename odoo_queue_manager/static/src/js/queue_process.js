/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.QueueProcess = publicWidget.Widget.extend({

    selector: '.queue-processing-page',

    start() {
        this._bindEvents();
        return this._super(...arguments);
    },

    _bindEvents() {

        const select = this.el.querySelector('#tokenStateSelect');
        const submit = this.el.querySelector('#submitButton');
        const query = this.el.querySelector('#customerQuery');
        const feedback = this.el.querySelector('#customerFeedback');

        if (!select || !submit) {
            return;
        }

        const updateLink = () => {

            const state = select.value;

            const tokenId = submit.dataset.tokenId;
            const counterId = submit.dataset.counterId;

            const q = encodeURIComponent(query?.value || '');
            const f = encodeURIComponent(feedback?.value || '');

            submit.href =
                `/queue/submit/${tokenId}/${counterId}/${state}` +
                `?query=${q}&feedback=${f}`;
        };

        select.addEventListener('change', updateLink);
        query?.addEventListener('input', updateLink);
        feedback?.addEventListener('input', updateLink);

        updateLink();
    },
});
