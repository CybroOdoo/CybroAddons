/** @odoo-module */
import PublicWidget from "@web/legacy/js/public/public_widget"
// Extend the PublicWidget.Widget class to create a new widget for the theme
export const themeIndex = PublicWidget.Widget.extend({
// Set the selector to the element with id 'wrapwrap', which is the main container of the page
    selector: "#wrapwrap",
    // Define the events to be handled by the widget
    events: {
        'scroll': '_handleScroll',
    },
    // The 'start' method is called when the widget is initialized
    start(){
        this.counters = this.$el;
    },
    // Method to handle the scroll event
    _handleScroll: function () {
        var counters = this.$el.find('.number')
        const speed = 1000;// Define the speed for counting animation


      const animateCounters = () => {
        // Iterate over each counter element
        counters.each((key,counter) => {
          const updateCount = () => {
            const target = +$(counter).attr("data-target");
            const count = +$(counter).text();
            const increment = target / speed;

            if (count < target) {
              counter.innerText = Math.ceil(count + increment);
              setTimeout(updateCount, 200);
            } else {
              $(counter).text(target);
            }
          };

          updateCount();// Call the 'updateCount' function to start the counting animation
        });
      };
    // Get the current scroll position plus the window height
    const scrollPosition = window.scrollY + window.innerHeight;
    counters.each((key,counter) => {
      const counterPosition = counter.offsetTop + counter.clientHeight / 2;
      if (scrollPosition >= counterPosition) {
        animateCounters();
      }
    });
    },
 })
 // Register the widget so it can be used on the website
 PublicWidget.registry.themeIndex = themeIndex

