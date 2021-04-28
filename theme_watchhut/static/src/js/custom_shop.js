odoo.define('theme_watchhut.theme_watchhut_shop', function (require) {
	"use strict";
	console.log("WatchHut Shop code working")

//    $(window).scroll(function(){
//        $(".banner").css("opacity", 1 - $(window).scrollTop() / 250);
//    });

//    filterSelection("all")
//    function filterSelection(c) {
//        var x, i;
//        x = document.getElementsByClassName("column");
//        if (c == "all") c = "";
//        for (i = 0; i < x.length; i++) {
//            w3RemoveClass(x[i], "show");
//            if (x[i].className.indexOf(c) > -1) w3AddClass(x[i], "show");
//        }
//    }
//    function w3AddClass(element, name) {
//        var i, arr1, arr2;
//        arr1 = element.className.split(" ");
//        arr2 = name.split(" ");
//        for (i = 0; i < arr2.length; i++) {
//            if (arr1.indexOf(arr2[i]) == -1) { element.className += " " + arr2[i]; }
//        }
//    }
//    function w3RemoveClass(element, name) {
//        var i, arr1, arr2;
//        arr1 = element.className.split(" ");
//        arr2 = name.split(" ");
//        for (i = 0; i < arr2.length; i++) {
//            while (arr1.indexOf(arr2[i]) > -1) {
//                arr1.splice(arr1.indexOf(arr2[i]), 1);
//            }
//        }
//        element.className = arr1.join(" ");
//    }
//    // Add active class to the current button (highlight it)
//    var btnContainer = document.getElementById("myBtnContainer");
//    var btns = btnContainer.getElementsByClassName("btn");
//    for (var i = 0; i < btns.length; i++) {
//        btns[i].addEventListener("click", function () {
//            var current = document.getElementsByClassName("active");
//            current[0].className = current[0].className.replace(" active", "");
//            this.className += " active";
//        });
//    }


    $(".test").hover(function () {
        $(this).attr("src", "/theme_watchhut/static/src/images/product/1-1.jpg");
    },
        function () {
            $(this).attr("src", "/theme_watchhut/static/src/images/product/1.jpg");
        });

//    $(".test1").hover(function () {
//        $(this).attr("src", "/theme_watchhut/static/src/images/product/2-2.jpg");
//    },
//
//        function () {
//            $(this).attr("src", "/theme_watchhut/static/src/images/product/2.jpg");
//        });
//
//    $(".test2").hover(function () {
//        $(this).attr("src", "/theme_watchhut/static/src/images/product/3-3.jpg");
//    },
//
//        function () {
//            $(this).attr("src", "/theme_watchhut/static/src/images/product/3.jpg");
//        });
//
//    $(".test3").hover(function () {
//        $(this).attr("src", "/theme_watchhut/static/src/images/product/4-4.jpg");
//    },
//
//        function () {
//            $(this).attr("src", "/theme_watchhut/static/src/images/product/4.jpg");
//        });
//
//    $(".test4").hover(function () {
//        $(this).attr("src", "/theme_watchhut/static/src/images/product/5-5.jpg");
//    },
//
//        function () {
//            $(this).attr("src", "/theme_watchhut/static/src/images/product/5.jpg");
//        });
//
//    $(".test5").hover(function () {
//        $(this).attr("src", "/theme_watchhut/static/src/images/product/6-6.jpg");
//    },
//
//        function () {
//            $(this).attr("src", "/theme_watchhut/static/src/images/product/6.jpg");
//        });
//
//    $(".test6").hover(function () {
//        $(this).attr("src", "/theme_watchhut/static/src/images/product/7-7.jpg");
//    },
//
//        function () {
//            $(this).attr("src", "/theme_watchhut/static/src/images/product/7.jpg");
//        });
//
//    $(".test7").hover(function () {
//        $(this).attr("src", "/theme_watchhut/static/src/images/product/8-8.jpg");
//    },
//        function () {
//            $(this).attr("src", "/theme_watchhut/static/src/images/product/8.jpg");
//        });
//        $(".test8").hover(function () {
//        $(this).attr("src", "/theme_watchhut/static/src/images/product/9-9.jpg");
//    },
//        function () {
//            $(this).attr("src", "/theme_watchhut/static/src/images/product/9.jpg");
//        });
});