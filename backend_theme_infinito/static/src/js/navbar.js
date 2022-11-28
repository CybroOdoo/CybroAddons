/** @odoo-module **/
import { NavBar } from "@web/webclient/navbar/navbar";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { WebClient } from "@web/webclient/webclient";
import { ControlPanel } from "@web/search/control_panel/control_panel";
import { patch } from "@web/core/utils/patch";
import ajax from 'web.ajax';
import InfinitoRecentApps from './recentApps';
import MenuBookmark from 'backend_theme_infinito.MenuBookmark';
import session from 'web.session';
const { fuzzyLookup } = require('@web/core/utils/search');
import { computeAppsAndMenuItems } from "@web/webclient/menus/menu_helpers";
import core from 'web.core';
import { variables, colors, to_color } from 'backend_theme_infinito.variables';
const { onMounted, onWillStart, useExternalListener, mount, useRef, useState} = owl;
patch(NavBar.prototype, 'backend_theme_infinito/static/src/js/navbar.NavBar.js', {

    /**
     * @override
     */
    setup() {
        this._super();
        this._search_def = $.Deferred();
        let {
            apps,
            menuItems
        } = computeAppsAndMenuItems(this.menuService.getMenuAsTree("root"));
        this._apps = apps;
        this._searchableMenus = menuItems;

        onMounted(() => {
            this.$search_container = $(".search-container");
            this.$search_input = $(".search-input input");
            this.$search_results = $(".search-results");
            this.$app_menu = $(".app-menu");
            this.$dropdown_menu = $(".dropdown-menu");
            this.doGreeting();
        });
    },

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

    _searchMenusSchedule: function() {
        this.$search_results.removeClass("o_hidden")
        this.$app_menu.addClass("o_hidden");
        this._search_def.reject();
        this._search_def = $.Deferred();
        setTimeout(this._search_def.resolve.bind(this._search_def), 50);
        this._search_def.done(this._searchMenus.bind(this));
    },

    _searchMenus: function() {
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
        this.$search_results.html(
            core.qweb.render(
                "backend_theme_infinito.SearchResults", {
                    results: results,
                    widget: this,
                }
            )
        );
    },
    onClick(ev) {
        let data;
        if (ev.target.classList.contains('nav-link') || ev.target.classList.contains('dropdown-item')) {
            data = ev.target.dataset
        } else {
            data = $(ev.target).parent()[0].dataset;
        }
        let app = {
            'appId': data.appId
        }
        if (data) ajax.jsonRpc('/theme_studio/add_recent_app', 'call', {
            app
        });
    },
    get sidebarEnabled() {
        return session.sidebar;
    },
    set sidebarEnabled(val) {

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
        return session.sidebarUser;;
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
    }
});

patch(WebClient.prototype, 'backend_theme_infinito/static/src/js/navbar.WebClient.js', {
    setup() {
        this._super();
        useExternalListener(document.body, 'mousemove', this.mouseMove);
        onWillStart(this.onWillStart);
        onMounted(() => {
            this.menuBookMark = mount(MenuBookmark, document.body);
            this.recent = mount(InfinitoRecentApps, document.body);
        })
    },
    async onWillStart() {
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
     rerenderMenuBookmark(){
        this.menuBookmark.state.menus = session.infinitoMenuBookmarks;
    },
    mouseMove(ev) {
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
                if (recentapps){
                recentapps.classList.add('d-none');
            }}
        }
        if (session.infinitoBookmarks.length && session.infinitoBookmark && this.env.services.ui.size >= 4) {
            var Menuboook = document.getElementById("menuBookmark");
            if (ev.clientX >= (screen.availWidth - 160)) {
             if (Menuboook){
                Menuboook.classList.add('d-flex');
                }
            } else {
            if (Menuboook){
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
    darkModeCheck() {
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

patch(DropdownItem.prototype, 'backend_theme_infinito/static/src/js/navbar.MenuItem.js', {
    onClick(ev) {
        this._super(ev);
        if (ev.target.classList.contains('o_app')) {
            let app = {
                'appId': ev.target.dataset.section
            }
            ajax.jsonRpc('/theme_studio/add_recent_app', 'call', {
                app
            });
        }
    }
});

patch(ControlPanel.prototype, 'backend_theme_infinito/static/src/js/navbar.ControlPanel.js', {
    async onBookmark(ev) {
        let action_id = this.env.config.actionId;
        let url = location.href.split('/');
        let menu_url = url[url.length - 1];
        if (!this.state.infinitoBookmarks.includes(action_id)) {
            let menu = {
                'actionId': action_id,
                'menuUrl': menu_url
            }
            let book = {
                name: $('.breadcrumb-item.active').text(),
                short_name: $('.breadcrumb-item.active').text().substring(0, 2).toUpperCase(),
                url: menu_url
            }
            await ajax.jsonRpc('/theme_studio/add_menu_bookmarks', 'call', {
                menu
            });
            ev.target.classList.add("active");
            this.state.infinitoBookmarks.push(action_id)
            this.state.infinitoMenuBookmarks.push(book);
            console.log(this.state)
        } else {
            let index = this.state.infinitoBookmarks.indexOf(action_id);
            this.state.infinitoBookmarks.splice(index, 1);
            this.state.infinitoMenuBookmarks.splice(index, 1);
            let menu = {
                'actionId': action_id
            }
            await ajax.jsonRpc('/theme_studio/remove_menu_bookmarks', 'call', {
                menu
            });
            ev.target.classList.remove("active");
        }
    },

    setup() {
        this._super();
        onMounted(this.mounted);
        this.state = useState({
            infinitoBookmarks: session.infinitoBookmarks,
            infinitoMenuBookmarks: session.infinitoMenuBookmarks
        });
        this.ref = useRef('bookmark');
    },

    mounted() {
        if (this.env.config && session.infinitoBookmark) {
            let action_id = this.env.config.actionId;
            if (this.state.infinitoBookmarks.includes(action_id)) {
            if (this.ref.el){
                this.ref.el.classList.add("active");
            }}
        }
    },

    get bookmarkOn() {
        return session.infinitoBookmark;
    }
});

if (session.infinitoChameleon) {
    setInterval(() => {
        let randomColor = colors[Math.floor(Math.random() * colors.length)];
        for (let key in variables) {
            let index = variables[key][0] - 1;
            let percentage = variables[key][1];
            document.documentElement.style.setProperty(key, to_color(randomColor[index], percentage))
        }
    }, 600000);
}