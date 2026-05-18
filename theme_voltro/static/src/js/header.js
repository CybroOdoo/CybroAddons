/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.MenuOverflow = publicWidget.Widget.extend({
    selector: '#top_menu',

    /**
     * @override
     */
    start: function () {
        this._super.apply(this, arguments);

        const afterFontsloading = new Promise((resolve) => {
            if (document.fonts) {
                document.fonts.ready.then(resolve);
            } else {
                setTimeout(resolve, 150);
            }
        });

        afterFontsloading.then(() => {
            this._adapt();
        });

        this._resizeObserver = new ResizeObserver(() => {
            this._throttleAdapt();
        });
        this._resizeObserver.observe(this.el.parentElement);

        return Promise.resolve();
    },

    /**
     * @override
     */
    destroy: function () {
        if (this._resizeObserver) {
            this._resizeObserver.disconnect();
        }
        this._super.apply(this, arguments);
    },

    _throttleAdapt: function () {
        if (this._refreshId) {
            window.cancelAnimationFrame(this._refreshId);
        }
        this._refreshId = window.requestAnimationFrame(() => {
            this._adapt();
            this._refreshId = null;
        });
    },

    _adapt: function () {
        this._restore();
        if (window.matchMedia(`(max-width: 991px)`).matches) {
            return;
        }

        const items = [...this.el.children].filter(node => !node.classList.contains('o_extra_menu_items'));
        let nbItems = items.length;

        // User requirement: Only show 4 or 5 menus
        const MAX_ITEMS = 5;

        let menuItemsWidth = items.reduce((sum, el) => sum + this._computeOuterWidth(el), 0);
        let maxWidth = this.el.clientWidth || this.el.parentElement.clientWidth;

        // If we have more than MAX_ITEMS, or if they overflow the width
        if (nbItems <= MAX_ITEMS && maxWidth - menuItemsWidth >= -0.1) {
            return;
        }

        const dropdownMenu = this._addExtraItemsButton();
        menuItemsWidth += this._computeOuterWidth(this._extraItemsToggle);

        // Move items to dropdown if they exceed MAX_ITEMS OR if they overflow width
        while ((nbItems > MAX_ITEMS || maxWidth - menuItemsWidth < -0.1) && nbItems > 0) {
            const item = items[--nbItems];
            menuItemsWidth -= this._computeOuterWidth(item);
            item.classList.remove('nav-item');
            const link = item.querySelector('.nav-link');
            if (link) {
                link.classList.remove('nav-link');
                link.classList.add('dropdown-item');
            }
            dropdownMenu.insertBefore(item, dropdownMenu.firstChild);
        }
    },

    _restore: function () {
        if (!this._extraItemsToggle) {
            return;
        }
        const dropdownMenu = this._extraItemsToggle.querySelector('.dropdown-menu');
        [...dropdownMenu.children].forEach(item => {
            item.classList.add('nav-item');
            const link = item.querySelector('.dropdown-item');
            if (link) {
                link.classList.remove('dropdown-item');
                link.classList.add('nav-link');
            }
            this.el.insertBefore(item, this._extraItemsToggle);
        });
        this._extraItemsToggle.remove();
        this._extraItemsToggle = null;
    },

    _addExtraItemsButton: function () {
        if (this._extraItemsToggle) {
            return this._extraItemsToggle.querySelector('.dropdown-menu');
        }

        const li = document.createElement('li');
        li.className = 'nav-item dropdown o_extra_menu_items';

        const a = document.createElement('a');
        a.className = 'nav-link dropdown-toggle o-no-caret';
        a.href = '#';
        a.dataset.bsToggle = 'dropdown';
        a.innerHTML = '<i class="bi bi-plus-lg"></i>';

        const ul = document.createElement('ul');
        ul.className = 'dropdown-menu dropdown-menu-end';

        li.appendChild(a);
        li.appendChild(ul);

        this.el.appendChild(li);
        this._extraItemsToggle = li;

        return ul;
    },

    _computeOuterWidth: function (el) {
        const style = window.getComputedStyle(el);
        return el.offsetWidth + parseFloat(style.marginLeft) + parseFloat(style.marginRight);
    }
});
