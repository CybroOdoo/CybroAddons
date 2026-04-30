/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";
const BREAKPOINT_SIZES = { sm: "575", md: "767", lg: "991", xl: "1199", xxl: "1399" };
publicWidget.registry.MenuOverflow = publicWidget.Widget.extend({
    selector: 'header#top .top_menu', // ADJUST THIS SELECTOR TO MATCH YOUR MENU

    /**
     * @override
     */
    start: function () {
        this._super.apply(this, arguments);
        // Wait for fonts and images to load before calculating widths
        const afterFontsloading = new Promise((resolve) => {
            if (document.fonts) {
                document.fonts.ready.then(resolve);
            } else {
                setTimeout(resolve, 150);
            }
        });

        // Initial adaptation
        afterFontsloading.then(() => this._adapt());

        // Adapt on window resize
        this._resizeObserver = new ResizeObserver(() => this._throttleAdapt());
        this._resizeObserver.observe(this.el.parentElement);
        this._resizeObserver.observe(this.el);

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
    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------
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
        // 1. Restore any previously hidden items
        this._restore();
        // 2. Check if we need to hide items (e.g. not on mobile)
        // You might need to adjust this condition based on your theme's mobile breakpoint
        if (window.matchMedia(`(max-width: 991px)`).matches) {
            return;
        }
        // 3. Calculate available space vs required space
        const items = [...this.el.children].filter(node => !node.classList.contains('o_extra_menu_items'));
        let nbItems = items.length;

        // Calculate total width of all items
        let menuItemsWidth = items.reduce((sum, el) => sum + this._computeOuterWidth(el), 0);

        // Calculate max available width
        // This assumes the parent container constrains the width
        let maxWidth = this.el.clientWidth;
        // Or if the menu itself doesn't have a fixed width, check its parent
        if (!maxWidth) {
             maxWidth = this.el.parentElement.clientWidth;
        }
        // 4. If no overflow, we are done
        if (maxWidth - menuItemsWidth >= -0.1) {
            return;
        }
        // 5. Create the "+" dropdown if needed
        const dropdownMenu = this._addExtraItemsButton();

        // Add width of the "+" button itself
        menuItemsWidth += this._computeOuterWidth(this._extraItemsToggle);
        // 6. Move items to the dropdown until they fit
        while (maxWidth - menuItemsWidth < -0.1 && nbItems > 0) {
            const item = items[--nbItems];
            menuItemsWidth -= this._computeOuterWidth(item);

            // Move item to dropdown
            // Adjust classes for dropdown context
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
        // Move items back to the main menu
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
        a.innerHTML = '<i class="fa fa-plus"></i>'; // Using FontAwesome plus icon

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