/** @odoo-module **/
// Import necessary components and functionalities from Odoo libraries
import {NavBar} from "@web/webclient/navbar/navbar";
import {DropdownItem} from "@web/core/dropdown/dropdown_item";
import {WebClient} from "@web/webclient/webclient";
import {ControlPanel} from "@web/search/control_panel/control_panel";
import {patch} from "@web/core/utils/patch";
import {jsonrpc} from "@web/core/network/rpc_service";
import InfinitoRecentApps from './recentApps';
import MenuBookmark from 'backend_theme_infinito.MenuBookmark';
import {session} from "@web/session";
import {renderToFragment} from "@web/core/utils/render";

const {fuzzyLookup} = require('@web/core/utils/search');
import {computeAppsAndMenuItems} from "@web/webclient/menus/menu_helpers";
import {variables, colors, to_color} from './variables';

const {
    onMounted,
    onWillStart,
    useExternalListener,
    mount,
    useRef,
    useState
} = owl;
// Patching the NavBar component
patch(NavBar.prototype, {

    /**
     * @override
     * Setup method to initialize the NavBar component
     */
    setup() {
        // Call the setup method of the parent class
        super.setup()
        // Deferred object for search functionality
        this._search_def = $.Deferred();
        // Compute apps and menu items
        let {
            apps,
            menuItems
        } = computeAppsAndMenuItems(this.menuService.getMenuAsTree("root"));
        this._apps = apps;
        this._searchableMenus = menuItems;
        this.state = useState({
            flag: false,
        });
        // Execute mounted logic after component is mounted
        onMounted(() => {
            // Assign DOM elements
            this.$search_container = $(".search-container");
            this.$search_input = $(".search-input input");
            this.$search_results = $(".search-results");
            this.$app_menu = $(".app-menu");
            this.$dropdown_menu = $(".dropdown-menu");
            this.doGreeting(); // Perform greeting
        });
    },
    // Method for greeting user based on current time
    doGreeting() {
        let time = new Date().getHours();
        let greetings = 'Good'
        if (12 > time > 0) {
            greetings = 'Good Morning, '
        } else if (16 > time > 12) {
            greetings = 'Good Afternoon, '
        } else {
            greetings = 'Good Evening, '
        }
        greetings += session.name
        $('.infinito-greeting').text(greetings)
        let img = `${session["web.base.url"]}/web/image?model=res.users&field=avatar_128&id=${session.uid}`
        $('.infinito-user_img').attr('src', img)
    },
    // Method to search menus based on user input
    _searchMenusSchedule() {
        // Implementation of search menus
        this.$search_results.removeClass("o_hidden")
        this.$app_menu.addClass("o_hidden");
        this._search_def.reject();
        this._search_def = $.Deferred();
        setTimeout(this._search_def.resolve.bind(this._search_def), 50);
        this._search_def.done(this._searchMenus.bind(this));
    },
    // Method to handle menu search
    _searchMenus() {
        // Implementation of menu search
        var query = this.$search_input.val();
        if (query === "") {
            this.$search_container.removeClass("has-results");
            this.$app_menu.removeClass("o_hidden");
            this.$search_results.empty();
            return;
        }
        var results = [];
        fuzzyLookup(query, this._apps, (menu) => menu.label)
            .forEach((menu) => {
                results.push({
                    category: "apps",
                    name: menu.label,
                    actionID: menu.actionID,
                    id: menu.id,
                    webIconData: menu.webIconData,
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
        this.$search_container.toggleClass(
            "has-results",
            Boolean(results.length)
        );
        const render = renderToFragment(
            "backend_theme_infinito.SearchResults", {
                results: results,
                widget: this,
            }
        );
        const searchResultsDiv = (this.$search_results[0]);
        searchResultsDiv.appendChild(render);
    },
    // Method to handle click events
    onClick(ev) {
        // Implementation of click event handling
        let data;
        if (ev.target.classList.contains('nav-link') || ev.target.classList.contains('dropdown-item')) {
            data = ev.target.dataset
        } else {
            var targetElement = ev.target
            data = targetElement.parentNode.parentNode.dataset;
        }
        let app = {
            'appId': data.appId
        }
        if (data) jsonrpc('/theme_studio/add_recent_app', {
            method: 'call',
            args: [app]
        });
        $('.dropdown:first').click();
    },
    OnClickMainMenu() {
        this.state.flag = true;
        if ($('.app_components').css("display") === "none") {
            $('.app_components').fadeIn(250);
            $('.o_menu_sections').attr('style', 'display: none !important');
            $('.o_menu_brand').attr('style', 'display: none !important');
            $('.o_action_manager').attr('style', 'display: none !important');
            $('.sidebar_panel').attr('style', 'display: none !important');
        } else {
            $('.app_components').fadeOut(50);
            $('.o_menu_sections').attr('style', 'display: flex !important');
            $('.o_menu_brand').attr('style', 'display: block !important');
            $('.o_action_manager').attr('style', 'display: block !important');
            $('.sidebar_panel').attr('style', 'display: block !important');
        }
    },
    OnClickCloseMainMenu() {
        this.state.flag = false;
            $('.app_components').fadeOut(50);
            $('.o_menu_sections').attr('style', 'display: flex !important');
            $('.o_menu_brand').attr('style', 'display: block !important');
            $('.o_action_manager').attr('style', 'display: block !important');
            $('.sidebar_panel').attr('style', 'display: none !important');
    },
    OnclickFullScreenMenu() {
        if ($('a').hasClass('show')) {
            $('.o_menu_sections').attr('style', 'display: none !important');
            $('.o_menu_brand').attr('style', 'display: none !important');
        } else {
            $('.o_menu_sections').attr('style', 'display: flex !important');
            $('.o_menu_brand').attr('style', 'display: block !important');
        }
    },
    // Getters and setters for various properties
    get sidebarEnabled() {
        // Get the sidebar enabled state
        return session.sidebar;
    },
    set sidebarEnabled(val) {
        // Set the sidebar enabled state
    },
    get sidebarIcon() {
        return session.sidebarIcon;
    },
    set sidebarIcon(val) {
    },
    get sidebarName() {
        return session.sidebarName;
    },
    set sidebarName(val) {
    },
    get sidebarResize() {
        return session.sidebarIcon && !session.sidebarName ? 'm-sidebar' : ''
    },
    set sidebarResize(val) {
    },
    get sidebarCompany() {
        return session.sidebarCompany;
    },
    set sidebarCompany(val) {
    },
    get sidebarCompanyLogo() {
        return session.sidebarCompany ? 'has-company' : '';
    },
    set sidebarCompanyLogo(val) {
    },
    get sidebarUser() {
        return session.sidebarUser;
        ;
    },
    set sidebarUser(val) {
    },
    get FullScreenEnabled() {
        return session.fullscreen ? 'd-none' : '';
    },
    set FullScreenEnabled(val) {
    },
    get fullScreenApp() {
        return session.fullScreenApp;
    },
    set fullScreenApp(val) {
    },
});
// Patching the WebClient component
patch(WebClient.prototype, {
    // Setup method to initialize the WebClient component
    setup() {
        // Call the setup method of the parent class
        super.setup()
        // Attach mouse move listener
        useExternalListener(document.body, 'mousemove', this.mouseMove);
        // Execute logic on component will start
        onWillStart(this.onWillStart);
        // Execute logic after component is mounted
        onMounted(() => {
            // Mount MenuBookmark and InfinitoRecentApps components
            this.menuBookMark = mount(MenuBookmark, document.body);
            this.recent = mount(InfinitoRecentApps, document.body);
        })
    },
    // Logic executed before component starts
    async onWillStart() {
        // Implementation of onWillStart logic
        this.fullScreenEnabled = session.fullscreen;
        this.recentApps = session.recentApps;
        this.is_dark = false;
        if (session.infinitoRtl) {
            $('.o_web_client').addClass('infinito-rtl');
        } else {
            $('.o_web_client').removeClass('infinito-rtl')
        }
        this.last_check = new Date().getMinutes();
        this.darkModeCheck();
    },
    // Method to rerender menu bookmark
    rerenderMenuBookmark() {
        // Implementation of rerendering menu bookmark
        this.menuBookmark.state.menus = session.infinitoMenuBookmarks;
    },
    // Method to handle mouse move events
    mouseMove(ev) {
        // Implementation of mouse move handling
        if (this.fullScreenEnabled && this.env.services.ui.size >= 4) {
            if (ev.clientY <= 20) {
                $(ev.target).parents('.o_action_manager').prev().find('nav').removeClass('d-none');
            } else {
                $(ev.target).parents('.o_action_manager').prev().find('nav').addClass('d-none');
            }
        }
        if (this.recentApps && this.env.services.ui.size >= 4) {
            var recentapps = document.getElementById("recentApps");
            if (ev.clientY >= (screen.availHeight - 200)) {
                recentapps.classList.remove('d-none');
            } else {
                if (recentapps) {
                    recentapps.classList.add('d-none');
                }
            }
        }
        if (session.infinitoBookmarks.length && session.infinitoBookmark && this.env.services.ui.size >= 4) {
            var Menuboook = document.getElementById("menuBookmark");
            if (ev.clientX >= (screen.availWidth - 160)) {
                if (Menuboook) {
                    Menuboook.classList.add('d-flex');
                }
            } else {
                if (Menuboook) {
                    Menuboook.classList.remove('d-flex');
                }
            }
        }
        let now = new Date();
        if (this.last_check != now.getMinutes()) {
            this.darkModeCheck();
            this.last_check = now.getMinutes();
        }
    },
    // Method to check dark mode
    darkModeCheck() {
        // Implementation of dark mode check
        if (session.infinitoDark) {
            if (session.infinitoDarkMode == 'all') {
                $('.o_web_client').addClass('dark-mode');
                this.is_dark = true;
            } else {
                let now = new Date();
                let dark = false;
                let hour = now.getHours();
                let min = now.getMinutes();
                let start = session.infinitoDarkStart.split(':');
                let startHour = parseInt(start[0]);
                let startMin = parseInt(start[1]);
                let end = session.infinitoDarkEnd.split(':');
                let endHour = parseInt(end[0]);
                let endMin = parseInt(end[1]);
                if (startHour > endHour) {
                    endHour += 24;
                    if (hour < startHour) {
                        hour += 24;
                    }
                }
                if (endHour > hour && hour > startHour) {
                    dark = true;
                } else if (hour == startHour && min >= startMin && hour < endHour) {
                    dark = true;
                } else if (hour == endHour && min <= endMin && hour >= startHour) {
                    dark = true;
                } else {
                    dark = false;
                }
                if (dark) {
                    $('.o_web_client').addClass('dark-mode');
                    this.is_dark = true;
                } else {
                    $('.o_web_client').removeClass('dark-mode');
                    this.is_dark = false;
                }
            }
        } else if (!session.infinitoDark && this.is_dark) {
            $('.o_web_client').removeClass('dark-mode');
            this.is_dark = false;
        }
    },
});
// Patching the DropdownItem component
patch(DropdownItem.prototype, {
    // Method to handle click events
    onClick(ev) {
        // Implementation of click event handling
        super.onClick(ev);
        if (ev.target.classList.contains('o_app')) {
            let app = {
                'appId': ev.target.dataset.section
            }
            jsonrpc('/theme_studio/add_recent_app', {
                method: 'call',
                args: [app]
            });
        }
    }
});
// Patching the ControlPanel component
patch(ControlPanel.prototype, {
        setup() {
        // Call the setup method of the parent class
            super.setup();
            // Execute logic after component is mounted
            onMounted(this.mounted);
            // Initialize component state and reference
            this.state = useState({
                infinitoBookmarks: session.infinitoBookmarks,
                infinitoMenuBookmarks: session.infinitoMenuBookmarks,
                infinitoBookmarkColors:[]
            });
            this.ref = useRef('bookmark');
        },
    // Method to handle bookmarking
    async onBookmark(ev) {
    // Implementation of bookmarking
        let action_id = this.env.config.actionId;
        let url = location.href.split('/');
        let menu_url = url[url.length - 1];

    // Check if the action is already bookmarked
        if (!this.state.infinitoBookmarks.includes(action_id)) {
            let menu = {
                'actionId': action_id,
                'menuUrl': menu_url
            };
            let book = {
                name: $('.breadcrumb-item.active').text(),
                short_name: $('.breadcrumb-item.active').text().substring(0, 2).toUpperCase(),
                url: menu_url
            };

            // Add bookmark through jsonrpc
            await jsonrpc('/theme_studio/add_menu_bookmarks', {
                method: 'call',
                args: { menu }
            });

            // Update DOM and state dynamically
            ev.target.classList.add("active");
            ev.target.style.color = 'yellow';
            this.state.infinitoBookmarks.push(action_id);
            this.state.infinitoMenuBookmarks.push(book);
            this.state.infinitoBookmarkColors.push('yellow');
            location.reload();

        } else {
            let index = this.state.infinitoBookmarks.indexOf(action_id);
            this.state.infinitoBookmarks.splice(index, 1);
            this.state.infinitoMenuBookmarks.splice(index, 1);
            this.state.infinitoBookmarkColors.push('blue');
            let menu = {
                'actionId': action_id
            };

        // Remove bookmark through jsonrpc
            await jsonrpc('/theme_studio/remove_menu_bookmarks', {
                method: 'call',
                args: { menu }
            });

            // Update DOM and state dynamically
            ev.target.classList.remove("active");
            ev.target.style.color = ''; // Reset the color or apply your preferred default
        }
    },

    // Setup method to initialize the ControlPanel component

    mounted() {
        if (this.env.config && session.infinitoBookmark) {
            let action_id = this.env.config.actionId;
            if (this.state.infinitoBookmarks.includes(action_id)) {
                if (this.ref.el) {
                    this.ref.el.classList.add("active");
                }
            }
        }
    },

    get bookmarkOn() {
        return session.infinitoBookmark;
    },
    set bookmarkOn(value) {
        session.bookmarkOn = value;
    }
});
