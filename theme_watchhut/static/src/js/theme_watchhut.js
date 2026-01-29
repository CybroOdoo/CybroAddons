odoo.define('theme_watchhut.theme_watchhut', function (require) {
	"use strict";
    $(window).scroll(function(){
      $(".banner").css("opacity", 1 - $(window).scrollTop() / 250);
    });
    /**
     * Handles the banner opacity change as the user scrolls.
     */
    // Detect request animation frame
    var scroll = window.requestAnimationFrame ||
      // IE Fallback
      function (callback) { window.setTimeout(callback, 1000 / 90) };
    var elementsToShow = document.querySelectorAll('.show-on-scroll');
      /**
     * Handles the visibility of elements as the user scrolls.
     */
    function loop() {
      Array.prototype.forEach.call(elementsToShow, function (element) {
        if (isElementInViewport(element)) {
          element.classList.add('is-visible');
        } else {
          element.classList.remove('is-visible');
        }
      });
      scroll(loop);
       /**
     * Checks if an element is within the viewport.
     * @param {HTMLElement} el - The HTML element to check.
     * @returns {boolean} True if the element is in the viewport, false otherwise.
     */
    }
    // Call the loop for the first time
    loop();
    // Helper function from: http://stackoverflow.com/a/7557433/274826
    function isElementInViewport(el) {
      // special bonus for those using jQuery
      if (typeof jQuery === "function" && el instanceof jQuery) {
        el = el[0];
      }
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
     /**
     * Handles filtering of items on button click.
     */
    $(document).ready(function () {
      $(".filter-button").click(function () {
        var value = $(this).attr('data-filter');
        if (value == "all") {
          $('.filter').show('1000');
        }
        else {
          $(".filter").not('.' + value).hide('3000');
          $('.filter').filter('.' + value).show('3000');
        }
      });
      if ($(".filter-button").removeClass("active")) {
        $(this).removeClass("active");
      }
      $(this).addClass("active");
    });
       /**
     * Sets opacity for certain banners on scroll.
     */
    $(window).scroll(function(){
        $(".banner_about, .banner_contact").css("opacity", 1 - $(window).scrollTop() / 250);
    });
    $(window).scroll(function () {
        $(".banner_contact").css("opacity", 1 - $(window).scrollTop() / 250);
    });
    /**
     * Handles quantity increase and decrease functionality.
     */
    $(document).ready(function(){
        var quantitiy=0;
        $('.quantity-right-plus').click(function(e){
            // Stop acting like a button
            e.preventDefault();
            // Get the field name
            var quantity = parseInt($('#quantity').val());
            // If is not undefined
            $('#quantity').val(quantity + 1);
            // Increment
        });
        $('.quantity-left-minus').click(function(e){
            // Stop acting like a button
            e.preventDefault();
            // Get the field name
            var quantity = parseInt($('#quantity').val());
            // If is not undefined
            // Increment
            if(quantity>0){
                $('#quantity').val(quantity - 1);
            }
        });
    });
});
