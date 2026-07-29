/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";

const FlynovaListingFilterWidget = publicWidget.Widget.extend({
    selector: '.flynova-listing-filter',
    events: {
        'change select': '_onSelectChange',
        'change input[type="checkbox"]': '_onCheckboxChange',
        'input input[type="range"]': '_onRangeInput',
        'change input[type="range"]': '_onRangeChange',
    },

    start() {
        const range = this.el.querySelector('input[type="range"][name="max_price"]');
        const display = this.el.querySelector('.flynova-price-display');
        if (range && display) {
            display.textContent = range.value;
        }
        return this._super(...arguments);
    },

    _onSelectChange() {
        this.el.submit();
    },

    _onRangeInput(ev) {
        const display = this.el.querySelector('.flynova-price-display');
        if (display) {
            display.textContent = ev.currentTarget.value;
        }
    },

    _onRangeChange() {
        this.el.submit();
    },

    _onCheckboxChange() {
        const action = this.el.getAttribute('action') || window.location.pathname;
        const url = new URL(window.location.origin + action);

        this.el.querySelectorAll('select[name]').forEach(sel => {
            url.searchParams.set(sel.name, sel.value);
        });
        this.el.querySelectorAll('input[type="range"][name]').forEach(inp => {
            url.searchParams.set(inp.name, inp.value);
        });

        const groups = {};
        this.el.querySelectorAll('input[type="checkbox"][name]:checked').forEach(cb => {
            (groups[cb.name] = groups[cb.name] || []).push(cb.value);
        });
        Object.entries(groups).forEach(([name, vals]) => {
            url.searchParams.set(name, vals.join(','));
        });

        window.location.href = url.toString();
    },
});

publicWidget.registry.FlynovaListingFilterWidget = FlynovaListingFilterWidget;
