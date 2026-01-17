/** @odoo-module */
import { NavBar } from "@web/webclient/navbar/navbar";
import { fuzzyLookup } from '@web/core/utils/search';
import { computeAppsAndMenuItems } from "@web/webclient/menus/menu_helpers";
import { useRef, onMounted, onWillUnmount } from "@odoo/owl";
import { patch } from "@web/core/utils/patch";
import { debounce } from "@web/core/utils/timing";

patch(NavBar.prototype, {
    setup() {
        super.setup();
        this.state = {
            searchQuery: "",
            hasResults: false,
            isSearchContext: false,
            isMobile: window.innerWidth <= 768
        };

        const { apps, menuItems } = computeAppsAndMenuItems(this.menuService.getMenuAsTree("root"));
        this._apps = apps;
        this._searchableMenus = menuItems;
        this._searchMenusSchedule = debounce(this._searchMenus.bind(this), 200);
        this.searchResultsRef = useRef("searchResults");
        this._setupMenuObserver();

        onMounted(() => {
            this._initializeSearchElements();
            this._checkMobileView();
        });

        onWillUnmount(() => {
            this._cleanupMenuObserver();
        });
    },

    _setupMenuObserver() {
        this._menuChangeHandler = () => {
            this._updateNavbar();
        };
        if (this.menuService.addEventListener) {
            this.menuService.addEventListener('menu-changed', this._menuChangeHandler);
        }
    },

    _cleanupMenuObserver() {
        if (this.menuService.removeEventListener) {
            this.menuService.removeEventListener('menu-changed', this._menuChangeHandler);
        }
    },

    _updateNavbar() {
        const currentApp = this.menuService.getCurrentApp();
        if (currentApp) {
            this.currentApp = currentApp;
            this.currentAppSections = this.menuService.getMenuAsTree(currentApp.id).children;
            this.render();
        }
    },

    _initializeSearchElements() {
        const sidebarPanel = document.querySelector("#sidebar_panel");
        if (sidebarPanel) {
            this.$search_container = sidebarPanel.querySelector(".search-container");
            this.$search_input = sidebarPanel.querySelector(".search-input input");
            this.$search_results = sidebarPanel.querySelector(".search-results");
            this.$sidebar_menu = sidebarPanel.querySelector(".sidebar_menu");
            if (this.$search_input) {
                this.$search_input.addEventListener('input', this._searchMenusSchedule.bind(this));
            }
        }
    },

    _searchMenus() {
        if (!this.$search_input) return;
        const query = this.$search_input.value.trim();
        if (!query) {
            this._clearSearch();
            return;
        }
        this.state.isSearchContext = true;
        this.state.hasResults = true;
        if (this.$search_results && this.$sidebar_menu) {
            this.$sidebar_menu.style.display = 'none';
            this.$search_results.style.display = 'block';
        }
        const results = [
            ...this._searchApps(query),
            ...this._searchMenuItems(query)
        ];
        this._renderResults(results);
    },

     async _onAppClick(app) {
        if (app.actionID) {
            await this.menuService.selectMenu(app.id);
            await this.env.services.action.doAction(app.actionID, {
                clearBreadcrumbs: true,
            });
        }
        if (this.state.isMobile) {
            this._toggleSidebar(false);
        }
    },

    _clearSearch() {
        if (!this.state.isSearchContext) return;
        this.state.isSearchContext = false;
        if (this.$sidebar_menu) {
            this.$sidebar_menu.style.display = 'block';
        }
        if (this.$search_results) {
            this.$search_results.style.display = 'none';
            this.$search_results.innerHTML = "";
        }
        if (this.$search_input) {
            this.$search_input.value = "";
        }
    },

    _searchApps(query) {
        return fuzzyLookup(query, this._apps, (menu) => menu.label)
            .map((menu) => ({
                category: "apps",
                name: menu.label,
                actionID: menu.actionID,
                id: menu.id,
                webIconData: menu.webIconData,
                xmlid: menu.xmlid,
            }));
    },

    _searchMenuItems(query) {
        return fuzzyLookup(query, this._searchableMenus, (menu) =>
            (menu.parents + " / " + menu.label).split("/").reverse().join("/")
        ).map((menu) => ({
            category: "menu_items",
            name: menu.parents + " / " + menu.label,
            actionID: menu.actionID,
            id: menu.id,
            webIconData: menu.webIconData,
            xmlid: menu.xmlid,
        }));
    },

     async _navigateToApp(menuId, actionId, xmlid) {
        try {
            await this.menuService.selectMenu(menuId);
            if (actionId) {
                await this.env.services.action.doAction(actionId, {
                    clearBreadcrumbs: true,
                });
            }
            if (this.$search_results) {
                this.$search_results.style.display = 'none';
                this.$search_results.innerHTML = '';
            }
            if (this.$search_input) {
                this.$search_input.value = '';
            }
            if (this.$sidebar_menu) {
                this.$sidebar_menu.style.display = 'block';
            }
            const sidebarPanel = document.querySelector("#sidebar_panel");
            if (sidebarPanel) {
                sidebarPanel.style.display = 'none';
                sidebarPanel.classList.remove('show');
            }
            const actionManager = document.querySelector('.o_action_manager');
            if (actionManager) {
                actionManager.style.marginLeft = '0';
                actionManager.style.transition = 'all .1s linear';
            }
            const sidebarToggle = document.querySelector('#openSidebar .fa');
            if (sidebarToggle) {
                sidebarToggle.classList.remove('opened');
            }
            this.state.isSearchContext = false;

        } catch (error) {
            console.error('Error navigating to app:', error);
        }
    },

    _renderResults(results) {
        if (!this.$search_results) return;
        const resultsHtml = results.map((result, index) => `
            <div class="search_icons">
                <a class="o-menu-search-result dropdown-item col-12 ml-auto mr-auto ${index === 0 ? 'active' : ''}"
                   href="#menu_id=${result.id}&action_id=${result.actionID}"
                   data-menu-id="${result.id}"
                   data-action-id="${result.actionID}"
                   data-menu-xmlid="${result.xmlid}"
                   role="menuitem">
                    <div class="app-icon d-flex align-items-center">
                        ${this._renderResultIcon(result)}
                        <span class="ms-2">${result.name}</span>
                    </div>
                </a>
            </div>
        `).join('');
        this.$search_results.innerHTML = resultsHtml;
        this._addSearchResultHandlers();
    },

    _renderResultIcon(result) {
        if (!result.webIconData) {
            return '';
        }
        if (result.webIconData.startsWith('data:image/')) {
            return `<img src="${result.webIconData}"
                        class="search-result-icon"
                        style="width: 24px; height: 24px; margin-right: 8px;"/>`;
        }
        return `<div class="o_app_icon"
                    data-icon="${result.webIconData}"
                    style="width: 24px; height: 24px; margin-right: 8px;"></div>`;
    },

    _addSearchResultHandlers() {
        if (!this.$search_results) return;
        const searchResults = this.$search_results.querySelectorAll('.search_icons a');
        searchResults.forEach(element => {
            element.addEventListener('click', async (e) => {
                e.preventDefault();
                const menuId = parseInt(element.dataset.menuId);
                const actionId = parseInt(element.dataset.actionId);
                const xmlid = element.dataset.menuXmlid;
                await this._navigateToApp(menuId, actionId, xmlid);
            });
        });
    }
});