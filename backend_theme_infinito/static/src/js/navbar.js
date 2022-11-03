/** @odoo-module **/

import { NavBar, MenuItem } from "@web/webclient/navbar/navbar";
import { WebClient } from "@web/webclient/webclient";
import ControlPanel from "web.ControlPanel";
import { patch } from 'web.utils';
import ajax from 'web.ajax';
import { useListener } from 'web.custom_hooks';
import { useBus } from "@web/core/utils/hooks";
import InfinitoRecentApps from './recentApps';
import MenuBookmark from 'backend_theme_infinito.MenuBookmark';
import session from 'web.session';
const { fuzzyLookup } = require('@web/core/utils/search');
import { computeAppsAndMenuItems } from "@web/webclient/menus/menu_helpers";
import core from 'web.core';
import Bus from 'web.Bus';
import { variables, colors, to_color} from 'backend_theme_infinito.variables';
const bus = new Bus();

patch(NavBar.prototype, 'backend_theme_infinito/static/src/js/navbar.NavBar.js', {
     /**
     * @override
     */
     setup() {
        this._super();
        this._search_def = $.Deferred();
        let { apps, menuItems } = computeAppsAndMenuItems(this.menuService.getMenuAsTree("root"));
        this._apps = apps;
        this._searchableMenus = menuItems;
    },

    mounted() {
        this._super();
        this.$search_container = $(".search-container");
        this.$search_input = $(".search-input input");
        this.$search_results = $(".search-results");
        this.$app_menu = $(".app-menu");
        this.$dropdown_menu = $(".dropdown-menu");
        this.doGreeting();
    },

    doGreeting(){
        let time =  new Date().getHours();
        let greetings = 'Good'
        if(12 > time > 0){
            greetings = 'Good Morning, '
        }
        else if(16 > time > 12){
            greetings = 'Good Afternoon, '
        }else {
            greetings = 'Good Evening, '
        }
        greetings += session.name
        $('.infinito-greeting').text(greetings)
        let img = `${session["web.base.url"]}/web/image?model=res.users&field=avatar_128&id=${session.uid}`
        $('.infinito-user_img').attr('src', img)
    },

     _searchMenusSchedule: function () {
        this.$search_results.removeClass("o_hidden")
        this.$app_menu.addClass("o_hidden");
        this._search_def.reject();
        this._search_def = $.Deferred();
        setTimeout(this._search_def.resolve.bind(this._search_def), 50);
        this._search_def.done(this._searchMenus.bind(this));
    },

    _searchMenus: function () {
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
                "backend_theme_infinito.SearchResults",
                {
                    results: results,
                    widget: this,
                }
            )
        );
    },
    onClick(ev){
        let data;
        if (ev.target.classList.contains('nav-link') || ev.target.classList.contains('dropdown-item')){
            data = ev.target.dataset
        } else {
            data = $(ev.target).parent()[0].dataset;
        }
        let app = {
            'appId': data.appId
        }
        if(data) ajax.jsonRpc('/theme_studio/add_recent_app', 'call', {app});
    },
    get sidebarEnabled(){
        return session.sidebar;
    },
    get sidebarIcon(){
        return session.sidebarIcon;
    },
    get sidebarName(){
        return session.sidebarName;
    },
    get sidebarResize(){
        return session.sidebarIcon && !session.sidebarName ? 'm-sidebar' : ''
    },
    get sidebarCompany(){
        return session.sidebarCompany;
    },
    get sidebarCompanyLogo(){
        return session.sidebarCompany? 'has-company': '';
    },
    get sidebarUser(){
        return session.sidebarUser;;
    },
    get FullScreenEnabled(){
        return session.fullscreen ? 'd-none': '';
    },
    get fullScreenApp(){
        return session.fullScreenApp;
    }
});

patch(WebClient.prototype, 'backend_theme_infinito/static/src/js/navbar.WebClient.js', {
    async willStart(){
        this._super();
        useListener('mousemove', '.o_web_client', this.mouseMove);
        this.fullScreenEnabled = session.fullscreen;
        this.recentApps = session.recentApps;
        this.recent = new InfinitoRecentApps();
        this.menuBookmark = new MenuBookmark(this);
        this.is_dark = false;
        this.recent._mount();
        this.menuBookmark._mount();
        if(session.infinitoRtl){
            $('.o_web_client').addClass('infinito-rtl');
        } else {
            $('.o_web_client').removeClass('infinito-rtl')
        }
        this.last_check = new Date().getMinutes();
        this.darkModeCheck();
        useBus(bus, "RERENDER_MENU_BOOKMARK", this.rerenderMenuBookmark.bind(this));
    },
    rerenderMenuBookmark(){
        this.menuBookmark._unmount();
        this.menuBookmark.state.menus = session.infinitoMenuBookmarks;
        this.menuBookmark._mount();
    },
    mouseMove(ev){
        if(this.fullScreenEnabled && this.env.services.ui.size >= 4){
            if(ev.clientY <= 40){
                $(ev.target).parents('.o_action_manager').prev().find('nav').removeClass('d-none');
            } else {
                $(ev.target).parents('.o_action_manager').prev().find('nav').addClass('d-none');
            }
        }
        if(this.recentApps && this.env.services.ui.size >= 4){
            if (ev.clientY >= (screen.availHeight - 200)){
                $(this.recent.ref.el).removeClass('d-none');
            } else{
                $(this.recent.ref.el).addClass('d-none');
            }
        }
        if(session.infinitoBookmarks.length && session.infinitoBookmark && this.env.services.ui.size >= 4){
            if (ev.clientX >= (screen.availWidth - 160)){
                this.menuBookmark.el.classList.add('d-flex');
            } else {
                this.menuBookmark.el.classList.remove('d-flex');
            }
        }
        let now = new Date();
        if(this.last_check != now.getMinutes()){
            this.darkModeCheck();
            this.last_check = now.getMinutes();
        }
    },
    darkModeCheck(){
        if(session.infinitoDark){
            if(session.infinitoDarkMode == 'all'){
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
                if(startHour > endHour){
                    endHour += 24;
                    if(hour < startHour){
                        hour += 24;
                    }
                }
                if(endHour > hour && hour > startHour){
                    dark = true;
                } else if(hour == startHour && min >= startMin && hour < endHour){
                    dark = true;
                } else if(hour == endHour && min <= endMin && hour >= startHour){
                    dark = true;
                } else {
                    dark = false;
                }
                if(dark){
                    $('.o_web_client').addClass('dark-mode');
                    this.is_dark = true;
                } else {
                    $('.o_web_client').removeClass('dark-mode');
                    this.is_dark = false;
                }
            }
        } else if (!session.infinitoDark && this.is_dark){
            $('.o_web_client').removeClass('dark-mode');
            this.is_dark = false;
        }
    },
});

patch(MenuItem.prototype, 'backend_theme_infinito/static/src/js/navbar.MenuItem.js', {
    onClick(ev){
        this._super(ev);
        if(ev.target.classList.contains('o_app')){
            let app = {
                'appId': ev.target.dataset.section
            }
            ajax.jsonRpc('/theme_studio/add_recent_app', 'call', {app});
        }
    }
});

patch(ControlPanel.prototype, 'backend_theme_infinito/static/src/js/navbar.ControlPanel.js', {
    async onBookmark(ev){
        let action_id = this.props.action.id;
        let url = location.href.split('/');
        let menu_url = url[url.length - 1];
        if (!session.infinitoBookmarks.includes(action_id)) {
            let menu = {
                'actionId': action_id,
                'menuUrl': menu_url
            }
            let book = {
                name: $('.breadcrumb-item.active span').text(),
                short_name: $('.breadcrumb-item.active span').text().substring(0, 2).toUpperCase(),
                url: menu_url
            }
            await ajax.jsonRpc('/theme_studio/add_menu_bookmarks', 'call', {menu});
            ev.target.classList.add("active");
            session.infinitoBookmarks.push(action_id)
            session.infinitoMenuBookmarks.push(book);
        } else {
            let index = session.infinitoBookmarks.indexOf(action_id);
            session.infinitoBookmarks.splice(index, 1);
            session.infinitoMenuBookmarks.splice(index, 1);
            let menu = {
                'actionId': action_id
            }
            await ajax.jsonRpc('/theme_studio/remove_menu_bookmarks', 'call', {menu});
            ev.target.classList.remove("active");
        }
        bus.trigger("RERENDER_MENU_BOOKMARK");
    },

    mounted() {
        this._super();
        if(this.props.action && session.infinitoBookmark){
            let action_id = this.props.action.id;
            if (session.infinitoBookmarks.includes(action_id)) {
                this.el.querySelector('.btn-bookmark').classList.add("active");
            }
        }
    },

    get bookmarkOn(){
        return session.infinitoBookmark;
    }
});

if(session.infinitoChameleon){
    setInterval(()=>{
        let randomColor = colors[Math.floor(Math.random() * colors.length)];
        for(let key in variables){
            let index = variables[key][0] -1;
            let percentage = variables[key][1];
            document.documentElement.style.setProperty(key, to_color(randomColor[index], percentage))
        }
     }, 600000);
}