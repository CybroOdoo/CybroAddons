/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";

// ── Shared DatePicker Logic ─────────────────────────────────────────────
const MONTHS_LONG = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
const MONTHS_SHORT = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

class DatePicker {
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
    _render() { this._renderHeader(); this._renderGrid(); this._renderTime(); }
    _renderHeader() {
        const el = this.panel.querySelector(".dp-my");
        if (el) el.textContent = `${MONTHS_LONG[this.s.viewMonth]} ${this.s.viewYear}`;
    }
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
            const isToday = d === todayD && m === todayM && y === todayY;
            const isSelected = d === selDay && m === selMonth && y === selYear;
            const isBookedDay = !isPast && isBooked(d);
            const cls = [
                isToday ? "dp-day--today" : "",
                isSelected ? "dp-day--selected" : "",
                isPast ? "dp-day--past" : "",
                isBookedDay ? "dp-day--booked" : "",
            ].join(" ").trim();
            const btn = mk(d, cls, (isPast || isBookedDay) ? null : () => {
                this.s.selYear = y; this.s.selMonth = m; this.s.selDay = d; this._renderGrid();
            });
            if (isPast || isBookedDay) btn.disabled = true;
            grid.appendChild(btn);
        }
        const total = firstDow + daysInMon;
        const tail = total % 7 === 0 ? 0 : 7 - (total % 7);
        for (let i = 1; i <= tail; i++) grid.appendChild(mk(i, "dp-day--other"));
    }
    _renderTime() {
        const hh = this.panel.querySelector(".dp-hh");
        const mm = this.panel.querySelector(".dp-mm");
        if (hh) hh.textContent = String(this.s.hour).padStart(2, "0");
        if (mm) mm.textContent = String(this.s.minute).padStart(2, "0");
    }
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
    // Attach booked date ranges — call after construction
    setBookedRanges(ranges) {
        this.bookedRanges = ranges || [];
        this._renderGrid();
    }
    _open() {
        if (window._dpAll) window._dpAll.forEach(dp => { if (dp !== this) dp._close(); });
        const csOpen = this.field ? this.field.closest('body').querySelectorAll(".cs-wrap.open") : [];
        csOpen.forEach(s => s.classList.remove("open"));
        if (this.panel.parentElement !== document.body) document.body.appendChild(this.panel);
        this._positionPanel();
        this.s.open = true;
        this.panel.classList.add("dp-open");
        // A fixed panel should not remain visible while its trigger scrolls
        // away. Capturing catches scrolls from Odoo's inner page containers.
        this._closeOnScroll = () => this._close();
        window.addEventListener("scroll", this._closeOnScroll, { passive: true });
        document.addEventListener("scroll", this._closeOnScroll, true);
    }
    _positionPanel() {
        const rect = this.field.getBoundingClientRect();
        const panelW = 300, vw = window.innerWidth;
        const isMobile = window.matchMedia("(max-width: 768px)").matches;
        let top = isMobile ? 104 : rect.bottom + 8;
        let left = rect.left;
        if (left + panelW > vw - 12) left = rect.right - panelW;
        this.panel.style.cssText = `position:fixed;top:${top}px;left:${left}px;width:300px;z-index:999999;margin:0;`;
    }
    _close() {
        this.s.open = false;
        this.panel.classList.remove("dp-open");
        if (this._closeOnScroll) {
            window.removeEventListener("scroll", this._closeOnScroll);
            document.removeEventListener("scroll", this._closeOnScroll, true);
            this._closeOnScroll = null;
        }
        if (this.panel.parentElement === document.body && this.field) {
            this.field.appendChild(this.panel);
            this.panel.style.cssText = "";
        }
    }
}

// ── Global Helper ──────────────────────────────────────────────────
function capitalize(str) {
    if (!str) return "";
    return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
}

// ── Global Helper: show a styled Odoo AlertDialog instead of native alert() ──
function showAlert(dialogService, message, title) {
    if (dialogService && dialogService.add) {
        dialogService.add(AlertDialog, {
            body: message,
            title: title || _t("Notice"),
            confirmLabel: _t("Close"),
        });
    } else {
        // Fallback in case the dialog service isn't available for some reason
        window.alert(message);
    }
}

// ── Widget: Header & Mobile Menu ─────────────────────────────────────
publicWidget.registry.ThemeDriveXHeader = publicWidget.Widget.extend({
    selector: "#header",
    events: {
        'click #hamburger': '_onHamburgerClick',
    },
    start() {
        this.menu = this.el.querySelector("#menu");
        this.hamburger = this.el.querySelector("#hamburger");

        // Document click for closing menu
        document.addEventListener("click", (e) => {
            if (this.menu && this.menu.classList.contains("open") && !this.el.contains(e.target)) {
                this.hamburger.classList.remove("open");
                this.menu.classList.remove("open");
                document.body.classList.remove("menu-open");
            }
            // Close the "more" overflow dropdown on outside click too.
            if (this._moreBtn && this._moreBtn.classList.contains("open")
                && !this._moreBtn.contains(e.target)
                && !(this._moreDropdown && this._moreDropdown.contains(e.target))) {
                this._moreBtn.classList.remove("open");
                this._moreBtn.querySelector(".menu-more-toggle").setAttribute("aria-expanded", "false");
                if (this._moreDropdown) {
                    this._moreDropdown.classList.remove("open");
                }
            }
        });

        this._initMenuOverflow();

        return this._super.apply(this, arguments);
    },
    _onHamburgerClick(e) {
        if (!this.hamburger || !this.menu) return;
        // Always restore collapsed items before opening — handles the case
        // where the page was loaded at desktop width (items moved to + dropdown)
        // but is now being viewed in a narrowed/mobile viewport.
        if (this._moreBtn) {
            [...this._moreDropdown.children].forEach((li) => {
                this.menu.insertBefore(li, this._moreBtn);
            });
            this._moreBtn.remove();
            this._moreDropdown.remove();
            this._moreBtn = null;
            this._moreDropdown = null;
        }
        this.menu.classList.remove("menu-loading");
        this.hamburger.classList.toggle("open");
        this.menu.classList.toggle("open");
        document.body.classList.toggle("menu-open");
    },

    /**
     * Mirrors Odoo's core "auto-hide menu" behaviour (see
     * website/static/src/js/content/auto_hide_menu.js): on desktop widths,
     * Collapses menu items into a "+" dropdown based on a simple item count
     * rather than measured pixel widths: if there are more than
     * MAX_VISIBLE_ITEMS top-level menu items, everything after that count is
     * moved into the dropdown. Below the mobile breakpoint the existing
     * hamburger already shows the full menu, so this is skipped there.
     */
    _initMenuOverflow() {
        const menu = this.menu;
        if (!menu) {
            return;
        }

        const MOBILE_BREAKPOINT = 900; // keep in sync with theme.scss
        const MAX_VISIBLE_ITEMS = 5;   // show the first 5 menu items, collapse the rest
        this._moreBtn = null;      // <li class="menu-more"> toggle, lives inside .menu
        this._moreDropdown = null; // <ul class="menu-more-dropdown">, lives outside .menu

        const restore = () => {
            if (!this._moreBtn) {
                return;
            }
            [...this._moreDropdown.children].forEach((li) => {
                menu.insertBefore(li, this._moreBtn);
            });
            this._moreBtn.remove();
            this._moreDropdown.remove();
            this._moreBtn = null;
            this._moreDropdown = null;
        };

        const positionDropdown = () => {
            // Positioned relative to the header (JS-computed) rather than
            // nested inside .menu, so it can't get clipped by anything.
            const headerRect = this.el.getBoundingClientRect();
            const toggleRect = this._moreBtn.getBoundingClientRect();
            this._moreDropdown.style.top = `${toggleRect.bottom - headerRect.top + 12}px`;
            this._moreDropdown.style.right = `${headerRect.right - toggleRect.right}px`;
        };

        const buildMoreButton = () => {
            const li = document.createElement("li");
            li.className = "menu-more";
            li.innerHTML =
                '<a href="#" class="menu-more-toggle" aria-haspopup="true" aria-expanded="false">' +
                '<i class="fa-solid fa-plus"></i></a>';
            menu.appendChild(li);

            const dropdown = document.createElement("ul");
            dropdown.className = "menu-more-dropdown";
            this.el.appendChild(dropdown); // outside .menu on purpose, see restore()/positionDropdown()

            const toggle = li.querySelector(".menu-more-toggle");
            toggle.addEventListener("click", (e) => {
                e.preventDefault();
                const isOpen = li.classList.toggle("open");
                toggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
                dropdown.classList.toggle("open", isOpen);
                if (isOpen) {
                    positionDropdown();
                }
            });

            this._moreBtn = li;
            this._moreDropdown = dropdown;
        };

        const adapt = () => {
            // Below the mobile breakpoint, the hamburger owns the full menu.
            if (window.matchMedia(`(max-width: ${MOBILE_BREAKPOINT}px)`).matches) {
                restore();
                requestAnimationFrame(() => menu.classList.remove("menu-loading"));
                return;
            }

            restore();

            // Only the real page/menu links count toward the limit — not a
            // "+" button from a previous run (already removed by restore()).
            const items = [...menu.children];
            if (items.length <= MAX_VISIBLE_ITEMS) {
                requestAnimationFrame(() => menu.classList.remove("menu-loading"));
                return; // fits within the limit, nothing to collapse
            }

            buildMoreButton();

            const overflowItems = items.slice(MAX_VISIBLE_ITEMS);
            overflowItems.forEach((li) => this._moreDropdown.appendChild(li));
            // Remove loading class in next frame — after DOM mutations are done
            requestAnimationFrame(() => menu.classList.remove("menu-loading"));
        };

        window.addEventListener("resize", () => {
            // Item count doesn't change with width, but we still need to
            // switch between "hamburger owns it" and "+ owns it" as the
            // viewport crosses the mobile breakpoint.
            adapt();
        });

        adapt();
    },
});

// ── Widget: Custom Selects ───────────────────────────────────────────
publicWidget.registry.ThemeDriveXCustomSelect = publicWidget.Widget.extend({
    selector: ".cs-wrap",
    events: {
        'click .cs-trigger': '_onTriggerClick',
        'click .cs-opt': '_onOptionClick',
    },
    start() {
        document.addEventListener("click", () => {
            this.el.classList.remove("open");
        });
        return this._super.apply(this, arguments);
    },
    _onTriggerClick(e) {
        e.stopPropagation();
        const isOpen = this.el.classList.contains("open");
        this.el.closest('body').querySelectorAll(".cs-wrap.open").forEach(s => s.classList.remove("open"));
        if (!isOpen) this.el.classList.add("open");
    },
    _onOptionClick(e) {
        const opt = e.currentTarget;
        const valEl = this.el.querySelector(".cs-val");
        if (valEl) valEl.textContent = opt.textContent.trim();
        this.el.querySelectorAll(".cs-opt").forEach(o => o.classList.remove("cs-opt--active"));
        opt.classList.add("cs-opt--active");
        this.el.classList.remove("open");
    }
});

// ── Widget: DatePickers ──────────────────────────────────────────────
publicWidget.registry.ThemeDriveXDatePicker = publicWidget.Widget.extend({
    selector: ".date-field",
    start() {
        window._dpAll = window._dpAll || [];
        const display = this.el.querySelector(".date-display");
        const panel = this.el.querySelector(".dp-panel");
        if (display && panel) {
            this.dp = new DatePicker(this.el, display, panel);
            this.el._dpInstance = this.dp;
            window._dpAll.push(this.dp);
        }
        return this._super.apply(this, arguments);
    }
});
// Close a picker only when the click is outside both its trigger and panel.
document.addEventListener("click", event => {
    if (!window._dpAll) return;
    window._dpAll.forEach(dp => {
        if (dp.s.open && !dp.field.contains(event.target) &&
            !dp.panel.contains(event.target)) {
            dp._close();
        }
    });
});

// ── Widget: Fleet Filter (Homepage + Snippet) ────────────────────────
// Covers both:
//   • home_templates.xml  – "All" button is server-rendered; all other
//     filter buttons and car cards are injected by _buildFilterButtons /
//     _buildVehicleCards *after* page load.
//   • drivex_fleet_section snippet – all buttons and cards are server-
//     rendered by Qweb t-foreach, present in the DOM from the start.
//
// Using the section as the selector + delegated 'click .filter-btn'
// means the handler fires for every button regardless of when it was
// added to the DOM.  disabledInEditableMode:false lets the filter also
// work in Website Builder preview mode.
publicWidget.registry.ThemeDriveXFleetFilter = publicWidget.Widget.extend({
    selector: ".fleet-section",
    disabledInEditableMode: false,
    events: {
        'click .filter-btn': '_onClick',
    },
    _onClick(e) {
        const btn = e.currentTarget;
        // De-activate all sibling buttons inside this section
        this.el.querySelectorAll(".filter-btn").forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        const filter = (btn.dataset.filter || btn.dataset.cat || "all").toLowerCase();
        // Show / hide car cards – handles both single-value ("sports") and
        // space-separated multi-value ("luxury sports") data-category attrs.
        this.el.querySelectorAll(".car-card").forEach(card => {
            const cat = (card.dataset.cat || card.dataset.category || "").toLowerCase();
            card.style.display = (filter === "all" || cat.split(" ").some(c => c === filter)) ? "" : "none";
        });
    }
});

// ── Widget: Fleet Page ───────────────────────────────────────────────
publicWidget.registry.ThemeDriveXFleetPage = publicWidget.Widget.extend({
    selector: ".fleet-page", // Cover both filter bar and grid

    events: {
        'click .fb-cat': '_onCatFilter',
        'input .fb-search input': '_onSearch',
        'click .fv-btn': '_onViewToggle',
        'change .fb-sort': '_onSortChange',
    },
    start() {
        const filterBar = this.el.querySelector(".filter-bar-wrap") || this.el.closest('body').querySelector(".filter-bar-wrap");
        if (filterBar) {
            window.addEventListener("scroll", () => {
                filterBar.classList.toggle("fb-sticky", window.scrollY > 100);
            }, { passive: true });
        }
        // Store original index for default sorting
        this.el.querySelectorAll('.fc-card').forEach((card, index) => {
            card.dataset.index = index;
        });
        // Update counts from real rendered cards
        this._updateCount();
        // Update hero stats from rendered data
        this._updateHeroStats();
        return this._super.apply(this, arguments);
    },
    _updateCount() {
        const cnt = document.getElementById('resultsCount');
        if (!cnt) return;
        const visible = Array.from(this.el.querySelectorAll('.fc-card'))
            .filter(c => c.style.display !== 'none').length;
        cnt.innerHTML = `Showing <strong>${visible}</strong> vehicle${visible !== 1 ? 's' : ''}`;
    },
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
        const heroCount = document.getElementById('heroVehicleCount');
        const heroCats = document.getElementById('heroCategoryCount');
        if (heroCount) heroCount.textContent = total > 0 ? total + '+' : total;
        if (heroCats) heroCats.textContent = catSet.size;
    },
    _onCatFilter(e) {
        const btn = e.currentTarget;
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
        const cnt = document.getElementById('resultsCount');
        if (cnt) cnt.innerHTML = `Showing <strong>${visible}</strong> vehicles`;
        const noRes = this.el.querySelector("#noResults");
        if (noRes) noRes.style.display = visible === 0 ? "" : "none";
    },
    _onSearch(e) {
        const q = e.currentTarget.value.toLowerCase();
        const cards = this.el.querySelectorAll(".fc-card");
        cards.forEach(card => {
            const name = (card.querySelector("h3") || card).textContent.toLowerCase();
            card.style.display = name.includes(q) ? "" : "none";
        });
    },
    _onViewToggle(e) {
        const btn = e.currentTarget;
        this.el.querySelectorAll(".fv-btn").forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        const grid = this.el.classList.contains("fc-grid") ? this.el : this.el.querySelector(".fc-grid");
        if (grid) grid.classList.toggle("fc-list-mode", btn.dataset.view === "list");
    },
    _onSortChange(e) {
        const val = e.currentTarget.value;
        const grid = this.el.querySelector('.fc-grid');
        if (!grid) return;

        const cards = Array.from(grid.querySelectorAll('.fc-card'));

        cards.sort((a, b) => {
            if (val === 'price-asc') {
                return parseFloat(a.dataset.price || 0) - parseFloat(b.dataset.price || 0);
            } else if (val === 'price-desc') {
                return parseFloat(b.dataset.price || 0) - parseFloat(a.dataset.price || 0);
            } else if (val === 'rating') {
                return parseFloat(b.dataset.rating || 0) - parseFloat(a.dataset.rating || 0);
            } else if (val === 'newest') {
                return parseInt(b.dataset.year || 0) - parseInt(a.dataset.year || 0);
            }
            // default
            return parseInt(a.dataset.index || 0) - parseInt(b.dataset.index || 0);
        });

        cards.forEach(card => grid.appendChild(card));
    },
});

// ── Widget: Homepage Dynamic Content Loader ───────────────────────────────────
// Populates homepage-specific IDs: #locationMenu, #carTypeMenu, #fleetFilter,
// #fleetGrid. Separate from the snippet widget so the homepage and the snippet
// can coexist without interfering with each other.
publicWidget.registry.ThemeDriveXHomepageLoader = publicWidget.Widget.extend({
    selector: '#wrap',
    start() {
        // Only load on homepage (check if we have the hero section)
        if (!this.el.querySelector('.hero')) {
            return this._super.apply(this, arguments);
        }
        // Fetch homepage data from controller
        fetch('/homepage/data', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ jsonrpc: '2.0', method: 'call', params: {} }),
        })
        .then(r => r.json())
        .then(resp => {
            const data = resp.result || {};
            this._populateLocations(data.locations || []);
            this._populateCarTypes(data.categories || [], data.has_vehicles);
            this._populateFleetFilters(data.categories || [], data.has_vehicles);
            this._populateVehicleCards(data.vehicles || [], data.has_vehicles);
        })
        .catch(e => {
            console.warn('[DriveX] homepage/data fetch failed:', e);
            this._showUnavailableStates();
        });
        return this._super.apply(this, arguments);
    },

    _populateLocations(locations) {
        const locationMenu = document.getElementById('locationMenu');
        if (!locationMenu) return;
        locationMenu.innerHTML = '';
        if (!locations.length) return;
        locations.forEach(loc => {
            const opt = document.createElement('div');
            opt.className = 'cs-opt';
            opt.dataset.value = loc.id;
            opt.innerHTML = '<span class="cs-opt-icon"><i class="fa-solid fa-building"></i></span>' + loc.name;
            locationMenu.appendChild(opt);
        });
    },

    _populateCarTypes(categories, hasVehicles) {
        const carTypeMenu = document.getElementById('carTypeMenu');
        if (!carTypeMenu) return;
        // Keep "All Vehicles" — remove any previously injected
        carTypeMenu.querySelectorAll('.cs-opt[data-dynamic]').forEach(el => el.remove());
        if (!hasVehicles || !categories.length) return;
        categories.forEach(cat => {
            const opt = document.createElement('div');
            opt.className = 'cs-opt';
            opt.dataset.value = cat.name_lower;
            opt.dataset.dynamic = '1';
            opt.innerHTML = '<span class="cs-opt-icon"><i class="fa-solid fa-car"></i></span>' + cat.name;
            carTypeMenu.appendChild(opt);
        });
    },

    _populateFleetFilters(categories, hasVehicles) {
        const fleetFilter = document.getElementById('fleetFilter');
        if (!fleetFilter) return;
        // Remove previously injected buttons (keep "All")
        fleetFilter.querySelectorAll('.filter-btn[data-dynamic]').forEach(el => el.remove());
        if (!hasVehicles) {
            fleetFilter.style.display = 'none';
            return;
        }
        // Force flex centering in case Website Builder CSS overrides SCSS
        fleetFilter.style.display = 'flex';
        fleetFilter.style.justifyContent = 'center';
        fleetFilter.style.alignItems = 'center';
        fleetFilter.style.flexWrap = 'wrap';
        if (categories.length) {
            categories.forEach(cat => {
                const btn = document.createElement('button');
                btn.className = 'filter-btn';
                btn.dataset.filter = cat.name_lower;
                btn.dataset.dynamic = '1';
                btn.textContent = cat.name;
                fleetFilter.appendChild(btn);
            });
        }
    },

    _populateVehicleCards(vehicles, hasVehicles) {
        const fleetGrid = document.getElementById('fleetGrid');
        if (!fleetGrid) return;
        fleetGrid.innerHTML = '';
        if (!hasVehicles || !vehicles.length) {
            this._showFleetUnavailable(fleetGrid);
            return;
        }
        vehicles.forEach(v => {
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
                    '<p class="car-type">' +
                        '<i class="fa-solid fa-tag"></i> ' + (v.category || '') + ' · ' + v.horsepower + ' HP' +
                    '</p>' +
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
            fleetGrid.appendChild(card);
        });
    },

    _showFleetUnavailable(fleetGrid) {
        const msg = document.createElement('div');
        msg.style.cssText = 'text-align:center;padding:60px 20px;width:100%;';
        msg.innerHTML =
            '<i class="fa-solid fa-car" style="font-size:2.8rem;color:#ccc;margin-bottom:16px;display:block;"></i>' +
            '<h3 style="font-size:1.4rem;font-weight:700;color:#222;margin-bottom:10px;">No Vehicles Available</h3>' +
            '<p style="font-size:0.95rem;color:#666;max-width:420px;margin:0 auto;">' +
                'No vehicles have been published yet. Configure and publish vehicles from the Fleet module in the backend.' +
            '</p>';
        fleetGrid.appendChild(msg);
    },

    _showUnavailableStates() {
        this._populateCarTypes([], false);
        this._populateFleetFilters([], false);
        const fleetGrid = document.getElementById('fleetGrid');
        if (fleetGrid) {
            this._showFleetUnavailable(fleetGrid);
        }
    }
});

// ── Widget: Fleet Section Snippet Loader ──────────────────────────────────────
// Handles the drivex_fleet_section snippet when dropped on any page.
// Uses /homepage/data so vehicle data is always live, never baked into the
// saved page arch. Re-initialisation safe: clears containers before rebuild.
publicWidget.registry.ThemeDriveXFleetSnippet = publicWidget.Widget.extend({
    selector: '#snippetFleetGrid',
    start() {
        const grid = this.el;                                    // #snippetFleetGrid
        const filter = document.getElementById('snippetFleetFilter');
        // Guard: avoid double-init if widget fires twice on the same element
        if (grid.dataset.dxSnippetLoaded) {
            return this._super.apply(this, arguments);
        }
        grid.dataset.dxSnippetLoaded = '1';
        // Force flex centering on the filter bar — Website Builder can override SCSS
        if (filter) {
            filter.style.display = 'flex';
            filter.style.justifyContent = 'center';
            filter.style.alignItems = 'center';
            filter.style.flexWrap = 'wrap';
        }
        fetch('/homepage/data', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ jsonrpc: '2.0', method: 'call', params: {} }),
        })
        .then(r => r.json())
        .then(resp => {
            const data = resp.result || {};
            this._buildFilters(filter, data.categories || [], data.has_vehicles);
            this._buildCards(grid, data.vehicles || [], data.has_vehicles);
        })
        .catch(() => {
            this._buildFilters(filter, [], false);
            this._showUnavailable(grid);
        });
        return this._super.apply(this, arguments);
    },

    _buildFilters(filter, categories, hasVehicles) {
        if (!filter) return;
        if (!hasVehicles) {
            filter.style.display = 'none';
            return;
        }
        // Force flex centering
        filter.style.display = 'flex';
        filter.style.justifyContent = 'center';
        filter.style.alignItems = 'center';
        filter.style.flexWrap = 'wrap';
        // Remove previously injected category buttons (safe re-init)
        filter.querySelectorAll('.filter-btn:not([data-filter="all"])').forEach(btn => btn.remove());
        if (categories.length) {
            categories.forEach(cat => {
                const btn = document.createElement('button');
                btn.className = 'filter-btn';
                btn.dataset.filter = cat.name_lower;
                btn.textContent = cat.name;
                filter.appendChild(btn);
            });
        }
    },

    _buildCards(grid, vehicles, hasVehicles) {
        grid.innerHTML = '';
        if (!hasVehicles || !vehicles.length) {
            this._showUnavailable(grid);
            return;
        }
        vehicles.forEach(v => {
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
            grid.appendChild(card);
        });
    },

    _showUnavailable(grid) {
        grid.innerHTML =
            '<div style="text-align:center;padding:60px 20px;width:100%;">' +
                '<i class="fa-solid fa-car" style="font-size:2.8rem;color:#ccc;margin-bottom:16px;display:block;"></i>' +
                '<h3 style="font-size:1.4rem;font-weight:700;color:#222;margin-bottom:10px;">No Vehicles Available</h3>' +
                '<p style="font-size:0.95rem;color:#666;max-width:420px;margin:0 auto;">' +
                    'No vehicles have been published yet. Configure and publish vehicles from the Fleet module in the backend.' +
                '</p>' +
            '</div>';
    },
});

// ── Widget: Homepage Search ──────────────────────────────────────────
publicWidget.registry.ThemeDriveXHomepageSearch = publicWidget.Widget.extend({
    selector: ".search-btn",
    events: {
        'click': '_onSearchClick',
    },
    /**
     * @override
     */
    init() {
        this._super(...arguments);
        this.dialog = this.bindService("dialog");
    },
    _onSearchClick(e) {
        const container = this.el.closest(".search-box, section") || document;
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
        const pYear = pDp.s.selYear;
        const pMonth = formatNum(pDp.s.selMonth + 1);
        const pDay = formatNum(pDp.s.selDay);
        const pHour = pDp.s.hour;
        const pMin = pDp.s.minute;
        const rYear = rDp.s.selYear;
        const rMonth = formatNum(rDp.s.selMonth + 1);
        const rDay = formatNum(rDp.s.selDay);
        const rHour = rDp.s.hour;
        const rMin = rDp.s.minute;
        const pDateStr = `${pYear}-${pMonth}-${pDay}`;
        const rDateStr = `${rYear}-${rMonth}-${rDay}`;
        const pTimeStr = `${formatNum(pHour > 12 ? pHour - 12 : (pHour === 0 ? 12 : pHour))}:${formatNum(pMin)} ${pHour >= 12 ? 'PM' : 'AM'}`;
        const rTimeStr = `${formatNum(rHour > 12 ? rHour - 12 : (rHour === 0 ? 12 : rHour))}:${formatNum(rMin)} ${rHour >= 12 ? 'PM' : 'AM'}`;
        const pDateObj = new Date(pYear, pDp.s.selMonth, pDp.s.selDay, pHour, pMin);
        const rDateObj = new Date(rYear, rDp.s.selMonth, rDp.s.selDay, rHour, rMin);
        if (rDateObj <= pDateObj) {
            showAlert(this.dialog, _t("Return Date & Time must be after the Pickup Date & Time."));
            return;
        }
        let url = `/fleet?pickup_date=${pDateStr}&pickup_time=${encodeURIComponent(pTimeStr)}&return_date=${rDateStr}&return_time=${encodeURIComponent(rTimeStr)}`;
        if (locVal) url += `&pickup_loc=${encodeURIComponent(locVal)}`;
        if (catVal && catVal !== 'all') url += `&category=${encodeURIComponent(catVal)}`;
        window.location.href = url;
    }
});

// ── Widget: FAQ Accordion ────────────────────────────────────────────
publicWidget.registry.ThemeDriveXFaqAccordion = publicWidget.Widget.extend({
    selector: ".faq-item",
    events: {
        'click .faq-question': '_onToggle',
    },
    _onToggle(e) {
        const isOpen = this.el.classList.contains("open");
        const container = this.el.closest(".faq-container, section") || document;
        container.querySelectorAll(".faq-item").forEach(i => i.classList.remove("open"));
        if (!isOpen) this.el.classList.add("open");
    }
});

// ── Widget: Scroll Reveal ────────────────────────────────────────────
publicWidget.registry.ThemeDriveXScrollReveal = publicWidget.Widget.extend({
    selector: ".car-card, .fc-card, .feature, .step, .review, .stat, .service-card, .value-card, .team-card, .pricing-card, .contact-info-card",
    start() {
        if (typeof IntersectionObserver !== "undefined") {
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
        }
        return this._super.apply(this, arguments);
    }
});

// ── Widget: Booking Wizard ───────────────────────────────────────────
publicWidget.registry.ThemeDriveXBookingWizard = publicWidget.Widget.extend({
    selector: "#wrap",
    events: {
        'click .bw-btn-next-action': '_onNextStep',
        'click .bw-btn-back-action': '_onPrevStep',
        'click .bw-ins-card': '_onSelectInsurance',
        'click .bw-addon': '_onToggleAddon',
        'click .bw-btn-confirm-action': '_onConfirmBooking',
        'click .bw-btn-copy-ref': '_onCopyRef',
        'input .bw-card-number-input': '_formatCardNumber',
        'input .bw-expiry-input': '_formatExpiry',
        // Listen to both date fields AND time selects so any change
        // immediately recalculates duration and all dependent pricing.
        'change .tripPickup': '_updatePricing',
        'change .tripReturn': '_updatePricing',
        'change .tripPickupTime': '_updatePricing',
        'change .tripReturnTime': '_updatePricing',
    },
    /**
     * @override
     */
    init() {
        this._super(...arguments);
        this.dialog = this.bindService("dialog");
    },
    start() {
        // Pre-fill from URL params
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

        // Pre-select pickup location
        if (pLoc) {
            const locSel = this.el.querySelector('.tripPickupLoc');
            if (locSel) {
                for (let i = 0; i < locSel.options.length; i++) {
                    const opt = locSel.options[i];
                    if (String(opt.value) === String(pLoc) ||
                        opt.text.toLowerCase().trim() === pLoc.toLowerCase().trim()) {
                        locSel.selectedIndex = i;
                        break;
                    }
                }
            }
        }

        // Pre-select insurance card matching insurance_id from URL
        if (insId) {
            const allCards = this.el.querySelectorAll('.bw-ins-card');
            allCards.forEach(card => {
                card.classList.remove('selected');
                card.style.border = '2px solid rgba(255,255,255,.08)';
                card.style.background = 'transparent';
            });
            const matchCard = this.el.querySelector(`.bw-ins-card[data-id="${insId}"]`);
            if (matchCard) {
                matchCard.classList.add('selected');
                matchCard.style.border = '2px solid var(--accent)';
                matchCard.style.background = 'rgba(212,25,28,.06)';
            }
        }
        setTimeout(() => this._updatePricing(), 200);
        return this._super.apply(this, arguments);
    },

    _setVal(sel, val) {
        const el = this.el.querySelector(sel);
        if (el) el.value = val;
    },
    _onNextStep(e) {
        const current = parseInt(e.currentTarget.dataset.nextStep);
        const curr = this.el.querySelector(".step" + current);
        if (curr) {
            const inputs = curr.querySelectorAll("input[required], select[required], textarea[required]");
            for (let input of inputs) {
                if (!input.value || input.value.trim() === "") {
                    showAlert(this.dialog, _t("Please fill in all required fields before continuing."));
                    input.focus();
                    return;
                }
            }
        }

        // ── Step 1: validate selected dates don't overlap any booked range ──
        if (current === 1) {
            const pickupInput = this.el.querySelector(".tripPickup");
            const returnInput = this.el.querySelector(".tripReturn");
            const pickupTimeInput = this.el.querySelector(".tripPickupTime");
            const returnTimeInput = this.el.querySelector(".tripReturnTime");

            if (pickupInput && returnInput && pickupInput.value && returnInput.value) {
                const parseDate = (dateStr, timeStr) => {
                    if (!dateStr) return null;
                    const [y, m, d] = dateStr.split('-').map(Number);
                    let h = 12, min = 0;
                    if (timeStr) {
                        const tm = timeStr.trim().match(/^(\d{1,2}):(\d{2})\s*(AM|PM)$/i);
                        if (tm) {
                            h = parseInt(tm[1]);
                            min = parseInt(tm[2]);
                            const ampm = tm[3].toUpperCase();
                            if (ampm === 'AM' && h === 12) h = 0;
                            else if (ampm === 'PM' && h !== 12) h += 12;
                        }
                    }
                    return new Date(y, m - 1, d, h, min, 0, 0);
                };

                const pickupDt = parseDate(pickupInput.value, pickupTimeInput ? pickupTimeInput.value : '12:00 PM');
                const returnDt = parseDate(returnInput.value, returnTimeInput ? returnTimeInput.value : '12:00 PM');

                if (returnDt && pickupDt && returnDt <= pickupDt) {
                    showAlert(this.dialog, _t("Return Date & Time must be after the Pickup Date & Time."));
                    return;
                }

                // Get booked ranges — read from picker instance (most reliable)
                // or fall back to grid element store
                const bwDateGrid = document.getElementById('bwDateGrid');
                let bookedRanges = [];
                if (bwDateGrid) {
                    // Try reading from the picker instance first
                    const pickupField = bwDateGrid.querySelector('.tripPickupField');
                    const dp = pickupField && pickupField._dpInstance;
                    if (dp && dp.bookedRanges && dp.bookedRanges.length) {
                        bookedRanges = dp.bookedRanges;
                    } else if (bwDateGrid._bookedRanges && bwDateGrid._bookedRanges.length) {
                        bookedRanges = bwDateGrid._bookedRanges;
                    }
                }

                if (pickupDt && returnDt && bookedRanges.length) {
                    const selStart = pickupDt.getTime();
                    const selEnd = returnDt.getTime();
                    const conflict = bookedRanges.some(r => {
                        const bookedStart = new Date(r.from + 'T00:00:00').getTime();
                        const bookedEnd = new Date(r.to + 'T23:59:59').getTime();
                        return selStart < bookedEnd && selEnd > bookedStart;
                    });
                    if (conflict) {
                        showAlert(
                            this.dialog,
                            _t("This vehicle is not available for the selected dates. Please choose different dates."),
                            _t("Vehicle Not Available")
                        );
                        return;
                    }
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
        window.scrollTo({ top: 0, behavior: "smooth" });
    },
    _onPrevStep(e) {
        const current = parseInt(e.currentTarget.dataset.prevStep);
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
        window.scrollTo({ top: 0, behavior: "smooth" });
    },
    _onSelectInsurance(e) {
        const el = e.currentTarget;
        this.el.querySelectorAll(".bw-ins-card").forEach(c => {
            c.classList.remove("selected");
            c.style.border = "2px solid rgba(255,255,255,.08)";
            c.style.background = "transparent";
        });
        el.classList.add("selected");
        el.style.border = "2px solid var(--accent)";
        el.style.background = "rgba(212,25,28,.06)";
        this._updatePricing();
    },
    _onToggleAddon(e) {
        const el = e.currentTarget;
        const selected = el.classList.toggle("selected");
        el.style.border = selected ? "1px solid var(--accent)" : "1px solid rgba(255,255,255,.08)";
        el.style.background = selected ? "rgba(212,25,28,.06)" : "transparent";
        this._updatePricing();
    },
    /**
     * Recalculate booking duration and all pricing components.
     *
     * Duration logic mirrors the backend exactly:
     *   delta_seconds = (return_datetime - pickup_datetime).total_seconds()
     *   days = max(1, delta.days + (1 if delta.seconds > 0 else 0))
     *
     * Both the date (YYYY-MM-DD from the hidden inputs set by the custom
     * DatePicker) and the time (HH:MM AM/PM from the <select> dropdowns)
     * are combined before computing the difference, so changing either
     * field will always produce the same result as the backend.
     */
    _updatePricing() {
        const sumDays    = this.el.querySelector(".sumDays");
        const sumIns     = this.el.querySelector(".sumInsurance");
        const sumAddons  = this.el.querySelector(".sumAddons");
        const sumTotal   = this.el.querySelector(".sumTotal");
        const baseRateSpan = this.el.querySelector(".sumBaseRate");

        if (!sumTotal || !baseRateSpan) return;

        const dailyRate = parseFloat(
            (baseRateSpan.textContent || "0").replace(/[^0-9.]/g, "")
        );

        // ── Build full datetimes from date + time fields ──────────────────
        const pickupDateInput  = this.el.querySelector(".tripPickup");
        const returnDateInput  = this.el.querySelector(".tripReturn");
        const pickupTimeSelect = this.el.querySelector(".tripPickupTime");
        const returnTimeSelect = this.el.querySelector(".tripReturnTime");

        let days = 1;

        const pickupDate = pickupDateInput ? pickupDateInput.value.trim() : "";
        const returnDate = returnDateInput ? returnDateInput.value.trim() : "";

        if (pickupDate && returnDate) {
            // Default to 12:00 PM when the time select has no value yet,
            // matching the backend's default of '12:00 PM'.
            const pickupTimeStr = (pickupTimeSelect && pickupTimeSelect.value)
                ? pickupTimeSelect.value.trim()
                : "12:00 PM";
            const returnTimeStr = (returnTimeSelect && returnTimeSelect.value)
                ? returnTimeSelect.value.trim()
                : "12:00 PM";

            const pickupDt = _parseDateTimeLocal(pickupDate, pickupTimeStr);
            const returnDt = _parseDateTimeLocal(returnDate, returnTimeStr);

            if (pickupDt && returnDt && returnDt > pickupDt) {
                // Mirror Python: delta.days + (1 if delta.seconds > 0 else 0)
                const totalSeconds = (returnDt - pickupDt) / 1000;
                const deltaDays    = Math.floor(totalSeconds / 86400);
                const extraSeconds = totalSeconds % 86400;
                days = Math.max(1, deltaDays + (extraSeconds > 0 ? 1 : 0));
            }
        }

        if (sumDays) sumDays.textContent = `${days} day${days !== 1 ? "s" : ""}`;

        // ── Insurance ────────────────────────────────────────────────────
        const selIns = this.el.querySelector(".bw-ins-card.selected");
        const insDailyRate = (selIns && selIns.dataset.price)
            ? parseFloat(selIns.dataset.price)
            : 0;
        if (sumIns) {
            sumIns.textContent = insDailyRate > 0
                ? `+$${insDailyRate}/day`
                : "Included";
        }

        // ── Add-ons ───────────────────────────────────────────────────────
        let totalAddons = 0;
        this.el.querySelectorAll(".bw-addon.selected").forEach(add => {
            const p = parseFloat(add.dataset.price || 0);
            if (add.dataset.type === "per_day") totalAddons += p * days;
            else totalAddons += p;
        });
        if (sumAddons) sumAddons.textContent = `+$${totalAddons}`;

        // ── Grand total ───────────────────────────────────────────────────
        const total = (dailyRate * days) + (insDailyRate * days) + totalAddons;
        sumTotal.textContent = `$${total.toFixed(0)}`;
    },
    _onConfirmBooking(e) {
        const termsBox = this.el.querySelector(".termsCheck");
        if (termsBox && !termsBox.checked) {
            showAlert(this.dialog, _t("Please accept the terms and conditions."));
            return;
        }
        const btn = e.currentTarget;
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
            driver_dob: this.el.querySelector(".driverDob")?.value || '',
            driver_license: this.el.querySelector(".driverLicense")?.value || '',
            license_expiry_date: this.el.querySelector(".licenseExpiryDate")?.value || '',
            insurance_id: this.el.querySelector(".bw-ins-card.selected")?.dataset.id || null,
            addon_ids: Array.from(this.el.querySelectorAll(".bw-addon.selected")).map(el => el.dataset.id)
        };
        fetch('/booking/submit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ params: payload })
        })
            .then(res => res.json())
            .then(data => {
                if (data.result && data.result.success) {
                    const confirmEmail = this.el.querySelector(".confirmEmail");
                    const ref = this.el.querySelector(".bookingRef");
                    if (confirmEmail && payload.driver_email) confirmEmail.textContent = payload.driver_email;
                    if (ref) ref.textContent = data.result.order_name;
                    // Manually trigger nextStep(3)
                    const pseudoEvent = { currentTarget: { dataset: { nextStep: "3" } } };
                    this._onNextStep(pseudoEvent);
                } else {
                    showAlert(this.dialog, _t("Booking Error: ") + (data.result ? data.result.error : _t("Unknown error")));
                }
            })
            .catch(err => {
                console.error(err);
                showAlert(this.dialog, _t("A network error occurred."));
            })
            .finally(() => {
                btn.innerHTML = originalHtml;
            });
    },
    _onCopyRef() {
        const ref = this.el.querySelector(".bookingRef");
        if (ref && navigator.clipboard) navigator.clipboard.writeText(ref.textContent);
    },
    _formatCardNumber(e) {
        const input = e.currentTarget;
        let v = input.value.replace(/\D/g, "").slice(0, 16);
        input.value = v.replace(/(.{4})/g, "$1 ").trim();
        const cvNum = this.el.querySelector(".cvNumber");
        if (cvNum) cvNum.textContent = input.value || "••••  ••••  ••••  ••••";
    },
    _formatExpiry(e) {
        const input = e.currentTarget;
        let v = input.value.replace(/\D/g, "").slice(0, 4);
        if (v.length >= 2) v = v.slice(0, 2) + " / " + v.slice(2);
        input.value = v;
        const cvExp = this.el.querySelector(".cvExpiry");
        if (cvExp) cvExp.textContent = input.value || "MM / YY";
    }
});

// ── Widget: Car Detail Page Specifications ─────────────────────────
publicWidget.registry.ThemeDriveXCarDetail = publicWidget.Widget.extend({
    selector: "#detail_content_zone, .detail_content_zone",
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
            if (!el) return;
            const val = d[key] || "";
            el.textContent = cfg.format(val);
        });
        const wrap = zone.closest("#wrap");
        if (wrap) {
            wrap.querySelectorAll(".gallery-thumb").forEach(thumb => {
                thumb.addEventListener("click", () => {
                    const src = thumb.dataset.src;
                    const hero = wrap.querySelector(".heroImg");
                    if (hero && src) hero.src = src;
                    wrap.querySelectorAll(".gallery-thumb").forEach(t => t.classList.remove("active"));
                    thumb.classList.add("active");
                });
            });
        }
        return this._super.apply(this, arguments);
    }
});

// ── Widget: Live Booking Price Calculation (Car Detail Sidebar) ─────────────
publicWidget.registry.ThemeDriveXDetailBooking = publicWidget.Widget.extend({
    selector: '.booking-sidebar',
    events: {
        'change .bookPickup': '_recalc',
        'change .bookReturn': '_recalc',
        'change .insurancePlan': '_recalc',
        'change .bookLocation': '_recalc',
        // Time selects on the detail sidebar (if present) must also trigger
        // a recalc so the sidebar total stays in sync with the backend.
        'change .bookPickupTime': '_recalc',
        'change .bookReturnTime': '_recalc',
    },
    start() {
        this.container = this.el;
        const urlParams = new URLSearchParams(window.location.search);
        const pLoc = urlParams.get('pickup_loc');
        // Pre-select location from URL if present
        if (pLoc) {
            const locSel = this.container.querySelector('.bookLocation');
            if (locSel) {
                for (let i = 0; i < locSel.options.length; i++) {
                    const opt = locSel.options[i];
                    if (String(opt.value) === String(pLoc) ||
                        opt.text.toLowerCase().trim() === pLoc.toLowerCase().trim()) {
                        locSel.selectedIndex = i;
                        break;
                    }
                }
            }
        }
        this._recalc();
        return this._super.apply(this, arguments);
    },
    _recalc() {
        const totalEl   = this.container.querySelector('.totalVal');
        const daysEl    = this.container.querySelector('.daysVal');
        const insLine   = this.container.querySelector('.insuranceLine');
        const insValEl  = this.container.querySelector('.insuranceVal');
        const insPlan   = this.container.querySelector('.insurancePlan');
        const pickup    = this.container.querySelector('.bookPickup');
        const ret       = this.container.querySelector('.bookReturn');
        const locSel    = this.container.querySelector('.bookLocation');
        const btn       = this.container.querySelector('.booking-btn');
        if (!totalEl) return;
        const totalWidget = this.el.querySelector('.booking-total');
        const dailyRate = parseFloat(
            totalWidget ? totalWidget.dataset.dailyRate
                        : (this.el.dataset.dailyRate || 0)
        );
        // Store the pristine href once, then always derive from it
        if (btn && !btn.dataset.originalHref) {
            btn.dataset.originalHref = btn.getAttribute('href') || '';
        }
        const originalHref = btn ? btn.dataset.originalHref : '';

        // ── Build full datetimes from date + optional time fields ─────────
        // The detail sidebar uses hidden date inputs populated by the custom
        // DatePicker; time selects are optional (.bookPickupTime /
        // .bookReturnTime).  Fall back to 12:00 PM when absent, matching
        // the backend default.
        let days = 1;
        const pickupDate = pickup ? pickup.value.trim() : "";
        const returnDate = ret    ? ret.value.trim()    : "";

        if (pickupDate && returnDate) {
            const pTimeEl = this.container.querySelector('.bookPickupTime');
            const rTimeEl = this.container.querySelector('.bookReturnTime');
            const pickupTimeStr = (pTimeEl && pTimeEl.value)
                ? pTimeEl.value.trim() : "12:00 PM";
            const returnTimeStr = (rTimeEl && rTimeEl.value)
                ? rTimeEl.value.trim() : "12:00 PM";

            const pickupDt = _parseDateTimeLocal(pickupDate, pickupTimeStr);
            const returnDt = _parseDateTimeLocal(returnDate, returnTimeStr);

            if (pickupDt && returnDt && returnDt > pickupDt) {
                // Mirror Python backend: delta.days + (1 if delta.seconds > 0 else 0)
                const totalSeconds = (returnDt - pickupDt) / 1000;
                const deltaDays    = Math.floor(totalSeconds / 86400);
                const extraSeconds = totalSeconds % 86400;
                days = Math.max(1, deltaDays + (extraSeconds > 0 ? 1 : 0));
            }
        }

        if (daysEl) daysEl.textContent = `${days} day${days !== 1 ? 's' : ''}`;

        // Insurance price from data-price attribute on the selected option
        const selectedOpt = insPlan ? insPlan.options[insPlan.selectedIndex] : null;
        const insPrice    = selectedOpt ? parseFloat(selectedOpt.dataset.price || 0) : 0;
        const insId       = selectedOpt ? selectedOpt.value : '';
        if (insLine)  insLine.style.display  = insPrice > 0 ? '' : 'none';
        if (insValEl) insValEl.textContent   = insPrice > 0 ? `+$${insPrice}/day` : 'Included';
        const total = (dailyRate * days) + (insPrice * days);
        totalEl.textContent = `$${total.toFixed(0)}`;
        // Update Reserve Now button href with all selected values
        if (btn && originalHref) {
            try {
                const url = new URL(originalHref, window.location.origin);
                if (pickupDate) url.searchParams.set('pickup_date', pickupDate);
                if (returnDate) url.searchParams.set('return_date', returnDate);
                if (locSel && locSel.value) url.searchParams.set('pickup_loc', locSel.value);
                if (insId) url.searchParams.set('insurance_id', insId);
                btn.setAttribute('href', url.pathname + url.search);
            } catch (_) { }
        }
    }
});

// ── Helper: parse "YYYY-MM-DD" + "HH:MM AM/PM" into a local Date ────────────
// Mirrors the backend's strptime(f"{date} {time}", '%Y-%m-%d %I:%M %p').
// Using explicit field extraction (no Date string parsing) avoids all
// browser/UTC quirks so the result is always a true local-time Date.
function _parseDateTimeLocal(dateStr, timeStr) {
    if (!dateStr || !timeStr) return null;
    try {
        // dateStr: "YYYY-MM-DD"
        const dp = dateStr.split('-').map(Number);
        if (dp.length !== 3 || dp.some(isNaN)) return null;
        const [y, mo, d] = dp;

        // timeStr: "HH:MM AM" or "HH:MM PM"  (12-hour clock, space before meridiem)
        const tMatch = timeStr.trim().match(/^(\d{1,2}):(\d{2})\s*(AM|PM)$/i);
        if (!tMatch) return null;
        let h = parseInt(tMatch[1], 10);
        const m = parseInt(tMatch[2], 10);
        const meridiem = tMatch[3].toUpperCase();
        // Convert 12-hour → 24-hour
        if (meridiem === 'AM') {
            if (h === 12) h = 0;       // 12:xx AM → 00:xx
        } else {
            if (h !== 12) h += 12;     // 1–11 PM  → 13–23
        }
        return new Date(y, mo - 1, d, h, m, 0, 0);
    } catch (_) {
        return null;
    }
}

// ── Helper: fetch booked date ranges for a vehicle via JSON RPC ──────────────
function fetchBookedRanges(vehicleId) {
    if (!vehicleId || vehicleId === '0') return Promise.resolve([]);
    return fetch('/vehicle/' + vehicleId + '/booked-dates', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ jsonrpc: '2.0', method: 'call', params: {} }),
    })
        .then(resp => resp.json())
        .then(data => (data && data.result && data.result.ranges) ? data.result.ranges : [])
        .catch(e => { console.warn('[DriveX] Could not fetch booked dates:', e); return []; });
}

// ── Helper: build a DatePicker and link its hidden input ─────────────────────
function buildLinkedPicker(fieldEl) {
    var display = fieldEl.querySelector('.date-display');
    var panel = fieldEl.querySelector('.dp-panel');
    var hidden = fieldEl.querySelector('input[type="hidden"]');
    if (!display || !panel) return null;
    var dp = new DatePicker(fieldEl, display, panel);
    dp.hiddenInput = hidden || null;
    window._dpAll = window._dpAll || [];
    window._dpAll.push(dp);
    fieldEl._dpInstance = dp;
    return dp;
}

// ── Helper: pre-fill a picker from a YYYY-MM-DD string ───────────────────────
function _prefillWizardPicker(dp, dateStr) {
    if (!dp || !dateStr) return;
    var parts = dateStr.split('-').map(Number);
    var y = parts[0], m = parts[1], d = parts[2];
    if (!y || !m || !d) return;
    dp.s.selYear = y;
    dp.s.selMonth = m - 1;
    dp.s.selDay = d;
    dp.s.viewYear = y;
    dp.s.viewMonth = m - 1;
    dp._renderGrid();
    dp._confirm();
}

// ── Helper: select a <select> option matching value or text ──────────────────
function _selectOption(sel, val) {
    if (!sel || !val) return;
    for (var i = 0; i < sel.options.length; i++) {
        if (sel.options[i].value === val || sel.options[i].text.includes(val)) {
            sel.selectedIndex = i;
            sel.dispatchEvent(new Event('change', { bubbles: true }));
            break;
        }
    }
}

// ── Helper: sync Reserve Now button href with selected dates ─────────────────
function _syncDetailBtn(sidebar) {
    if (!sidebar) return;
    var btn = sidebar.querySelector('.booking-btn');
    var pickup = sidebar.querySelector('.bookPickup');
    var ret = sidebar.querySelector('.bookReturn');
    if (!btn || !pickup || !ret) return;
    var href = btn.getAttribute('href') || '';
    try {
        var url = new URL(href, window.location.origin);
        if (pickup.value) url.searchParams.set('pickup_date', pickup.value);
        if (ret.value) url.searchParams.set('return_date', ret.value);
        btn.setAttribute('href', url.pathname + url.search);
    } catch (_) { }
}

// ── Widget: Car Detail Sidebar — Date Pickers with Availability ──────────────
publicWidget.registry.ThemeDriveXDetailDates = publicWidget.Widget.extend({
    selector: '.booking-sidebar',
    start: function () {
        var superResult = this._super.apply(this, arguments);
        var vehicleId = this.el.dataset.vehicleId;
        var pickupField = this.el.querySelector('.bookPickupField');
        var returnField = this.el.querySelector('.bookReturnField');
        if (!pickupField || !returnField) return superResult;
        var pickupDp = buildLinkedPicker(pickupField);
        var returnDp = buildLinkedPicker(returnField);
        // Capture sidebar in closure — do NOT use this.el inside _confirm overrides
        var sidebar = this.el;
        if (pickupDp) {
            var origPickup = pickupDp._confirm.bind(pickupDp);
            pickupDp._confirm = function () {
                origPickup();
                _syncDetailBtn(sidebar);
            };
        }
        if (returnDp) {
            var origReturn = returnDp._confirm.bind(returnDp);
            returnDp._confirm = function () {
                origReturn();
                _syncDetailBtn(sidebar);
            };
        }
        // Fetch booked ranges async, no need to block start()
        if (vehicleId && vehicleId !== '0') {
            fetchBookedRanges(vehicleId).then(function (ranges) {
                if (pickupDp) pickupDp.setBookedRanges(ranges);
                if (returnDp) returnDp.setBookedRanges(ranges);
            });
        }
        return superResult;
    }
});

// ── Widget: Booking Wizard Step 1 — Date Pickers with Availability ───────────
publicWidget.registry.ThemeDriveXBookingDates = publicWidget.Widget.extend({
    selector: '#bwDateGrid',
    start: function () {
        var superResult = this._super.apply(this, arguments);
        var vehicleId = this.el.dataset.vehicleId;
        var pickupField = this.el.querySelector('.tripPickupField');
        var returnField = this.el.querySelector('.tripReturnField');
        if (!pickupField || !returnField) return superResult;
        var pickupDp = buildLinkedPicker(pickupField);
        var returnDp = buildLinkedPicker(returnField);
        var urlParams = new URLSearchParams(window.location.search);
        var pDate = urlParams.get('pickup_date');
        var rDate = urlParams.get('return_date');
        var hasUrlDates = !!(pDate && rDate);
        if (hasUrlDates) {
            // Coming via Reserve Now: pre-fill display + hidden inputs
            _prefillWizardPicker(pickupDp, pDate);
            _prefillWizardPicker(returnDp, rDate);
            // Time selects live outside #bwDateGrid
            var pTime = urlParams.get('pickup_time');
            var rTime = urlParams.get('return_time');
            var bodyEl = this.el.closest('body');
            if (pTime) _selectOption(bodyEl.querySelector('.tripPickupTime'), pTime);
            if (rTime) _selectOption(bodyEl.querySelector('.tripReturnTime'), rTime);
        }
        // Always fetch booked ranges — needed for Continue validation
        if (vehicleId && vehicleId !== '0') {
            var grid = this.el;
            fetchBookedRanges(vehicleId).then(function (ranges) {
                if (pickupDp) pickupDp.setBookedRanges(ranges);
                if (returnDp) returnDp.setBookedRanges(ranges);
                // Store on grid element so wizard can read them on Continue
                grid._bookedRanges = ranges;
                grid._bookedRangesReady = true;
            });
        } else {
            // No vehicle — mark as ready with empty ranges
            this.el._bookedRanges = [];
            this.el._bookedRangesReady = true;
        }
        return superResult;
    }
});
