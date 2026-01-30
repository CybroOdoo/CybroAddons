/** @odoo-module */
import PublicWidget from "@web/legacy/js/public/public_widget";
// Extend the PublicWidget.Widget class to create a new widget for the theme
export const themeIndex = PublicWidget.Widget.extend({
// Set the selector to the element with id 'wrapwrap', which is the main container of the page
    selector: "#wrapwrap",
    // Define the events to be handled by the widget

    /**
     * @override
     */
    // The 'start' method is called when the widget is initialized

    start() {
        this._super(...arguments);
        this.counters = this.$el.find('.number');
        this._setupIntersectionObserver();
        return Promise.resolve();
    },

    /**
     * Sets up the Intersection Observer to watch counter elements
     * @private
     */
    _setupIntersectionObserver() {
        const options = {
            root: null, // use viewport
            rootMargin: '0px',
            threshold: 0.5 // trigger when 50% of element is visible
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting && !entry.target.dataset.animated) {
                    this._animateCounter(entry.target);
                }
            });
        }, options);

        // Observe each counter element
        this.counters.each((_, counter) => {
            observer.observe(counter);
        });
    },

    /**
     * Animates a single counter element
     * @private
     * @param {HTMLElement} counter - The counter element to animate
     */
    _animateCounter(counter) {
        const speed = 10;
        const $counter = $(counter);
        const target = +$counter.attr("data-target");
        const increment = target / speed;

        counter.dataset.animated = 'true';  // Mark as animated

        const updateCounter = (currentValue) => {
            if (currentValue < target) {
                const nextValue = Math.ceil(currentValue + increment);
                counter.innerText = nextValue;
                setTimeout(() => updateCounter(nextValue), 200);
            } else {
                counter.innerText = target;
            }
        };

        updateCounter(0);// Call the 'updateCounter' function to start the counting animation
    },

    /**
     * @override
     */
    destroy() {
        this._super(...arguments);
        // Clean up observer if widget is destroyed
        if (this.observer) {
            this.observer.disconnect();
        }
    }
});

// Register the widget
PublicWidget.registry.themeIndex = themeIndex;
