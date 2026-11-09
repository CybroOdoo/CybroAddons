/** @odoo-module **/
import { onMounted, onPatched, onWillUnmount, useListener } from "@odoo/owl";


import { useBus } from "@web/core/utils/hooks";
import { NavBar } from "@web/webclient/navbar/navbar";
import { patch } from "@web/core/utils/patch";
import { rpc } from "@web/core/network/rpc";
import { session } from "@web/session";
import { _t } from "@web/core/l10n/translation";
import { fuzzyLookup } from "@web/core/utils/search";
import { computeAppsAndMenuItems } from "@web/webclient/menus/menu_helpers";



patch(NavBar.prototype, {

    setup() {
        super.setup();
        this._search_def = null;
        this._search_timeout = null;

        let { apps, menuItems } = computeAppsAndMenuItems(this.menuService.getMenuAsTree("root"));
        this._apps = apps;
        this._searchableMenus = menuItems;
        Object.assign(this.state, {
            flag: false,
            sidebarOpen: false,
            searchQuery: "",
            searchResults: []
        });


        useListener(document, "click", this.onSidebarOutsideClick.bind(this));
        useBus(this.env.bus, "INFINITO:CLOSE_SIDEBAR", () => this.closeSidebar());
        useBus(this.env.bus, "MENUS:APP-CHANGED", () => this.closeSidebar());

        onMounted(() => {
            this._setupFullScreenAppsMenuListeners();
            this.updateSidebarMargin();
        });

        onWillUnmount(() => {
            clearTimeout(this._search_timeout);
            this._removeFullScreenListeners?.();
        });

        onPatched(() => {
            this.updateSidebarMargin();
        });
    },
    get themeNav() {
        return this.navRef?.() || this.root();
    },

    _hideActionManagerForFullScreenMenu() {
        const actionManager = document.querySelector(".o_action_manager");
        if (actionManager) {
            actionManager.style.display = "none";
        }
    },

    _showActionManagerAfterFullScreenMenu() {
        const actionManager = document.querySelector(".o_action_manager");
        if (actionManager) {
            actionManager.style.display = "";
        }
    },
    _closeFullScreenMenu() {
        const toggle = this.themeNav?.querySelector("a.full[data-bs-toggle='dropdown']");
        if (!toggle) return;
        const menu = this.themeNav?.querySelector('.fullscreen-menu');
        if (menu) {
            menu.classList.remove('show');
        }
        toggle.classList.remove('show');
        toggle.setAttribute('aria-expanded', 'false');
        // Dispatch the hidden event to trigger our cleanup
        const event = new Event('hidden.bs.dropdown', { bubbles: true });
        toggle.dispatchEvent(event);
    },
    _hideNavbarMenusForFullScreenAppsMenu() {
        this._setElementsDisplay('.o_menu_sections', 'none');
        this._setElementsDisplay('.o_menu_brand', 'none');
    },

    _showNavbarMenusAfterFullScreenAppsMenu() {
        this._setElementsDisplay('.o_menu_sections', 'flex');
        this._setElementsDisplay('.o_menu_brand', 'block');
    },

    _setupFullScreenAppsMenuListeners() {
        const toggle = this.themeNav?.querySelector("a.full[data-bs-toggle='dropdown']");
        if (!toggle) {
            return;
        }
        const onShow = () => {
            this._hideNavbarMenusForFullScreenAppsMenu();
            this._hideActionManagerForFullScreenMenu();
        };
        const onHide = () => {
            this._showNavbarMenusAfterFullScreenAppsMenu();
            this._clearSearch();
            this._showActionManagerAfterFullScreenMenu();
        };
        toggle.addEventListener("show.bs.dropdown", onShow);
        toggle.addEventListener("hidden.bs.dropdown", onHide);
        this._removeFullScreenListeners = () => {
            toggle.removeEventListener("show.bs.dropdown", onShow);
            toggle.removeEventListener("hidden.bs.dropdown", onHide);
        };
    }
    ,

    closeSidebar(ev) {
        ev?.preventDefault();
        this.state.sidebarOpen = false;
        this.updateSidebarMargin();
    },

    onSidebarOutsideClick(ev) {
        if (!this.state.sidebarOpen || !(ev.target instanceof Element)) return;
        if (!ev.target.closest('#sidebar_panel, #openSidebar, #closeSidebar')) {
            this.closeSidebar();
        }
    },

    toggleSidebar(ev) {
        ev.preventDefault();
        this.state.sidebarOpen = !this.state.sidebarOpen;
        this.updateSidebarMargin();
    },

    updateSidebarMargin() {
        const actionManager = document.querySelector(".o_action_manager");
        const topHead = this.themeNav?.querySelector(".top_heading");
        const sidebarPanel = document.getElementById('sidebar_panel');
        const isMin = sidebarPanel && sidebarPanel.classList.contains("m-sidebar");

        if (this.state.sidebarOpen) {
            if (actionManager) {
                actionManager.classList.add("sidebar_margin");
                if (isMin) {
                    actionManager.classList.add("m-sidebar");
                } else {
                    actionManager.classList.remove("m-sidebar");
                }
            }
            if (topHead) {
                topHead.classList.add("sidebar_margin");
                if (isMin) {
                    topHead.classList.add("m-sidebar");
                } else {
                    topHead.classList.remove("m-sidebar");
                }
            }
        } else {
            if (actionManager) {
                actionManager.classList.remove("sidebar_margin");
                actionManager.classList.remove("m-sidebar");
            }
            if (topHead) {
                topHead.classList.remove("sidebar_margin");
                topHead.classList.remove("m-sidebar");
            }
        }
    },

    get greeting() {
        const hour = new Date().getHours();
        const text = hour < 12 ? _t("Good Morning") : hour < 16 ? _t("Good Afternoon") : _t("Good Evening");
        return `${text}, ${session.name || _t("User")}`;
    },

    get userAvatar() {
        return `/web/image?model=res.users&field=avatar_128&id=${session.uid}`;
    },

    _clearSearch() {
        this.state.searchQuery = "";
        this.state.searchResults = [];
    },

    _searchMenusSchedule(ev) {
        this.state.searchQuery = ev.target.value;
        clearTimeout(this._search_timeout);
        this._search_timeout = setTimeout(() => this._searchMenus(), 50);
    },

    _searchMenus() {
        const query = this.state.searchQuery;
        if (!query) {
            this.state.searchResults = [];
            return;
        }

        var results = [];
        fuzzyLookup(query, this._apps, (menu) => menu.label)
            .forEach((menu) => {
                let webIconData = menu.webIcon || menu.webIconData || menu.web_icon_data || menu.web_icon || null;
                if (webIconData && !webIconData.startsWith('data:image')) {
                    webIconData = "data:image/png;base64," + webIconData;
                }
                results.push({
                    category: "apps",
                    name: menu.label,
                    actionID: menu.actionID,
                    id: menu.id,
                    webIconData: webIconData,
                });
            });

        fuzzyLookup(query, this._searchableMenus, (menu) =>
            (menu.parents + " / " + menu.label).split("/").reverse().join("/")
        ).forEach((menu) => {
            results.push({
                category: "menu_items",
                name: menu.parents + " / " + menu.label,
                actionID: menu.actionID,
                id: menu.id,
            });
        });

        this.state.searchResults = results;
    },

    onClick(ev) {
        ev.preventDefault();

        let target = ev.target;
        let data;

        while (target && !target.dataset.menuId && target !== document.body) {
            target = target.parentElement;
        }

        if (target && target.dataset) {
            data = target.dataset;
        }

        if (data && data.menuId) {
            const menuId = parseInt(data.menuId);
            const menu = this.menuService.getMenu(menuId);

            if (menu) {
                this.menuService.selectMenu(menu);
                this._clearSearch();
                if (ev.target.closest('.fullscreen-menu')) {
                    this._closeFullScreenMenu();
                }
                setTimeout(() => this._showNavbarMenusAfterFullScreenAppsMenu(), 0);

                let app = { 'appId': data.menuId };
                rpc('/theme_studio/add_recent_app', {

                    args: [app]
                }).then(() => {
                    this.env.bus.trigger('INFINITO:RECENT_APPS_UPDATED');
                }).catch(() => {
                    this.env.services.notification.add(_t("Could not update recent apps."), {
                        type: "warning",
                    });
                });
            }
        }

        if (window.innerWidth < 992 || ev.target.closest('.sidebar')) {
            this.state.sidebarOpen = false;
            this.updateSidebarMargin();
        }

        const openDropdowns = this.themeNav?.querySelectorAll('.dropdown-menu.show') || [];
        openDropdowns.forEach(dropdown => {
            dropdown.classList.remove('show');
        });
    },

    OnClickMainMenu() {
        this.state.flag = true;
        const appComponents = document.querySelector('.app_components');
        if (appComponents && getComputedStyle(appComponents).display === "none") {
            appComponents.style.display = "block";
            appComponents.style.animation = "fadeIn 250ms";
            this._setElementsDisplay('.o_menu_sections', 'none');
            this._setElementsDisplay('.o_menu_brand', 'none');
            this._setElementsDisplay('.o_action_manager', 'none');
            this._setElementsDisplay('.sidebar_panel', this.state.sidebarOpen ? 'block' : 'none');
        } else {
            if (appComponents) {
                appComponents.style.display = "none";
            }
            this._setElementsDisplay('.o_menu_sections', 'flex');
            this._setElementsDisplay('.o_menu_brand', 'block');
            this._setElementsDisplay('.o_action_manager', 'block');
            this._setElementsDisplay('.sidebar_panel', this.state.sidebarOpen ? 'block' : 'none');
        }
    },

    OnClickCloseMainMenu() {
        this.state.flag = false;
        const appComponents = document.querySelector('.app_components');
        if (appComponents) {
            appComponents.style.display = "none";
        }
        this._setElementsDisplay('.o_menu_sections', 'flex');
        this._setElementsDisplay('.o_menu_brand', 'block');
        this._setElementsDisplay('.o_action_manager', 'block');
        this._setElementsDisplay('.sidebar_panel', this.state.sidebarOpen ? 'block' : 'none');
    },

    OnclickFullScreenMenu() {
        const hasShow = this.themeNav?.querySelector('a.show');
        if (hasShow) {
            this._setElementsDisplay('.o_menu_sections', 'none');
            this._setElementsDisplay('.o_menu_brand', 'none');
        } else {
            this._setElementsDisplay('.o_menu_sections', 'flex');
            this._setElementsDisplay('.o_menu_brand', 'block');
        }
    },

    _setElementsDisplay(selector, displayValue) {
        const elements = document.querySelectorAll(selector);
        elements.forEach(el => {
            el.style.display = displayValue;
            el.style.setProperty('display', displayValue, 'important');
        });
    },

    get infinitoRtl() {
        return session.infinitoRtl ? "infinito-rtl" : "";
    },
    get sidebarEnabled() {
        return session.sidebar;
    },
    get sidebarIcon() {
        return session.sidebarIcon;
    },
    get sidebarName() {
        return session.sidebarName;
    },
    get sidebarResize() {
        return session.sidebarIcon && !session.sidebarName ? 'm-sidebar' : '';
    },
    get sidebarCompany() {
        return session.sidebarCompany;
    },
    get sidebarCompanyLogo() {
        return session.sidebarCompany ? 'has-company' : '';
    },
    get sidebarUser() {
        return session.sidebarUser;
    },
    get FullScreenEnabled() {
        return session.fullscreen ? 'infinito-navbar-hover' : '';
    },
    get fullScreenApp() {
        return session.fullScreenApp;
    },
});

