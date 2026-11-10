/** @odoo-module **/
import { ControlPanel } from "@web/search/control_panel/control_panel";
import { patch } from "@web/core/utils/patch";
import { rpc } from "@web/core/network/rpc";
import { session } from "@web/session";
import { router, stateToUrl } from "@web/core/browser/router";

const { onMounted, onPatched, useState, useRef } = owl;

patch(ControlPanel.prototype, {

    setup() {
        super.setup();
        onMounted(this.mounted.bind(this));
        onPatched(this._syncBookmarkClass.bind(this));
        this.infinitoState = useState({
            infinitoBookmarks: session.infinitoBookmarks || [],
            infinitoMenuBookmarks: session.infinitoMenuBookmarks || [],
            infinitoBookmarkColors: (session.infinitoBookmarks || []).map(() => '#ffc107'),
        });
        this.bookmarkRef = useRef('bookmark');
    },

    _isBookmarkFeatureEnabled() {
        const value = session.infinitoBookmark;
        return value === true || value === 1 || value === '1' || String(value).toLowerCase() === 'true';
    },

    _getCurrentActionId() {
        return (this.env.config && this.env.config.actionId) || (this.env.services.action && this.env.services.action.currentController && this.env.services.action.currentController.action && this.env.services.action.currentController.action.id);
    },

    _getCurrentMenuId() {
        const menuService = this.env.services.menu;
        if (!menuService) {
            return false;
        }
        const currentActionId = this._getCurrentActionId();
        const currentAction = currentActionId || (router.current && router.current.action);
        const currentApp = menuService.getCurrentApp && menuService.getCurrentApp();
        const menus = menuService.getAll ? menuService.getAll() : [];
        const actionMenu = menus.find(menu => (
            currentAction && (
                menu.actionPath === currentAction ||
                menu.actionID === currentAction
            )
        ));
        if (actionMenu) {
            return actionMenu.id;
        }
        const appMenu = currentActionId && currentApp && menus.find(menu => (
            menu.appID === currentApp.id && menu.actionID === currentActionId
        ));
        if (appMenu) {
            return appMenu.id;
        }
        return currentApp && currentApp.actionID === currentActionId ? currentApp.id : false;
    },

    _normalizeBookmarkUrl(url) {
        const cleanUrl = (url || '').trim();
        if (!cleanUrl) {
            return '';
        }
        return cleanUrl.length > 1 ? cleanUrl.replace(/\/$/, '') : cleanUrl;
    },

    _getCurrentBookmarkUrl() {
        if (router.current) {
            return this._normalizeBookmarkUrl(stateToUrl(router.current));
        }
        const pathname = location.pathname || '/web';
        const hash = pathname === '/web' ? location.hash : '';
        return this._normalizeBookmarkUrl(`${pathname}${hash}`);
    },

    _getCurrentBookmarkIndex() {
        const currentUrl = this._getCurrentBookmarkUrl();
        const currentMenuId = this._getCurrentMenuId();
        const currentActionId = this._getCurrentActionId();
        return this.infinitoState.infinitoMenuBookmarks.findIndex(bookmark => (
            (bookmark && bookmark.menu_id && bookmark.menu_id[0] === currentMenuId) ||
            (
                bookmark &&
                !bookmark.menu_id &&
                bookmark.url &&
                currentUrl &&
                this._normalizeBookmarkUrl(bookmark.url) === currentUrl
            ) ||
            (
                bookmark &&
                !bookmark.menu_id &&
                !bookmark.url &&
                bookmark.action_id &&
                bookmark.action_id[0] === currentActionId
            )
        ));
    },

    _isCurrentBookmark() {
        return this._getCurrentBookmarkIndex() !== -1;
    },

    async onBookmark(ev) {
        const targetButton = ev.target && ev.target.closest ? ev.target.closest('.btn-bookmark') : null;
        const bookmarkButton = ev.currentTarget || targetButton || this.bookmarkRef.el;
        let action_id = this._getCurrentActionId();
        if (!action_id) return;
        const menu_id = this._getCurrentMenuId();

        // Store the full pathname so the bookmark link navigates correctly.
        // e.g. /odoo/sales/products  (not just "products" which gives a 404)
        let menu_url = this._getCurrentBookmarkUrl();

        const isBookmarkedCurrently = this._isCurrentBookmark();

        if (!isBookmarkedCurrently) {
            const breadcrumbActive = document.querySelector('.breadcrumb-item.active');
            const breadcrumbText = breadcrumbActive ? breadcrumbActive.textContent.trim() : '';

            let menu = { 'actionId': action_id, 'menuId': menu_id, 'menuUrl': menu_url, 'name': breadcrumbText };

            let book = {
                name: breadcrumbText,
                short_name: breadcrumbText.substring(0, 2).toUpperCase(),
                action_id: [action_id, breadcrumbText],
                menu_id: menu_id ? [menu_id, breadcrumbText] : false,
                url: menu_url
            };

            await rpc('/theme_studio/add_menu_bookmarks', {
                method: 'call',
                args: { menu }
            });

            if (bookmarkButton) {
                bookmarkButton.classList.add("active");
            }
            this.infinitoState.infinitoBookmarks.push(action_id);
            this.infinitoState.infinitoMenuBookmarks.push(book);
            this.infinitoState.infinitoBookmarkColors.push('#ffc107');
            location.reload();
        } else {
            let index = this._getCurrentBookmarkIndex();
            if (index !== -1) {
                this.infinitoState.infinitoBookmarks.splice(index, 1);
                this.infinitoState.infinitoMenuBookmarks.splice(index, 1);
            }
            let menu = { 'actionId': action_id, 'menuId': menu_id, 'menuUrl': menu_url };

            await rpc('/theme_studio/remove_menu_bookmarks', {
                method: 'call',
                args: { menu }
            });

            if (bookmarkButton) {
                bookmarkButton.classList.remove("active");
            }
            location.reload();
        }
    },

    mounted() {
        this._syncBookmarkClass();
    },

    _syncBookmarkClass() {
        if (!this._isBookmarkFeatureEnabled() || !this.bookmarkRef.el) return;
        setTimeout(() => {
            if (!this.bookmarkRef.el) return;
            const isMarked = this._isCurrentBookmark();
            this.bookmarkRef.el.style.removeProperty('color');
            if (isMarked) {
                this.bookmarkRef.el.classList.add("active");
            } else {
                this.bookmarkRef.el.classList.remove("active");
            }
        }, 0);
    },

    get bookmarkOn() {
        if (!this._isBookmarkFeatureEnabled()) {
            return false;
        }
        const viewType = this.env.config && this.env.config.viewType;
        if (viewType === 'form') {
            return false;
        }
        const actionId = this._getCurrentActionId();
        return !!actionId;
    },

    get isBookmarked() {
        return this._isCurrentBookmark();
    },

    get bookmarkColor() {
        const idx = this._getCurrentBookmarkIndex();
        if (idx !== -1) {
            return this.infinitoState.infinitoBookmarkColors[idx] || '#ffc107';
        }
        return '#4f6bf8';
    },
    set bookmarkOn(value) { session.bookmarkOn = value; },
});
