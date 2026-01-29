odoo.define('theme_watchhut.theme_watchhut_shop', function (require) {
	"use strict";
	   /**
     * Handles the hover effect on the "test" element.
     */
    $(".test").hover(function () {
        $(this).attr("src", "/theme_watchhut/static/src/images/product/1-1.jpg");
    },
    /**
         * Mouse enter handler: Changes the image source on hover.
         */
        function () {
            $(this).attr("src", "/theme_watchhut/static/src/images/product/1.jpg");
        });
});
