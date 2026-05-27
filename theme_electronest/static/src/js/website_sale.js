/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";

publicWidget.registry.websiteSaleOffcanvasCustom = publicWidget.Widget.extend({
    selector: '#o_wsale_offcanvas',
    events: {
        'show.bs.offcanvas': '_toggleFilters',
        'hidden.bs.offcanvas': '_toggleFilters',
        'shown.bs.offcanvas': '_onOffcanvasShown',
        'hide.bs.offcanvas': '_onOffcanvasHide',
    },

    //--------------------------------------------------------------------------
    // Private./assets/img/images
    //--------------------------------------------------------------------------

    /**
     * Setup custom animations and interactions
     * @private
     */
    _setupAnimations: function () {
        // Add smooth scrolling to accordion items
        this._addSmoothScrolling();

        // Setup filter type data attributes
        this._setupFilterTypes();

        // Initialize price range sliders if present
        this._initializePriceSliders();
    },

    /**
     * Add smooth scrolling behavior
     * @private
     */
    _addSmoothScrolling: function () {
        if (this.el) {
            this.el.style.scrollBehavior = 'smooth';
        }
    },

    /**
     * Setup filter type data attributes for styling
     * @private
     */
    _setupFilterTypes: function () {
        if (!this.el) return;

        const accordionItems = this.el.querySelectorAll('.custom-accordion-item');
        accordionItems.forEach(item => {
            const button = item.querySelector('.custom-accordion-button b');
            if (button) {
                const filterText = button.textContent.toLowerCase().trim();
                if (filterText.includes('categor')) {
                    item.setAttribute('data-filter-type', 'category');
                } else if (filterText.includes('price')) {
                    item.setAttribute('data-filter-type', 'price');
                } else if (filterText.includes('tag')) {
                    item.setAttribute('data-filter-type', 'tags');
                } else {
                    item.setAttribute('data-filter-type', 'attribute');
                }
            }
        });
    },

    /**
     * Initialize custom price range sliders
     * @private
     */
    _initializePriceSliders: function () {
        if (!this.el) return;

        const priceSliders = this.el.querySelectorAll('input[type="range"]');
        priceSliders.forEach(slider => {
            this._updateSliderBackground(slider);
            slider.addEventListener('input', () => {
                this._updateSliderBackground(slider);
            });
        });
    },

    /**
     * Update slider background to show progress
     * @private
     * @param {HTMLElement} slider
     */
    _updateSliderBackground: function (slider) {
        const min = slider.min || 0;
        const max = slider.max || 100;
        const value = slider.value;
        const percentage = ((value - min) / (max - min)) * 100;

        slider.style.setProperty('--value', percentage + '%');
    },

    /**
     * Add stagger animation to accordion items
     * @private
     */
    _addStaggerAnimation: function () {
        if (!this.el) return;

        const items = this.el.querySelectorAll('.custom-accordion-item');
        items.forEach((item, index) => {
            item.style.animationDelay = (index * 0.1) + 's';
            item.classList.add('animate-in');
        });
    },

    /**
     * Remove stagger animation
     * @private
     */
    _removeStaggerAnimation: function () {
        if (!this.el) return;

        const items = this.el.querySelectorAll('.custom-accordion-item');
        items.forEach(item => {
            item.classList.remove('animate-in');
            item.style.animationDelay = '';
        });
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * Called when widget is started
     */
    start: function () {
        this._setupAnimations();
        return this._super.apply(this, arguments);
    },

    /**
     * Unfold active filters, fold inactive ones
     * @private
     * @param {Event} ev
     */
    _toggleFilters: function (ev) {
        if (!this.el) return;

        for (const btn of this.el.querySelectorAll('button[data-status]')) {
            if(btn.classList.contains('collapsed') && btn.dataset.status == "active" ||
               !btn.classList.contains('collapsed') && btn.dataset.status == "inactive") {
                btn.click();
            }
        }
    },

    /**
     * Handle offcanvas shown event
     * @private
     * @param {Event} ev
     */
    _onOffcanvasShown: function (ev) {
        // Add entrance animation
        this._addStaggerAnimation();

        // Focus management for accessibility
        const firstFocusable = this.el?.querySelector('button, input, select, textarea, a[href]');
        if (firstFocusable) {
            firstFocusable.focus();
        }

        // Initialize any dynamic content
        this._initializePriceSliders();

        // Add backdrop blur effect
        this._addBackdropEffect();
    },

    /**
     * Handle offcanvas hide event
     * @private
     * @param {Event} ev
     */
    _onOffcanvasHide: function (ev) {
        // Remove animations
        this._removeStaggerAnimation();

        // Remove backdrop effect
        this._removeBackdropEffect();
    },

    /**
     * Add backdrop blur effect
     * @private
     */
    _addBackdropEffect: function () {
        const backdrop = document.querySelector('.offcanvas-backdrop');
        if (backdrop) {
            backdrop.style.backdropFilter = 'blur(5px)';
            backdrop.style.backgroundColor = 'rgba(0, 0, 0, 0.3)';
        }
    },

    /**
     * Remove backdrop blur effect
     * @private
     */
    _removeBackdropEffect: function () {
        const backdrop = document.querySelector('.offcanvas-backdrop');
        if (backdrop) {
            backdrop.style.backdropFilter = '';
            backdrop.style.backgroundColor = '';
        }
    },
});

// Additional widget for enhanced filter interactions
publicWidget.registry.customFilterInteractions = publicWidget.Widget.extend({
    selector: '.custom-list-item',
    events: {
        'mouseenter': '_onMouseEnter',
        'mouseleave': '_onMouseLeave',
        'click input[type="checkbox"], input[type="radio"]': '_onFilterChange',
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * Handle mouse enter for enhanced hover effects
     * @private
     * @param {Event} ev
     */
    _onMouseEnter: function (ev) {
        const item = ev.currentTarget;
        item.style.transform = 'translateX(4px)';
        item.style.transition = 'all 0.2s ease';
    },

    /**
     * Handle mouse leave
     * @private
     * @param {Event} ev
     */
    _onMouseLeave: function (ev) {
        const item = ev.currentTarget;
        item.style.transform = '';
    },

    /**
     * Handle filter change with visual feedback
     * @private
     * @param {Event} ev
     */
    _onFilterChange: function (ev) {
        const input = ev.target;
        const item = input.closest('.custom-list-item');

        if (input.checked) {
            item.style.backgroundColor = 'rgba(0, 123, 255, 0.08)';
            item.style.borderRadius = '8px';
            item.style.margin = '0 -0.5rem';
            item.style.padding = '0.5rem 0.5rem';

            // Add a subtle pulse animation
            item.style.animation = 'pulse 0.3s ease-out';
            setTimeout(() => {
                item.style.animation = '';
            }, 300);
        } else {
            item.style.backgroundColor = '';
            item.style.borderRadius = '';
            item.style.margin = '';
            item.style.padding = '0.5rem 0';
        }
    },
});

publicWidget.registry.WebsiteSaleLayout = publicWidget.Widget.extend({
    selector: '.oe_website_sale',
    disabledInEditableMode: false,
    events: {
        'click .o_wsale_apply_layout input': '_onApplyShopLayoutChange',
    },

    init() {
        this._super(...arguments);
        this.orm = this.bindService("orm");
        this.currentLayoutMode = "grid";
    },

    async willStart() {
        await this._super(...arguments);
        this.currentLayoutMode = await this.orm.call('website', 'get_shop_product_layout', []);
    },

    start() {
        this._updateLayoutActiveClasses(this.currentLayoutMode);
        return this._super(...arguments);
    },

    _updateLayoutActiveClasses(layoutMode) {
        const gridLabel = this.el.querySelector('label[for="o_wsale_apply_grid"]');
        const listLabel = this.el.querySelector('label[for="o_wsale_apply_list"]');
        const activeClass = this.el.querySelector('.o_wsale_apply_layout')?.dataset.activeClasses || 'active';
        if (!gridLabel || !listLabel) {
            return;
        }
        gridLabel.classList.toggle(activeClass, layoutMode !== 'list');
        listLabel.classList.toggle(activeClass, layoutMode === 'list');
    },

    async _onApplyShopLayoutChange(ev) {
        const clickedValue = ev.target.value;
        this._updateLayoutActiveClasses(clickedValue);
        await this.orm.call('website', 'set_shop_product_layout', [clickedValue]);
        window.location.reload();
    },
});
