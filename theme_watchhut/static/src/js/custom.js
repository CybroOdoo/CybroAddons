/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";
/**
 * Created ScrollAnimation widget
 * To make available the animation opacity affect on the snippet gallery on
   scrolling the window here added event wheel effect to achieve the animation
 **/
publicWidget.registry.ScrollAnimation = publicWidget.Widget.extend({
    selector: '.images',
    events: {
        'wheel': 'onScroll',
    },
    // In start function called the function onScroll();
    start: function() {
        this.onScroll();
    },
    /**This function is triggered whenever window is scrolled
        image variable stores images with class .inline-photo
        and check in isElementInViewport(args) function
    **/
    onScroll: function() {
         var images = document.querySelectorAll('.inline-photo');
         function loop() {
              Array.prototype.forEach.call(images, function (element) {
                    if (isElementInViewport(element)) {
                      element.classList.add('is-visible');
                    } else {
                      element.classList.remove('is-visible');
                    }
              });
          scroll(loop);
        }
    loop();
    /**  This function called from each scroll checking each picture
         present in the viewport and if present it is made visible
    **/
    function isElementInViewport(el) {
          var rect = el.getBoundingClientRect();
          return (
            (rect.top <= 0
              && rect.bottom >= 0)
            ||
            (rect.bottom >= (window.innerHeight || document.documentElement.clientHeight) &&
              rect.top <= (window.innerHeight || document.documentElement.clientHeight))
            ||
            (rect.top >= 0 &&
              rect.bottom <= (window.innerHeight || document.documentElement.clientHeight))
          );
    }
    },
});
export default publicWidget.registry.ScrollAnimation;
