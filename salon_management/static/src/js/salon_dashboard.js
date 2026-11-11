/** @odoo-module */
import { rpc } from "@web/core/network/rpc";
import { Component, onMounted, proxy, signal } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { formatCurrency } from "@web/core/currency";
const actionRegistry = registry.category("actions");

/** Convert a local "YYYY-MM-DDTHH:mm" value (as produced by an
 * <input type="datetime-local">) into the naive-UTC "YYYY-MM-DD HH:mm:ss"
 * string format Odoo expects for Datetime fields. Implemented with plain
 * JS Date instead of an external date library, since the browser already
 * parses that input format as local time for us. **/
function localDatetimeToUTCString(localValue) {
    if (!localValue) {
        return false;
    }
    const dt = new Date(localValue);
    if (isNaN(dt.getTime())) {
        return false;
    }
    const pad = (n) => String(n).padStart(2, "0");
    return `${dt.getUTCFullYear()}-${pad(dt.getUTCMonth() + 1)}-${pad(dt.getUTCDate())} `
         + `${pad(dt.getUTCHours())}:${pad(dt.getUTCMinutes())}:${pad(dt.getUTCSeconds())}`;
}

/** Today's start/end of day, expressed as naive-UTC "YYYY-MM-DD HH:mm:ss"
 * strings, for filtering "today" domains. **/
function todayUTCRange() {
    const now = new Date();
    const startLocal = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 0, 0, 0);
    const endLocal = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 23, 59, 59);
    const pad = (n) => String(n).padStart(2, "0");
    const toUTCString = (d) => `${d.getUTCFullYear()}-${pad(d.getUTCMonth() + 1)}-${pad(d.getUTCDate())} `
        + `${pad(d.getUTCHours())}:${pad(d.getUTCMinutes())}:${pad(d.getUTCSeconds())}`;
    return [toUTCString(startLocal), toUTCString(endLocal)];
}

/* Create a component named 'SalonDashboard' with extending Component
 *
 * Odoo 19.5 / OWL 3 reactivity:
 *   - proxy({...}) in setup() → reactive object; assign props directly to update
 *   - signal(val)             → reactive primitive; read via this._sig(), write via this._sig.set(val)
 *   - Expose signal values to templates through plain getter methods (get foo() { return this._sig(); })
 */
export class SalonDashboard extends Component {
    static template = "SalonSpaDashBoard";

    /* Private signals for scalar counters */
    _bookings     = signal(0);
    _sales        = signal(0);
    _orders       = signal(0);
    _clients      = signal(0);
    _revenueToday = signal(0);
    _currencyId   = signal(false);
    _submitting   = signal(false);

    /* Computed getters — templates read these as plain properties */
    get bookingsCount()  { return this._bookings(); }
    get salesCount()     { return this._sales(); }
    get ordersCount()    { return this._orders(); }
    get clientsCount()   { return this._clients(); }
    get revenueToday()   { return this._revenueToday(); }
    get submitting()     { return this._submitting(); }
    get revenueTodayFormatted() {
        return formatCurrency(this._revenueToday(), this._currencyId());
    }

    setup() {
        /* Reactive state object for arrays/objects — initialised in setup()
         * so it is bound to this component instance (mirrors PropertiesGroupByItem pattern) */
        this.state = proxy({
            revenueStageIds: [],
            chairs: [],
            ordersByStage: [],
            bookingsByState: [],
            tableRows: [],
            servicesSummary: [],
            bookingForm: {
                name: '',
                phone: '',
                email: '',
                chair_id: false,
                time: '',
                service_ids: [],
            },
            formMessage: '',
            formMessageType: '',
        });
        this.orm = useService('orm');
        onMounted(() => {
            this.render_dashboards();
        });
    }

    /** Function that renders values into the dashboard **/
    async render_dashboards() {
        const result = await this.orm.call('salon.booking', 'get_booking_count', [0], {});
        this._bookings.set(result.bookings || 0);
        this._sales.set(result.sales       || 0);
        this._orders.set(result.orders     || 0);
        this._clients.set(result.clients   || 0);
        this._revenueToday.set(result.revenue_today || 0);
        this._currencyId.set(result.currency_id || false);

        /* Direct property reassignment on a proxy triggers OWL re-render */
        this.state.revenueStageIds = result.revenue_stage_ids || [];
        this.state.chairs = await rpc("/salon/chairs", {});
        this.state.ordersByStage = result.orders_by_stage || [];
        this.state.bookingsByState = result.bookings_by_state || [];
        this.state.tableRows = result.table_rows || [];
        this.state.servicesSummary = result.services_summary || [];
    }

    /** Click function of 'Bookings' card and open bookings list view **/
    show_bookings(ev) {
        ev.stopPropagation();
        ev.preventDefault();
        this.env.services.action.doAction({
            name: _t("Salon Bookings"),
            type: 'ir.actions.act_window',
            res_model: 'salon.booking',
            view_mode: 'list,form',
            views: [[false, 'list'], [false, 'form']],
            domain: [['state', '=', 'approved']],
            target: 'current'
        });
    }

    /** Click function of 'Revenue' card: opens today's invoiced/closed orders **/
    show_revenue(ev) {
        ev.stopPropagation();
        ev.preventDefault();
        const [todayStart, todayEnd] = todayUTCRange();
        this.env.services.action.doAction({
            name: _t("Today's Revenue"),
            type: 'ir.actions.act_window',
            res_model: 'salon.order',
            view_mode: 'list,form',
            views: [[false, 'list'], [false, 'form']],
            domain: [['stage_id', 'in', this.state.revenueStageIds || []], ['date', '>=', todayStart], ['date', '<=', todayEnd]],
            target: 'current'
        });
    }

    /** Click function of 'Salon Client' card **/
    show_clients(ev) {
        ev.stopPropagation();
        ev.preventDefault();
        this.env.services.action.doAction({
            name: _t("Clients"),
            type: 'ir.actions.act_window',
            res_model: 'res.partner',
            view_mode: 'list,form',
            views: [[false, 'list'], [false, 'form']],
            domain: [['partner_salon', '=', true]],
            target: 'current'
        });
    }

    /** Click function of 'Salon Orders' card **/
    show_orders(ev) {
        ev.stopPropagation();
        ev.preventDefault();
        this.env.services.action.doAction({
            name: _t("Salon Orders"),
            type: 'ir.actions.act_window',
            res_model: 'salon.order',
            view_mode: 'list,form,calendar',
            views: [[false, 'list'], [false, 'form']],
            target: 'current'
        });
    }

    /** Click function of dashboard chairs **/
    chairs_click(ev) {
        ev.stopPropagation();
        ev.preventDefault();
        const active_id = ev.currentTarget.id;
        this.env.services.action.doAction({
            name: _t("Chair Orders"),
            type: 'ir.actions.act_window',
            res_model: 'salon.order',
            view_mode: 'kanban,list,form',
            views: [[false, 'kanban'], [false, 'list'], [false, 'form']],
            domain: [['chair_id', '=', parseInt(active_id)]],
            context: {
                default_chair_id: parseInt(active_id)
            },
            target: 'current'
        });
    }

    /** Click function of dashboard chair's settings icon **/
    settings_click(ev) {
        ev.stopPropagation();
        ev.preventDefault();
        const active_id = ev.currentTarget.id;
        this.env.services.action.doAction({
            name: _t("Chair Orders"),
            type: 'ir.actions.act_window',
            res_model: 'salon.chair',
            view_mode: 'form',
            views: [[false, 'form']],
            context: {
                default_name: active_id
            },
            target: 'current'
        });
    }

    /** Click function for a stage badge in the "Orders by status" table:
     * opens the salon orders that are currently in that stage. **/
    show_stage_orders(ev) {
        ev.stopPropagation();
        ev.preventDefault();
        const stageId = parseInt(ev.currentTarget.dataset.stageId);
        this.env.services.action.doAction({
            name: _t("Salon Orders"),
            type: 'ir.actions.act_window',
            res_model: 'salon.order',
            view_mode: 'list,form',
            views: [[false, 'list'], [false, 'form']],
            domain: [['stage_id', '=', stageId]],
            target: 'current'
        });
    }

    /** Click function for a state badge in the "Bookings by status" table:
     * opens the salon bookings that are currently in that state. **/
    show_state_bookings(ev) {
        ev.stopPropagation();
        ev.preventDefault();
        const stateKey = ev.currentTarget.dataset.stateKey;
        this.env.services.action.doAction({
            name: _t("Salon Bookings"),
            type: 'ir.actions.act_window',
            res_model: 'salon.booking',
            view_mode: 'list,form',
            views: [[false, 'list'], [false, 'form']],
            domain: [['state', '=', stateKey]],
            target: 'current'
        });
    }

    /** Click function for a row in the recent "Orders & Bookings" table:
     * opens that specific order or booking. **/
    open_table_row(ev) {
        ev.stopPropagation();
        ev.preventDefault();
        const row = ev.currentTarget.dataset;
        this.env.services.action.doAction({
            type: 'ir.actions.act_window',
            res_model: row.model,
            view_mode: 'form',
            views: [[false, 'form']],
            res_id: parseInt(row.id),
            target: 'current'
        });
    }

    /** Generic change handler for the quick-booking form's text/select inputs **/
    on_booking_field_change(ev) {
        const field = ev.target.dataset.field;
        this.state.bookingForm[field] = ev.target.value;
    }

    /** Checkbox toggle handler for the quick-booking form's service list **/
    toggle_booking_service(ev) {
        const serviceId = parseInt(ev.target.value);
        const current = this.state.bookingForm.service_ids;
        if (ev.target.checked) {
            if (!current.includes(serviceId)) {
                this.state.bookingForm.service_ids = [...current, serviceId];
            }
        } else {
            this.state.bookingForm.service_ids = current.filter((id) => id !== serviceId);
        }
    }

    /** Submit handler for the "New Booking" quick-create form on the dashboard **/
    async submit_booking(ev) {
        ev.stopPropagation();
        ev.preventDefault();
        const form = this.state.bookingForm;
        this.state.formMessage = '';
        this.state.formMessageType = '';

        if (!form.name || !form.chair_id || !form.time) {
            this.state.formMessage = _t("Please fill in the customer name, chair and date/time.");
            this.state.formMessageType = 'danger';
            return;
        }

        // The <input type="datetime-local"> value is in the user's local
        // time; convert it to the naive-UTC string Odoo expects.
        const utcTime = localDatetimeToUTCString(form.time);
        if (!utcTime) {
            this.state.formMessage = _t("Please select a valid date & time.");
            this.state.formMessageType = 'danger';
            return;
        }

        this._submitting.set(true);
        try {
            const result = await this.orm.call('salon.booking', 'quick_create_booking', [{
                name: form.name,
                phone: form.phone,
                email: form.email,
                chair_id: parseInt(form.chair_id),
                time: utcTime,
                service_ids: form.service_ids,
            }]);
            this.state.formMessage = _t("Booking '%s' created successfully.").replace('%s', result.name);
            this.state.formMessageType = 'success';
            this.state.bookingForm = {
                name: '', phone: '', email: '', chair_id: false, time: '', service_ids: [],
            };
            await this.render_dashboards();
        } catch (error) {
            const message = (error && error.data && error.data.message)
                || (error && error.message)
                || _t("Could not create the booking. Please check the selected chair and time.");
            this.state.formMessage = message;
            this.state.formMessageType = 'danger';
        } finally {
            this._submitting.set(false);
        }
    }
}

actionRegistry.add("salon_dashboard", SalonDashboard);
