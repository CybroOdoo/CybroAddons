odoo.define('theme_watchhut.theme_watchhut_shop', function (require) {
	"use strict";
    $(".test").hover(function () {
        $(this).attr("src", "/theme_watchhut/static/src/images/product/1-1.jpg");
    },
        function () {
            $(this).attr("src", "/theme_watchhut/static/src/images/product/1.jpg");
        });
});