/**
 * DriveX theme frontend interactions.
 *
 * Provides the custom date pickers and selects, the homepage search and
 * dynamic vehicle sections, the fleet page filters, the car detail sidebar
 * and the multi-step booking wizard of the DriveX car rental website.
 */
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";
import { rpc } from "@web/core/network/rpc";
import { registry } from "@web/core/registry";
import { Interaction } from "@web/public/interaction";

const MONTHS_LONG = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
const MONTHS_SHORT = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

/** Every date picker of the page, so opening one closes the others. */
const allPickers = [];

/**
 * Calendar + time popup bound to a `.date-field` element.
 *
 * The panel is moved to <body> while open so it is never clipped by its
 * ancestors, and put back in the field when closed.
 */
class DatePicker {
    /**
     * @param {HTMLElement} field element toggling the picker
     * @param {HTMLElement} display element showing the selected date
     * @param {HTMLElement} panel calendar popup
     */
    constructor(field, display, panel) {
        this.field = field;
        this.display = display;
        this.panel = panel;
        if (!this.field || !this.display || !this.panel) return;
        const now = new Date();
        this.s = {
            viewYear: now.getFullYear(), viewMonth: now.getMonth(),
            selYear: null, selMonth: null, selDay: null,
            hour: 12, minute: 0, open: false
        };
        this._bind();
        this._render();
    }

    /** Bind the field, navigation, time and confirm buttons. */
    _bind() {
        this.field.addEventListener("click", e => {
            e.stopPropagation();
            this.s.open ? this._close() : this._open();
        });
        const prevBtn = this.panel.querySelector(".dp-prev");
        const nextBtn = this.panel.querySelector(".dp-next");
        if (prevBtn) {
            prevBtn.addEventListener("click", e => {
                e.stopPropagation();
                if (--this.s.viewMonth < 0) { this.s.viewMonth = 11; this.s.viewYear--; }
                this._renderHeader(); this._renderGrid();
            });
        }
        if (nextBtn) {
            nextBtn.addEventListener("click", e => {
                e.stopPropagation();
                if (++this.s.viewMonth > 11) { this.s.viewMonth = 0; this.s.viewYear++; }
                this._renderHeader(); this._renderGrid();
            });
        }
        const cols = this.panel.querySelectorAll(".dp-time-col");
        if (cols.length >= 2) {
            const hBtns = cols[0].querySelectorAll(".dp-tc");
            const mBtns = cols[1].querySelectorAll(".dp-tc");
            if (hBtns[0]) hBtns[0].addEventListener("click", e => { e.stopPropagation(); this.s.hour = (this.s.hour + 1) % 24; this._renderTime(); });
            if (hBtns[1]) hBtns[1].addEventListener("click", e => { e.stopPropagation(); this.s.hour = (this.s.hour + 23) % 24; this._renderTime(); });
            if (mBtns[0]) mBtns[0].addEventListener("click", e => { e.stopPropagation(); this.s.minute = (this.s.minute + 15) % 60; this._renderTime(); });
            if (mBtns[1]) mBtns[1].addEventListener("click", e => { e.stopPropagation(); this.s.minute = (this.s.minute + 45) % 60; this._renderTime(); });
        }
        const confirmBtn = this.panel.querySelector(".dp-confirm-btn");
        if (confirmBtn) {
            confirmBtn.addEventListener("click", e => {
                e.stopPropagation();
                if (this.s.selDay !== null) {
                    this._confirm();
                } else {
                    this.panel.classList.add("dp-shake");
                    setTimeout(() => this.panel.classList.remove("dp-shake"), 400);
                }
            });
        }
        this.panel.addEventListener("click", e => e.stopPropagation());
    }

    /** Render the whole panel. */
    _render() { this._renderHeader(); this._renderGrid(); this._renderTime(); }

    /** Render the "Month Year" title. */
    _renderHeader() {
        const el = this.panel.querySelector(".dp-my");
        if (el) el.textContent = `${MONTHS_LONG[this.s.viewMonth]} ${this.s.viewYear}`;
    }

    /** Render the day grid, disabling past, future and booked days as configured. */
    _renderGrid() {
        const grid = this.panel.querySelector(".dp-grid");
        if (!grid) return;
        grid.innerHTML = "";
        const { viewYear: y, viewMonth: m, selYear, selMonth, selDay } = this.s;
        const today = new Date();
        const [todayY, todayM, todayD] = [today.getFullYear(), today.getMonth(), today.getDate()];
        const firstDow = new Date(y, m, 1).getDay();
        const daysInMon = new Date(y, m + 1, 0).getDate();
        const daysInPrev = new Date(y, m, 0).getDate();
        const bookedRanges = this.bookedRanges || [];
        const isBooked = (d) => {
            const dt = new Date(y, m, d);
            return bookedRanges.some(r => {
                const from = new Date(r.from + 'T00:00:00');
                const to = new Date(r.to + 'T23:59:59');
                return dt >= from && dt <= to;
            });
        };
        const mk = (text, cls, onClick) => {
            const b = document.createElement("button");
            b.type = "button";
            b.textContent = text;
            b.className = "dp-day " + cls;
            if (onClick) b.addEventListener("click", e => { e.stopPropagation(); onClick(); });
            else b.tabIndex = -1;
            return b;
        };
        for (let i = firstDow - 1; i >= 0; i--) grid.appendChild(mk(daysInPrev - i, "dp-day--other"));
        for (let d = 1; d <= daysInMon; d++) {
            const isPast = new Date(y, m, d) < new Date(todayY, todayM, todayD);
            const isFuture = new Date(y, m, d) > new Date(todayY, todayM, todayD);
            const isToday = d === todayD && m === todayM && y === todayY;
            const isSelected = d === selDay && m === selMonth && y === selYear;
            // allowPast: past dates selectable (e.g. DOB)
            // blockFuture: future dates disabled (e.g. DOB)
            const disabledPast = isPast && !this.allowPast;
            const disabledFuture = isFuture && !!this.blockFuture;
            const isBookedDay = !disabledPast && isBooked(d);
            const isDisabled = disabledPast || disabledFuture || isBookedDay;
            const cls = [
                isToday ? "dp-day--today" : "",
                isSelected ? "dp-day--selected" : "",
                disabledPast ? "dp-day--past" : "",
                disabledFuture ? "dp-day--past" : "",
                isBookedDay ? "dp-day--booked" : "",
            ].join(" ").trim();
            const btn = mk(d, cls, isDisabled ? null : () => {
                this.s.selYear = y; this.s.selMonth = m; this.s.selDay = d; this._renderGrid();
            });
            if (isDisabled) btn.disabled = true;
            grid.appendChild(btn);
        }
        const total = firstDow + daysInMon;
        const tail = total % 7 === 0 ? 0 : 7 - (total % 7);
        for (let i = 1; i <= tail; i++) grid.appendChild(mk(i, "dp-day--other"));
    }

    /** Render the hour and minute counters. */
    _renderTime() {
        const hh = this.panel.querySelector(".dp-hh");
        const mm = this.panel.querySelector(".dp-mm");
        if (hh) hh.textContent = String(this.s.hour).padStart(2, "0");
        if (mm) mm.textContent = String(this.s.minute).padStart(2, "0");
    }

    /** Show the selected date in the display, sync the hidden input and close. */
    _confirm() {
        const { selYear: y, selMonth: m, selDay: d, hour: h, minute: mi } = this.s;
        this.display.classList.remove("placeholder");
        const q = sel => this.display.querySelector(sel);
        const dayEl = q(".dd-day"), monEl = q(".dd-month"), yearEl = q(".dd-year"), timeEl = q(".dd-time");
        if (dayEl) dayEl.textContent = String(d).padStart(2, "0");
        if (monEl) monEl.textContent = MONTHS_SHORT[m];
        if (yearEl) yearEl.textContent = y;
        if (timeEl) timeEl.textContent = `${String(h).padStart(2, "0")}:${String(mi).padStart(2, "0")}`;
        // Sync value to linked hidden input (YYYY-MM-DD)
        if (this.hiddenInput) {
            const mm = String(m + 1).padStart(2, '0');
            const dd = String(d).padStart(2, '0');
            this.hiddenInput.value = `${y}-${mm}-${dd}`;
            this.hiddenInput.dispatchEvent(new Event('change', { bubbles: true }));
        }
        this._close();
    }

    /**
     * Disable the days covered by existing bookings.
     *
     * @param {{from: string, to: string}[]} ranges YYYY-MM-DD date ranges
     */
    setBookedRanges(ranges) {
        this.bookedRanges = ranges || [];
        this._renderGrid();
    }

    /** Open the panel, closing the other pickers and custom selects. */
    _open() {
        allPickers.forEach(dp => { if (dp !== this) dp._close(); });
        // Custom selects can live anywhere on the page, so look them up from <body>.
        this.field.closest('body').querySelectorAll(".cs-wrap.open").forEach(s => s.classList.remove("open"));
        if (this.panel.parentElement !== document.body) document.body.appendChild(this.panel);
        this._positionPanel();
        this.s.open = true;
        this.panel.classList.add("dp-open");
        this._scrollHandler = () => { if (this.s.open) this._positionPanel(); };
        window.addEventListener("scroll", this._scrollHandler, { passive: true });
    }

    /** Place the fixed panel under the field, keeping it inside the viewport. */
    _positionPanel() {
        const rect = this.field.getBoundingClientRect();
        const panelW = 300, vw = window.innerWidth;
        const top = rect.bottom + 8;
        let left = rect.left;
        if (left + panelW > vw - 12) left = rect.right - panelW;
        this.panel.style.cssText = `position:fixed;top:${top}px;left:${left}px;width:300px;z-index:999999;margin:0;`;
    }

    /** Close the panel and move it back into its field. */
    _close() {
        this.s.open = false;
        this.panel.classList.remove("dp-open");
        if (this._scrollHandler) { window.removeEventListener("scroll", this._scrollHandler); this._scrollHandler = null; }
        if (this.panel.parentElement === document.body && this.field) {
            this.field.appendChild(this.panel);
            this.panel.style.cssText = "";
        }
    }
}

// Clicking anywhere else on the page closes every open picker.
document.addEventListener("click", () => allPickers.forEach(dp => dp._close()));

/**
 * Capitalize the first letter and lowercase the rest.
 *
 * @param {string} str
 * @returns {string}
 */
function capitalize(str) {
    if (!str) return "";
    return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
}

/**
 * Show a simple notice dialog.
 *
 * @param {Object} dialogService the `dialog` service
 * @param {string} message
 */
function showAlert(dialogService, message) {
    dialogService.add(AlertDialog, {
        body: message,
        title: _t("Notice"),
        confirmLabel: _t("Close"),
    });
}

/**
 * Build a delegated event handler for an Interaction root.
 *
 * Interactions bind listeners directly on the matched nodes, so nodes injected
 * later (e.g. filter buttons or select options loaded over RPC) would be
 * missed. This uses one listener on the root and dispatches to every handler
 * whose selector matches the event target.
 *
 * @param {Array<[string, Function]>} pairs selector / handler pairs
 * @returns {Function}
 */
function delegate(pairs) {
    return function (ev) {
        for (const [selector, handler] of pairs) {
            const target = ev.target.closest && ev.target.closest(selector);
            if (target && this.el.contains(target)) {
                handler.call(this, ev, target);
            }
        }
    };
}

/**
 * Create a DatePicker inside a field and link its hidden input.
 *
 * @param {HTMLElement} fieldEl
 * @returns {DatePicker|null}
 */
function buildLinkedPicker(fieldEl) {
    const display = fieldEl.querySelector('.date-display');
    const panel = fieldEl.querySelector('.dp-panel');
    const hidden = fieldEl.querySelector('input[type="hidden"]');
    if (!display || !panel) return null;
    const dp = new DatePicker(fieldEl, display, panel);
    dp.hiddenInput = hidden || null;
    allPickers.push(dp);
    fieldEl._dpInstance = dp;
    return dp;
}

/**
 * Select the date of a picker from a YYYY-MM-DD string.
 *
 * @param {DatePicker|null} dp
 * @param {string} dateStr
 */
function prefillPicker(dp, dateStr) {
    if (!dp || !dateStr) return;
    const [y, m, d] = dateStr.split('-').map(Number);
    if (!y || !m || !d) return;
    dp.s.selYear = y;
    dp.s.selMonth = m - 1;
    dp.s.selDay = d;
    dp.s.viewYear = y;
    dp.s.viewMonth = m - 1;
    dp._renderGrid();
    dp._confirm();
}

/**
 * Select the <select> option whose value or text matches, and notify listeners.
 *
 * @param {HTMLSelectElement|null} sel
 * @param {string} val
 */
function selectOption(sel, val) {
    if (!sel || !val) return;
    for (const option of sel.options) {
        if (option.value === val || option.text.includes(val)) {
            sel.selectedIndex = option.index;
            sel.dispatchEvent(new Event('change', { bubbles: true }));
            break;
        }
    }
}

/**
 * Select the location option matching an id or a name (case-insensitive).
 *
 * @param {HTMLSelectElement|null} sel
 * @param {string} loc
 */
function selectLocation(sel, loc) {
    if (!sel) return;
    for (const option of sel.options) {
        if (String(option.value) === String(loc) ||
            option.text.toLowerCase().trim() === loc.toLowerCase().trim()) {
            sel.selectedIndex = option.index;
            break;
        }
    }
}

/**
 * Copy the selected dates into the "Reserve Now" button URL of the sidebar.
 *
 * @param {HTMLElement} sidebar
 */
function syncDetailBtn(sidebar) {
    const btn = sidebar.querySelector('.booking-btn');
    const pickup = sidebar.querySelector('.bookPickup');
    const ret = sidebar.querySelector('.bookReturn');
    if (!btn || !pickup || !ret) return;
    const href = btn.getAttribute('href') || '';
    try {
        const url = new URL(href, window.location.origin);
        if (pickup.value) url.searchParams.set('pickup_date', pickup.value);
        if (ret.value) url.searchParams.set('return_date', ret.value);
        btn.setAttribute('href', url.pathname + url.search);
    } catch {
        // Unparsable href: leave the button untouched.
    }
}

/**
 * Fetch the booked date ranges of a vehicle.
 *
 * @param {string} vehicleId
 * @returns {Promise<{from: string, to: string}[]>} empty list on error
 */
function fetchBookedRanges(vehicleId) {
    if (!vehicleId || vehicleId === '0') return Promise.resolve([]);
    return rpc(`/vehicle/${vehicleId}/booked-dates`)
        .then(result => (result && result.ranges) || [])
        .catch(() => []);
}

/**
 * Build the HTML of a homepage vehicle card.
 *
 * @param {Object} v vehicle data returned by /homepage/data
 * @returns {HTMLElement}
 */
function renderVehicleCard(v) {
    const card = document.createElement('div');
    card.className = 'car-card';
    card.dataset.category = v.category_lower;
    card.innerHTML =
        '<div class="car-image">' +
            '<span class="car-badge">' + (v.category || '') + '</span>' +
            '<img src="' + v.image + '" alt="' + v.name + '">' +
        '</div>' +
        '<div class="car-info">' +
            '<div class="car-title-row">' +
                '<h3>' + v.name + '</h3>' +
                '<div class="price">$' + v.daily_rate + ' <span>/ day</span></div>' +
            '</div>' +
            '<p class="car-type"><i class="fa-solid fa-tag"></i> ' + (v.category || '') + ' · ' + v.horsepower + ' HP</p>' +
            '<div class="car-specs">' +
                '<span><i class="fa-solid fa-sliders"></i> ' + v.transmission + '</span>' +
                '<span><i class="fa-solid fa-users"></i> ' + v.seats + ' Seats</span>' +
                '<span><i class="fa-solid fa-gas-pump"></i> ' + v.fuel_type + '</span>' +
            '</div>' +
            '<div class="card-footer">' +
                '<a href="/car-detail/' + v.id + '" class="view-link"><i class="fa-solid fa-arrow-right"></i> View Details</a>' +
                '<a href="/booking/' + v.id + '" class="rent-btn">Rent Now</a>' +
            '</div>' +
        '</div>';
    return card;
}

/**
 * Replace a vehicle grid content with the "No Vehicles Available" message.
 *
 * @param {HTMLElement} grid
 */
function showFleetUnavailable(grid) {
    grid.innerHTML =
        '<div style="text-align:center;padding:60px 20px;width:100%;">' +
            '<i class="fa-solid fa-car" style="font-size:2.8rem;color:#ccc;margin-bottom:16px;display:block;"></i>' +
            '<h3 style="font-size:1.4rem;font-weight:700;color:#222;margin-bottom:10px;">No Vehicles Available</h3>' +
            '<p style="font-size:0.95rem;color:#666;max-width:420px;margin:0 auto;">' +
                'No vehicles have been published yet. Configure and publish vehicles from the Fleet module in the backend.' +
            '</p>' +
        '</div>';
}

/**
 * Fill a filter bar with one button per vehicle category.
 *
 * The bar is forced to flex centering because the Website Builder can
 * override the SCSS rule.
 *
 * @param {HTMLElement} filter
 * @param {Object[]} categories
 */
function addCategoryFilterButtons(filter, categories) {
    filter.style.display = 'flex';
    filter.style.justifyContent = 'center';
    filter.style.alignItems = 'center';
    filter.style.flexWrap = 'wrap';
    categories.forEach(cat => {
        const btn = document.createElement('button');
        btn.className = 'filter-btn';
        btn.dataset.filter = cat.name_lower;
        btn.textContent = cat.name;
        filter.appendChild(btn);
    });
}

/** Custom dropdown select (`.cs-wrap`). */
export class ThemeDriveXCustomSelect extends Interaction {
    static selector = ".cs-wrap";
    dynamicContent = {
        _root: {
            "t-on-click": delegate([
                [".cs-trigger", this.onTriggerClick],
                [".cs-opt", this.onOptionClick],
            ]),
        },
    };

    start() {
        this.addListener(document, "click", () => this.el.classList.remove("open"));
    }

    /** Toggle this select, closing any other open one. */
    onTriggerClick(e) {
        e.stopPropagation();
        const isOpen = this.el.classList.contains("open");
        // Other custom selects can live anywhere on the page.
        this.el.closest('body').querySelectorAll(".cs-wrap.open").forEach(s => s.classList.remove("open"));
        if (!isOpen) this.el.classList.add("open");
    }

    /** Select the clicked option. */
    onOptionClick(e, opt) {
        const valEl = this.el.querySelector(".cs-val");
        if (valEl) valEl.textContent = opt.textContent.trim();
        this.el.querySelectorAll(".cs-opt").forEach(o => o.classList.remove("cs-opt--active"));
        opt.classList.add("cs-opt--active");
        this.el.classList.remove("open");
    }
}

/** Date + time picker of the homepage search (`.date-field`). */
export class ThemeDriveXDatePicker extends Interaction {
    static selector = ".date-field";

    start() {
        const display = this.el.querySelector(".date-display");
        const panel = this.el.querySelector(".dp-panel");
        if (display && panel) {
            this.dp = new DatePicker(this.el, display, panel);
            this.el._dpInstance = this.dp;
            allPickers.push(this.dp);
        }
    }
}

/**
 * Date-only pickers of the booking wizard (date of birth, licence expiry).
 *
 * The panel markup has no time section; the hidden input receives YYYY-MM-DD.
 */
export class ThemeDriveXDatePickerSimple extends Interaction {
    static selector = ".dobField, .licExpiryField";

    start() {
        const display = this.el.querySelector('.date-display');
        const panel = this.el.querySelector('.dp-panel');
        const hidden = this.el.querySelector('input[type="hidden"]');
        if (!display || !panel) return;
        const dp = new DatePicker(this.el, display, panel);
        dp.hiddenInput = hidden;

        if (this.el.classList.contains('dobField')) {
            dp.allowPast = true;
            dp.blockFuture = true;
            dp.s.viewYear = new Date().getFullYear() - 30;
        } else if (this.el.classList.contains('licExpiryField')) {
            dp.allowPast = true;
        }

        this.el._dpInstance = dp;
        allPickers.push(dp);
        dp._render();

        if (hidden && this.el.classList.contains('dobField')) {
            hidden.addEventListener('change', () => this._updateAge(hidden.value));
        }
    }

    /**
     * Show the driver age computed from the date of birth.
     *
     * @param {string} val YYYY-MM-DD date of birth
     */
    _updateAge(val) {
        if (!val) return;
        const [y, mo, d] = val.split('-').map(Number);
        const today = new Date();
        const age = today.getFullYear() - y
            - ((today.getMonth() + 1 < mo ||
                (today.getMonth() + 1 === mo && today.getDate() < d)) ? 1 : 0);
        const wrap = this.el.closest('#wrap');
        const ageInput = wrap && wrap.querySelector('.driverAge');
        if (ageInput) ageInput.value = age + ' years';
    }
}

/** Category filter buttons of the homepage fleet section. */
export class ThemeDriveXFleetFilter extends Interaction {
    static selector = ".fleet-section";
    dynamicContent = {
        _root: {
            "t-on-click": delegate([[".filter-btn", this.onClick]]),
        },
    };

    /** Show only the cards of the clicked category. */
    onClick(e, btn) {
        this.el.querySelectorAll(".filter-btn").forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        const filter = (btn.dataset.filter || "all").toLowerCase();
        this.el.querySelectorAll(".car-card").forEach(card => {
            const cat = (card.dataset.category || "").toLowerCase();
            const show = filter === "all" || cat.includes(filter);
            card.style.display = show ? "" : "none";
        });
    }
}

/** Fleet page: search, category filter, sort and grid/list toggle. */
export class ThemeDriveXFleetPage extends Interaction {
    static selector = ".fleet-page";
    dynamicContent = {
        _root: {
            "t-on-click": delegate([
                [".fb-cat", this.onCatFilter],
                [".fv-btn", this.onViewToggle],
                ["#resetFiltersBtn", this.onResetFilters],
            ]),
            "t-on-input": delegate([["#carSearch", this.onSearch]]),
            "t-on-change": delegate([["#sortSelect", this.onSort]]),
        },
    };

    start() {
        const filterBar = this.el.querySelector('#filterBarWrap');
        if (filterBar) {
            const onScroll = () => {
                filterBar.classList.toggle("fb-sticky", window.scrollY > 100);
            };
            this.addListener(window, "scroll", onScroll, { passive: true });
        }

        // Initialize original order index for default sort
        this.el.querySelectorAll(".fc-card").forEach((card, index) => {
            if (!card.dataset.index) card.dataset.index = index;
        });

        this._updateCount();
        this._updateHeroStats();

        // Hide category filter bar when no vehicles
        const fbCats = this.el.querySelector('#fbCats');
        if (fbCats) {
            fbCats.style.display = this.el.querySelectorAll('.fc-card').length === 0 ? 'none' : '';
        }
    }

    /**
     * Show the number of visible vehicles.
     *
     * @param {number} [visible] defaults to the number of shown cards
     */
    _updateCount(visible) {
        const cnt = this.el.querySelector('#resultsCount');
        if (!cnt) return;
        if (visible === undefined) {
            visible = Array.from(this.el.querySelectorAll('.fc-card'))
                .filter(c => c.style.display !== 'none').length;
        }
        cnt.innerHTML = `Showing <strong>${visible}</strong> vehicle${visible !== 1 ? 's' : ''}`;
    }

    /** Show the vehicle and category counts in the page hero. */
    _updateHeroStats() {
        const cards = this.el.querySelectorAll('.fc-card');
        const total = cards.length;
        const catSet = new Set();
        cards.forEach(c => {
            const cat = (c.dataset.cat || '').trim();
            if (cat && cat !== 'all') {
                cat.split(' ').forEach(part => { if (part) catSet.add(part); });
            }
        });
        const heroCount = this.el.querySelector('#heroVehicleCount');
        const heroCats = this.el.querySelector('#heroCategoryCount');
        if (heroCount) heroCount.textContent = total > 0 ? total + '+' : total;
        if (heroCats) heroCats.textContent = catSet.size;
    }

    /**
     * Toggle the "no results" message.
     *
     * @param {number} visible number of shown cards
     * @param {number} total number of cards
     */
    _toggleNoResults(visible, total) {
        const noRes = this.el.querySelector('#noResults');
        if (noRes) noRes.style.display = (visible === 0 && total > 0) ? '' : 'none';
    }

    /** Mark the "All" category button as the active one. */
    _activateAllCategory() {
        this.el.querySelectorAll('.fb-cat').forEach(b => b.classList.remove('active'));
        const allBtn = this.el.querySelector('.fb-cat[data-cat="all"]');
        if (allBtn) allBtn.classList.add('active');
    }

    /** Show only the cards of the clicked category. */
    onCatFilter(e, btn) {
        this.el.querySelectorAll(".fb-cat").forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        const filter = (btn.dataset.cat || "all").toLowerCase();
        const cards = this.el.querySelectorAll(".fc-card");
        let visible = 0;
        cards.forEach(card => {
            const cat = (card.dataset.cat || "").toLowerCase();
            const show = filter === "all" || cat.split(" ").some(c => c === filter);
            card.style.display = show ? "" : "none";
            if (show) visible++;
        });
        this._updateCount(visible);
        this._toggleNoResults(visible, cards.length);
        // Drop the grid layout when only the no-results message is left
        const grid = this.el.querySelector('#fleetGrid');
        if (grid) grid.classList.toggle('fc-grid', visible > 0);
    }

    /** Filter the cards by name, resetting the category filter. */
    onSearch(e, input) {
        const q = input.value.toLowerCase().trim();
        this._activateAllCategory();
        const cards = this.el.querySelectorAll(".fc-card");
        let visible = 0;
        cards.forEach(card => {
            const name = (card.querySelector("h3") || card).textContent.toLowerCase();
            const show = !q || name.includes(q);
            card.style.display = show ? "" : "none";
            if (show) visible++;
        });
        this._updateCount(visible);
        this._toggleNoResults(visible, cards.length);
    }

    /** Switch between grid and list display. */
    onViewToggle(e, btn) {
        this.el.querySelectorAll(".fv-btn").forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        const grid = this.el.querySelector('#fleetGrid');
        if (grid) grid.classList.toggle("fc-list-mode", btn.dataset.view === "list");
    }

    /** Reorder the cards by price, rating, year or original order. */
    onSort(e, select) {
        const sortType = select.value;
        const grid = this.el.querySelector('#fleetGrid');
        if (!grid) return;

        const cards = Array.from(grid.querySelectorAll(".fc-card"));
        cards.sort((a, b) => {
            if (sortType === 'price-asc') {
                return parseFloat(a.dataset.price || 0) - parseFloat(b.dataset.price || 0);
            } else if (sortType === 'price-desc') {
                return parseFloat(b.dataset.price || 0) - parseFloat(a.dataset.price || 0);
            } else if (sortType === 'rating') {
                return parseFloat(b.dataset.rating || 0) - parseFloat(a.dataset.rating || 0);
            } else if (sortType === 'newest') {
                return parseInt(b.dataset.year || 0) - parseInt(a.dataset.year || 0);
            }
            return parseInt(a.dataset.index || 0) - parseInt(b.dataset.index || 0);
        });
        cards.forEach(card => grid.appendChild(card));
    }

    /** Clear the search and category filter and show every card. */
    onResetFilters() {
        this._activateAllCategory();
        const searchInput = this.el.querySelector('#carSearch');
        if (searchInput) searchInput.value = '';
        this.el.querySelectorAll('.fc-card').forEach(card => { card.style.display = ''; });
        this._updateCount();
        const noRes = this.el.querySelector('#noResults');
        if (noRes) noRes.style.display = 'none';
    }
}

/** Homepage search button: validates the dates and opens the fleet page. */
export class ThemeDriveXHomepageSearch extends Interaction {
    static selector = ".search-btn";
    dynamicContent = {
        _root: {
            "t-on-click": this.onSearchClick,
        },
    };

    setup() {
        this.dialog = this.services.dialog;
    }

    /** Redirect to /fleet with the selected location, category and dates. */
    onSearchClick() {
        const container = this.el.closest(".search-box, section") || this.el.parentElement;
        const locOpt = container.querySelector(".locationSelect .cs-opt--active, #locationSelect .cs-opt--active");
        const catOpt = container.querySelector(".carTypeSelect .cs-opt--active, #carTypeSelect .cs-opt--active");

        const locVal = locOpt ? locOpt.dataset.value : "";
        const catVal = catOpt ? catOpt.dataset.value : "all";

        const pickupField = container.querySelector(".pickupField, #pickupField");
        const returnField = container.querySelector(".returnField, #returnField");

        const pDp = pickupField && pickupField._dpInstance;
        const rDp = returnField && returnField._dpInstance;

        if (!pDp || pDp.s.selDay === null || !rDp || rDp.s.selDay === null) {
            showAlert(this.dialog, _t("Please select both Pickup Date and Return Date."));
            return;
        }

        const formatNum = n => String(n).padStart(2, "0");
        const formatDate = dp => `${dp.s.selYear}-${formatNum(dp.s.selMonth + 1)}-${formatNum(dp.s.selDay)}`;
        const formatTime = dp => {
            const h = dp.s.hour;
            return `${formatNum(h > 12 ? h - 12 : (h === 0 ? 12 : h))}:${formatNum(dp.s.minute)} ${h >= 12 ? 'PM' : 'AM'}`;
        };
        const toDate = dp => new Date(dp.s.selYear, dp.s.selMonth, dp.s.selDay, dp.s.hour, dp.s.minute);

        if (toDate(rDp) <= toDate(pDp)) {
            showAlert(this.dialog, _t("Return Date & Time must be after the Pickup Date & Time."));
            return;
        }

        let url = `/fleet?pickup_date=${formatDate(pDp)}&pickup_time=${encodeURIComponent(formatTime(pDp))}&return_date=${formatDate(rDp)}&return_time=${encodeURIComponent(formatTime(rDp))}`;
        if (locVal) url += `&pickup_loc=${encodeURIComponent(locVal)}`;
        if (catVal && catVal !== 'all') url += `&category=${encodeURIComponent(catVal)}`;

        window.location.href = url;
    }
}

/** FAQ item: only one answer open at a time within its section. */
export class ThemeDriveXFaqAccordion extends Interaction {
    static selector = ".faq-item";
    dynamicContent = {
        _root: {
            "t-on-click": delegate([[".faq-question", this.onToggle]]),
        },
    };

    /** Open this item and close its siblings. */
    onToggle() {
        const isOpen = this.el.classList.contains("open");
        const container = this.el.closest("section") || this.el.parentElement;
        container.querySelectorAll(".faq-item").forEach(i => i.classList.remove("open"));
        if (!isOpen) this.el.classList.add("open");
    }
}

/** Fade cards in when they scroll into view. */
export class ThemeDriveXScrollReveal extends Interaction {
    static selector = ".car-card, .fc-card, .feature, .step, .review, .stat, .service-card, .value-card, .team-card, .pricing-card, .contact-info-card";

    start() {
        if (typeof IntersectionObserver === "undefined") return;
        this.el.classList.add("reveal");
        const observer = new IntersectionObserver((entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    setTimeout(() => entry.target.classList.add("revealed"), 80);
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.1 });
        observer.observe(this.el);
        this.registerCleanup(() => observer.disconnect());
    }
}

/** Multi-step booking wizard: steps, extras, live pricing and submission. */
export class ThemeDriveXBookingWizard extends Interaction {
    static selector = "#wrap";
    dynamicContent = {
        _root: {
            "t-on-click": delegate([
                [".bw-btn-next-action", this._onNextStep],
                [".bw-btn-back-action", this._onPrevStep],
                [".bw-ins-card", this._onSelectInsurance],
                [".bw-addon", this._onToggleAddon],
                [".bw-btn-confirm-action", this._onConfirmBooking],
                [".bw-btn-copy-ref", this._onCopyRef],
            ]),
            "t-on-change": delegate([
                [".tripPickup", this._updatePricing],
                [".tripReturn", this._updatePricing],
                [".tripPickupTime", this._updatePricing],
                [".tripReturnTime", this._updatePricing],
            ]),
        },
    };

    setup() {
        this.dialog = this.services.dialog;
    }

    /** Pre-fill the trip from the URL parameters and compute the price. */
    start() {
        const urlParams = new URLSearchParams(window.location.search);
        const pDate = urlParams.get('pickup_date');
        const pTime = urlParams.get('pickup_time');
        const rDate = urlParams.get('return_date');
        const rTime = urlParams.get('return_time');
        const pLoc = urlParams.get('pickup_loc');
        const insId = urlParams.get('insurance_id');

        if (pDate) this._setVal('.tripPickup', pDate);
        if (rDate) this._setVal('.tripReturn', rDate);
        if (pTime) this._setVal('.tripPickupTime', pTime);
        if (rTime) this._setVal('.tripReturnTime', rTime);
        if (pLoc) selectLocation(this.el.querySelector('.tripPickupLoc'), pLoc);

        if (insId) {
            this.el.querySelectorAll('.bw-ins-card').forEach(card => this._styleInsuranceCard(card, false));
            const matchCard = this.el.querySelector(`.bw-ins-card[data-id="${insId}"]`);
            if (matchCard) this._styleInsuranceCard(matchCard, true);
        }

        this._updatePricing();
    }

    /**
     * Set the value of the first element matching the selector.
     *
     * @param {string} sel
     * @param {string} val
     */
    _setVal(sel, val) {
        const el = this.el.querySelector(sel);
        if (el) el.value = val;
    }

    /**
     * Mark an insurance card as selected or not.
     *
     * @param {HTMLElement} card
     * @param {boolean} selected
     */
    _styleInsuranceCard(card, selected) {
        card.classList.toggle('selected', selected);
        card.style.border = selected ? '2px solid var(--accent)' : '2px solid rgba(255,255,255,.08)';
        card.style.background = selected ? 'rgba(212,25,28,.06)' : 'transparent';
    }

    /** Validate the current step and move to the next one. */
    _onNextStep(e, target) {
        const current = parseInt(target.dataset.nextStep);
        const curr = this.el.querySelector(".step" + current);
        if (curr) {
            const inputs = curr.querySelectorAll("input[required], select[required], textarea[required]");
            for (const input of inputs) {
                if (!input.value || input.value.trim() === "") {
                    showAlert(this.dialog, _t("Please fill in all required fields."));
                    input.focus();
                    return;
                }
            }
        }
        const next = this.el.querySelector(".step" + (current + 1));
        if (!curr || !next) return;
        curr.classList.remove("active");
        next.classList.add("active");

        const steps = this.el.querySelectorAll(".bw-step");
        if (steps[current - 1]) { steps[current - 1].classList.remove("active"); steps[current - 1].classList.add("done"); }
        const lines = this.el.querySelectorAll(".bw-step-line");
        if (lines[current - 1]) lines[current - 1].classList.add("done");
        if (steps[current]) steps[current].classList.add("active");

        // Mark all steps as done when reaching confirmation page (step 4)
        if (current === 3) {
            steps.forEach(step => {
                step.classList.remove("active");
                step.classList.add("done");
            });
            lines.forEach(line => line.classList.add("done"));
        }

        // Update pricing when entering extras step (step 3)
        if (current === 2) {
            this._updatePricing();
        }

        window.scrollTo({ top: 0, behavior: "smooth" });
    }

    /** Go back to the previous step. */
    _onPrevStep(e, target) {
        const current = parseInt(target.dataset.prevStep);
        const curr = this.el.querySelector(".step" + current);
        const prev = this.el.querySelector(".step" + (current - 1));
        if (!curr || !prev) return;
        curr.classList.remove("active");
        prev.classList.add("active");

        const steps = this.el.querySelectorAll(".bw-step");
        if (steps[current - 1]) steps[current - 1].classList.remove("active");
        if (steps[current - 2]) { steps[current - 2].classList.remove("done"); steps[current - 2].classList.add("active"); }
        const lines = this.el.querySelectorAll(".bw-step-line");
        if (lines[current - 2]) lines[current - 2].classList.remove("done");

        // Update pricing when going back to extras step (step 3)
        if (current === 4) {
            this._updatePricing();
        }

        window.scrollTo({ top: 0, behavior: "smooth" });
    }

    /** Select the clicked insurance plan. */
    _onSelectInsurance(e, target) {
        this.el.querySelectorAll(".bw-ins-card").forEach(c => this._styleInsuranceCard(c, false));
        this._styleInsuranceCard(target, true);
        this._updatePricing();
    }

    /** Toggle the clicked add-on. */
    _onToggleAddon(e, target) {
        const selected = target.classList.toggle("selected");
        target.style.border = selected ? "1px solid var(--accent)" : "1px solid rgba(255,255,255,.08)";
        target.style.background = selected ? "rgba(212,25,28,.06)" : "transparent";
        this._updatePricing();
    }

    /**
     * Parse a "HH:MM AM/PM" time string into { hours, minutes } (24-hour).
     * Mirrors the backend's strptime('%I:%M %p') logic so day counts match.
     *
     * @param {string} timeStr
     * @returns {{hours: number, minutes: number}}
     */
    _parseTime(timeStr) {
        if (!timeStr) return { hours: 12, minutes: 0 };
        const m = timeStr.trim().match(/^(\d{1,2}):(\d{2})\s*(AM|PM)$/i);
        if (!m) return { hours: 12, minutes: 0 };
        let hours = parseInt(m[1], 10);
        const minutes = parseInt(m[2], 10);
        const ampm = m[3].toUpperCase();
        if (ampm === 'AM') {
            if (hours === 12) hours = 0;   // 12:xx AM → 00:xx
        } else {
            if (hours !== 12) hours += 12; // 01-11 PM → 13-23
        }
        return { hours, minutes };
    }

    /**
     * Build a local Date from a date string (YYYY-MM-DD) and a time string
     * (HH:MM AM/PM), so arithmetic matches what the user sees.
     *
     * @param {string} dateStr
     * @param {string} timeStr
     * @returns {Date|null}
     */
    _buildDatetime(dateStr, timeStr) {
        if (!dateStr) return null;
        const { hours, minutes } = this._parseTime(timeStr);
        const [year, month, day] = dateStr.split('-').map(Number);
        return new Date(year, month - 1, day, hours, minutes, 0, 0);
    }

    /** Recompute the rental days and the price summary. */
    _updatePricing() {
        const sumDays = this.el.querySelector(".sumDays");
        const sumIns = this.el.querySelector(".sumInsurance");
        const sumAddons = this.el.querySelector(".sumAddons");
        const sumTotal = this.el.querySelector(".sumTotal");
        const baseRateSpan = this.el.querySelector(".sumBaseRate");
        const pickupInput = this.el.querySelector(".tripPickup");
        const returnInput = this.el.querySelector(".tripReturn");
        const pickupTimeInput = this.el.querySelector(".tripPickupTime");
        const returnTimeInput = this.el.querySelector(".tripReturnTime");

        if (!sumTotal || !baseRateSpan) return;

        const dailyRate = parseFloat((baseRateSpan.textContent || "0").replace(/[^0-9.]/g, ""));
        let days = 1;

        if (pickupInput && returnInput && pickupInput.value && returnInput.value) {
            // Combine date + time exactly as the backend does, so the
            // displayed day count always matches the backend calculation.
            const pickupDt = this._buildDatetime(
                pickupInput.value,
                pickupTimeInput ? pickupTimeInput.value : '12:00 PM'
            );
            const returnDt = this._buildDatetime(
                returnInput.value,
                returnTimeInput ? returnTimeInput.value : '12:00 PM'
            );
            if (pickupDt && returnDt && returnDt > pickupDt) {
                const rawDays = (returnDt - pickupDt) / 86400000;
                // Mirror backend: ceil fractional days, minimum 1. The epsilon
                // avoids rounding exact full days up because of float errors.
                days = Math.max(1, Math.ceil(rawDays - 1e-9));
            }
        }
        if (sumDays) sumDays.textContent = `${days} day${days !== 1 ? "s" : ""}`;

        const selIns = this.el.querySelector(".bw-ins-card.selected");
        let insDailyRate = 0;
        if (selIns && selIns.dataset.price) insDailyRate = parseFloat(selIns.dataset.price);
        if (sumIns) sumIns.textContent = insDailyRate > 0 ? `+$${insDailyRate}/day` : 'Included';

        let totalAddons = 0;
        this.el.querySelectorAll(".bw-addon.selected").forEach(add => {
            const p = parseFloat(add.dataset.price || 0);
            totalAddons += add.dataset.type === 'per_day' ? p * days : p;
        });
        if (sumAddons) sumAddons.textContent = `+$${Math.round(totalAddons)}`;

        const total = (dailyRate * days) + (insDailyRate * days) + totalAddons;
        sumTotal.textContent = `$${Math.round(total)}`;
    }

    /** Submit the booking and show the confirmation step. */
    _onConfirmBooking(e, target) {
        const termsBox = this.el.querySelector(".termsCheck");
        if (termsBox && !termsBox.checked) {
            showAlert(this.dialog, _t("Please accept the terms and conditions."));
            return;
        }

        const btn = target;
        const originalHtml = btn.innerHTML;
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Processing...';

        const payload = {
            vehicle_id: this.el.querySelector("[data-vehicle-id]")?.dataset.vehicleId,
            pickup_date: this.el.querySelector(".tripPickup")?.value,
            return_date: this.el.querySelector(".tripReturn")?.value,
            pickup_time: this.el.querySelector(".tripPickupTime")?.value,
            return_time: this.el.querySelector(".tripReturnTime")?.value,
            pickup_location_id: this.el.querySelector(".tripPickupLoc")?.value,
            return_location_id: this.el.querySelector(".tripReturnLoc")?.value,

            driver_fname: this.el.querySelector(".driverFname")?.value || '',
            driver_lname: this.el.querySelector(".driverLname")?.value || '',
            driver_email: this.el.querySelector(".driverEmail")?.value || '',
            driver_phone: this.el.querySelector(".driverPhone")?.value || '',
            driver_license: this.el.querySelector(".driverLicense")?.value || '',

            driver_dob: this.el.querySelector(".driverDob")?.value || '',
            driver_license_expiry: this.el.querySelector(".driverLicenseExpiry")?.value || '',
            driver_license_state: this.el.querySelector(".driverLicenseState")?.value || '',
            driver_nationality: this.el.querySelector(".driverIssuingCountry")?.value || '',
            driver_personal_nationality: this.el.querySelector(".driverNationality")?.value || '',

            insurance_id: this.el.querySelector(".bw-ins-card.selected")?.dataset.id || null,
            addon_ids: Array.from(this.el.querySelectorAll(".bw-addon.selected")).map(el => el.dataset.id)
        };

        rpc('/booking/submit', payload)
            .then(result => {
                if (result && result.success) {
                    this._showConfirmation(result, payload.driver_email);
                } else {
                    showAlert(this.dialog, _t("Booking Error: %s", result ? result.error : _t("Unknown error")));
                }
            })
            .catch(() => {
                showAlert(this.dialog, _t("A network error occurred."));
            })
            .finally(() => {
                btn.innerHTML = originalHtml;
            });
    }

    /**
     * Fill the confirmation step with the booking returned by the server and
     * display it.
     *
     * @param {Object} result /booking/submit response
     * @param {string} email driver email
     */
    _showConfirmation(result, email) {
        const confirmEmail = this.el.querySelector(".confirmEmail");
        const ref = this.el.querySelector(".bookingRef");
        if (confirmEmail && email) confirmEmail.textContent = email;
        if (ref) ref.textContent = result.order_name;

        // Update summary with backend-calculated prices
        const sumBaseRate = this.el.querySelector(".sumBaseRate");
        const sumDays = this.el.querySelector(".sumDays");
        const sumInsurance = this.el.querySelector(".sumInsurance");
        const sumAddons = this.el.querySelector(".sumAddons");
        const sumTotal = this.el.querySelector(".sumTotal");

        if (sumBaseRate && result.daily_rate !== undefined) {
            sumBaseRate.textContent = result.daily_rate;
        }
        if (sumDays && result.days !== undefined) {
            sumDays.textContent = `${result.days} day${result.days !== 1 ? "s" : ""}`;
        }
        if (sumInsurance && result.amount_insurance !== undefined) {
            sumInsurance.textContent = result.amount_insurance > 0 ? `+$${result.amount_insurance}/day` : 'Included';
        }
        if (sumAddons && result.amount_addons !== undefined) {
            sumAddons.textContent = `+$${result.amount_addons}`;
        }
        if (sumTotal && result.amount_total !== undefined) {
            sumTotal.textContent = `$${result.amount_total}`;
        }

        this._onNextStep(null, { dataset: { nextStep: "3" } });
    }

    /** Copy the booking reference to the clipboard. */
    _onCopyRef() {
        const ref = this.el.querySelector(".bookingRef");
        if (ref && navigator.clipboard) navigator.clipboard.writeText(ref.textContent);
    }
}

/** Car detail page: specification values and image gallery. */
export class ThemeDriveXCarDetail extends Interaction {
    static selector = "#detail_content_zone";

    start() {
        const zone = this.el;
        const d = zone.dataset;

        const specMap = {
            horsepower: { sel: ".spec-value-horsepower", format: v => v ? `${v} HP` : "— HP" },
            transmission: { sel: ".spec-value-transmission", format: v => v ? capitalize(v) : "Auto" },
            seats: { sel: ".spec-value-seats", format: v => v ? `${v} Seats` : "— Seats" },
            doors: { sel: ".spec-value-doors", format: v => v ? `${v} Doors` : "— Doors" },
            fuel: { sel: ".spec-value-fuel", format: v => v ? capitalize(v) : "Petrol" },
            co2: { sel: ".spec-value-co2", format: v => v ? `${v} g/km` : "— g/km" },
        };

        Object.entries(specMap).forEach(([key, cfg]) => {
            const el = zone.querySelector(cfg.sel);
            if (el) el.textContent = cfg.format(d[key] || "");
        });

        // The gallery is outside the zone but in the same page wrapper.
        const wrap = zone.closest("#wrap");
        if (!wrap) return;
        const thumbs = wrap.querySelectorAll(".gallery-thumb");
        thumbs.forEach(thumb => {
            this.addListener(thumb, "click", () => {
                const src = thumb.dataset.src;
                const hero = wrap.querySelector(".heroImg");
                if (hero && src) hero.src = src;
                thumbs.forEach(t => t.classList.remove("active"));
                thumb.classList.add("active");
            });
        });
    }
}

/** Car detail sidebar: live price and "Reserve Now" link. */
export class ThemeDriveXDetailBooking extends Interaction {
    static selector = ".booking-sidebar";
    dynamicContent = {
        _root: {
            "t-on-change": delegate([
                [".bookPickup", this._recalc],
                [".bookReturn", this._recalc],
                [".insurancePlan", this._recalc],
                [".bookLocation", this._recalc],
            ]),
        },
    };

    start() {
        const pLoc = new URLSearchParams(window.location.search).get('pickup_loc');
        if (pLoc) selectLocation(this.el.querySelector('.bookLocation'), pLoc);
        this._recalc();
    }

    /** Recompute the total and update the "Reserve Now" URL. */
    _recalc() {
        const totalEl = this.el.querySelector('.totalVal');
        const daysEl = this.el.querySelector('.daysVal');
        const insLine = this.el.querySelector('.insuranceLine');
        const insValEl = this.el.querySelector('.insuranceVal');
        const insPlan = this.el.querySelector('.insurancePlan');
        const pickup = this.el.querySelector('.bookPickup');
        const ret = this.el.querySelector('.bookReturn');
        const locSel = this.el.querySelector('.bookLocation');
        const btn = this.el.querySelector('.booking-btn');

        if (!totalEl) return;

        const totalWidget = this.el.querySelector('.booking-total');
        const dailyRate = parseFloat(totalWidget ? totalWidget.dataset.dailyRate : (this.el.dataset.dailyRate || 0));

        // Store the pristine href once, then always derive from it
        if (btn && !btn.dataset.originalHref) {
            btn.dataset.originalHref = btn.getAttribute('href') || '';
        }
        const originalHref = btn ? btn.dataset.originalHref : '';

        // Days calculation from hidden inputs (set by custom DatePicker)
        let days = 1;
        if (pickup && ret && pickup.value && ret.value) {
            const ms = new Date(ret.value) - new Date(pickup.value);
            if (ms > 0) days = Math.ceil(ms / 86400000);
        }
        if (daysEl) daysEl.textContent = `${days} day${days !== 1 ? 's' : ''}`;

        // Insurance price from data-price attribute on the selected option
        const selectedOpt = insPlan ? insPlan.options[insPlan.selectedIndex] : null;
        const insPrice = selectedOpt ? parseFloat(selectedOpt.dataset.price || 0) : 0;
        const insId = selectedOpt ? selectedOpt.value : '';

        if (insLine) insLine.style.display = insPrice > 0 ? '' : 'none';
        if (insValEl) insValEl.textContent = insPrice > 0 ? `+$${insPrice}/day` : 'Included';

        const total = (dailyRate * days) + (insPrice * days);
        totalEl.textContent = `$${total.toFixed(0)}`;

        if (btn && originalHref) {
            try {
                const url = new URL(originalHref, window.location.origin);
                if (pickup && pickup.value) url.searchParams.set('pickup_date', pickup.value);
                if (ret && ret.value) url.searchParams.set('return_date', ret.value);
                if (locSel && locSel.value) url.searchParams.set('pickup_loc', locSel.value);
                if (insId) url.searchParams.set('insurance_id', insId);
                btn.setAttribute('href', url.pathname + url.search);
            } catch {
                // Unparsable href: leave the button untouched.
            }
        }
    }
}

/** Car detail sidebar date pickers, greying out the booked days. */
export class ThemeDriveXDetailDates extends Interaction {
    static selector = ".booking-sidebar";

    start() {
        const vehicleId = this.el.dataset.vehicleId;
        const pickupField = this.el.querySelector('.bookPickupField');
        const returnField = this.el.querySelector('.bookReturnField');
        if (!pickupField || !returnField) return;

        const pickupDp = buildLinkedPicker(pickupField);
        const returnDp = buildLinkedPicker(returnField);

        const sidebar = this.el;
        for (const dp of [pickupDp, returnDp]) {
            if (!dp) continue;
            const origConfirm = dp._confirm.bind(dp);
            dp._confirm = () => {
                origConfirm();
                syncDetailBtn(sidebar);
            };
        }

        if (vehicleId && vehicleId !== '0') {
            fetchBookedRanges(vehicleId).then(ranges => {
                if (pickupDp) pickupDp.setBookedRanges(ranges);
                if (returnDp) returnDp.setBookedRanges(ranges);
            });
        }
    }
}

/** Booking wizard step 1 date pickers, pre-filled from the URL. */
export class ThemeDriveXBookingDates extends Interaction {
    static selector = "#bwDateGrid";

    start() {
        const vehicleId = this.el.dataset.vehicleId;
        const pickupField = this.el.querySelector('.tripPickupField');
        const returnField = this.el.querySelector('.tripReturnField');
        if (!pickupField || !returnField) return;

        const pickupDp = buildLinkedPicker(pickupField);
        const returnDp = buildLinkedPicker(returnField);

        const urlParams = new URLSearchParams(window.location.search);
        const pDate = urlParams.get('pickup_date');
        const rDate = urlParams.get('return_date');

        if (pDate && rDate) {
            // Coming via Reserve Now: pre-fill display + hidden inputs
            prefillPicker(pickupDp, pDate);
            prefillPicker(returnDp, rDate);

            // Time selects live outside #bwDateGrid, in the page wrapper
            const pTime = urlParams.get('pickup_time');
            const rTime = urlParams.get('return_time');
            const wrap = this.el.closest('#wrap');
            if (wrap && pTime) selectOption(wrap.querySelector('.tripPickupTime'), pTime);
            if (wrap && rTime) selectOption(wrap.querySelector('.tripReturnTime'), rTime);
        } else if (vehicleId && vehicleId !== '0') {
            // Direct visit: fetch booked ranges so unavailable days are greyed out
            fetchBookedRanges(vehicleId).then(ranges => {
                if (pickupDp) pickupDp.setBookedRanges(ranges);
                if (returnDp) returnDp.setBookedRanges(ranges);
            });
        }
    }
}

/** Homepage: loads locations, categories and featured vehicles. */
export class ThemeDriveXHomepageLoader extends Interaction {
    static selector = "#wrap";

    start() {
        // Only on the homepage, identified by its hero section
        if (!this.el.querySelector('.hero')) return;

        this.waitFor(rpc('/homepage/data'))
            .then(result => {
                if (!result) return;
                this._populateLocations(result.locations || []);
                this._populateCarTypes(result.categories || [], result.has_vehicles);
                this._populateFleetFilters(result.categories || [], result.has_vehicles);
                this._populateVehicleCards(result.vehicles || [], result.has_vehicles);
            })
            .catch(() => this._showUnavailableStates());
    }

    /**
     * Fill the pickup location select.
     *
     * @param {Object[]} locations
     */
    _populateLocations(locations) {
        const locationMenu = this.el.querySelector('#locationOptions');
        if (!locationMenu) return;
        locationMenu.innerHTML = '';
        locations.forEach(loc => {
            const opt = document.createElement('div');
            opt.className = 'cs-opt';
            opt.dataset.value = loc.id;
            opt.innerHTML = '<span class="cs-opt-icon"><i class="fa-solid fa-building"></i></span>' + loc.name;
            locationMenu.appendChild(opt);
        });
    }

    /**
     * Fill the car type select.
     *
     * @param {Object[]} categories
     * @param {boolean} hasVehicles
     */
    _populateCarTypes(categories, hasVehicles) {
        const carTypeMenu = this.el.querySelector('#carTypeOptions');
        if (!carTypeMenu) return;
        carTypeMenu.innerHTML = '<div class="cs-opt cs-opt--active" data-value="all"><span class="cs-opt-icon"><i class="fa-solid fa-car-side"></i></span>All Vehicles</div>';
        if (!hasVehicles) return;
        categories.forEach(cat => {
            const opt = document.createElement('div');
            opt.className = 'cs-opt';
            opt.dataset.value = cat.name_lower;
            opt.innerHTML = '<span class="cs-opt-icon"><i class="fa-solid fa-car"></i></span>' + cat.name;
            carTypeMenu.appendChild(opt);
        });
    }

    /**
     * Fill the fleet section category filter.
     *
     * @param {Object[]} categories
     * @param {boolean} hasVehicles
     */
    _populateFleetFilters(categories, hasVehicles) {
        const fleetFilter = this.el.querySelector('#fleetFilter');
        if (!fleetFilter) return;
        fleetFilter.innerHTML = '<button class="filter-btn active" data-filter="all">All</button>';
        if (!hasVehicles) {
            fleetFilter.style.display = 'none';
            return;
        }
        addCategoryFilterButtons(fleetFilter, categories);
    }

    /**
     * Fill the fleet section with the featured vehicles.
     *
     * @param {Object[]} vehicles
     * @param {boolean} hasVehicles
     */
    _populateVehicleCards(vehicles, hasVehicles) {
        const fleetGrid = this.el.querySelector('#fleetGrid');
        if (!fleetGrid) return;
        if (!hasVehicles || !vehicles.length) {
            showFleetUnavailable(fleetGrid);
            return;
        }
        fleetGrid.innerHTML = '';
        vehicles.forEach(v => fleetGrid.appendChild(renderVehicleCard(v)));
    }

    /** Show the empty states when the data could not be loaded. */
    _showUnavailableStates() {
        this._populateCarTypes([], false);
        this._populateFleetFilters([], false);
        const fleetGrid = this.el.querySelector('#fleetGrid');
        if (fleetGrid) showFleetUnavailable(fleetGrid);
    }
}

/**
 * Fleet Section snippet dropped on any page.
 *
 * Uses /homepage/data so vehicle data is always live, never baked into the
 * saved page arch.
 */
export class ThemeDriveXFleetSnippet extends Interaction {
    static selector = "#snippetFleetGrid";

    start() {
        const grid = this.el;
        const section = grid.closest('section') || grid.parentElement;
        const filter = section.querySelector('#snippetFleetFilter');

        // Avoid double-init if the interaction starts twice on the same element
        if (grid.dataset.dxSnippetLoaded) return;
        grid.dataset.dxSnippetLoaded = '1';
        if (filter) addCategoryFilterButtons(filter, []);

        this.waitFor(rpc('/homepage/data'))
            .then(result => {
                if (result) {
                    this._buildFilters(filter, result.categories || [], result.has_vehicles);
                    this._buildCards(grid, result.vehicles || [], result.has_vehicles);
                } else {
                    this._buildFilters(filter, [], false);
                    showFleetUnavailable(grid);
                }
            })
            .catch(() => {
                this._buildFilters(filter, [], false);
                showFleetUnavailable(grid);
            });
    }

    /**
     * Rebuild the category filter buttons, keeping the "All" one.
     *
     * @param {HTMLElement|null} filter
     * @param {Object[]} categories
     * @param {boolean} hasVehicles
     */
    _buildFilters(filter, categories, hasVehicles) {
        if (!filter) return;
        if (!hasVehicles) {
            filter.style.display = 'none';
            return;
        }
        filter.querySelectorAll('.filter-btn:not([data-filter="all"])').forEach(btn => btn.remove());
        addCategoryFilterButtons(filter, categories);
    }

    /**
     * Render the vehicle cards.
     *
     * @param {HTMLElement} grid
     * @param {Object[]} vehicles
     * @param {boolean} hasVehicles
     */
    _buildCards(grid, vehicles, hasVehicles) {
        if (!hasVehicles || !vehicles.length) {
            showFleetUnavailable(grid);
            return;
        }
        grid.innerHTML = '';
        vehicles.forEach(v => grid.appendChild(renderVehicleCard(v)));
    }
}

const interactions = registry.category("public.interactions");
interactions.add("theme_drivex.custom_select", ThemeDriveXCustomSelect);
interactions.add("theme_drivex.date_picker", ThemeDriveXDatePicker);
interactions.add("theme_drivex.date_picker_simple", ThemeDriveXDatePickerSimple);
interactions.add("theme_drivex.fleet_filter", ThemeDriveXFleetFilter);
interactions.add("theme_drivex.fleet_page", ThemeDriveXFleetPage);
interactions.add("theme_drivex.homepage_search", ThemeDriveXHomepageSearch);
interactions.add("theme_drivex.faq_accordion", ThemeDriveXFaqAccordion);
interactions.add("theme_drivex.scroll_reveal", ThemeDriveXScrollReveal);
interactions.add("theme_drivex.booking_wizard", ThemeDriveXBookingWizard);
interactions.add("theme_drivex.car_detail", ThemeDriveXCarDetail);
interactions.add("theme_drivex.detail_booking", ThemeDriveXDetailBooking);
interactions.add("theme_drivex.detail_dates", ThemeDriveXDetailDates);
interactions.add("theme_drivex.booking_dates", ThemeDriveXBookingDates);
interactions.add("theme_drivex.homepage_loader", ThemeDriveXHomepageLoader);
interactions.add("theme_drivex.fleet_snippet", ThemeDriveXFleetSnippet);
