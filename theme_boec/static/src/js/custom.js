odoo.define('theme_boec.theme_boec', function (require) {
	"use strict";

    $(document).ready(function () {

        //Preloader//
        setTimeout(function () {
            $('body').addClass('loaded');
        }, 1000);

        //Banner Slider//
        $(".owl-carousel").owlCarousel({
            items: 1,
            loop: true,
            margin: 0,
            stagePadding: 0,
            smartSpeed: 450,
            autoplay: false,
            autoPlaySpeed: 1000,
            autoPlayTimeout: 1000,
            autoplayHoverPause: true,
            onInitialized: counter,
            dots: true,
            nav: true,
            navText: ['<div class="pre"><i class="material-icons" style="font-size:36px">keyboard_arrow_left</i></div>', '<div class="nxt"><i class="material-icons" style="font-size:36px">keyboard_arrow_right</i></div>'],
            animateOut: 'fadeOut'
        });

        function counter() {
            var buttons = $('.owl-dots button');
            buttons.each(function (index, item) {
                $(item).find('span').text(index + 1);
            });
        }

        //add another class for banner_added
        var banner = $(".banner_added");
        var banner_id = banner.data("id");
        $("div").addClass(banner_id);
        banner.addClass("banner_hide");

        //tab Heading Boarder//
        $(".nav-link").click(function () {
            var value = $(this).attr('data-filter');
            if (value == "all") {
                $('.filter').show('1000');
            }else {
                $(".filter").not('.' + value).hide('3000');
                $('.filter').filter('.' + value).show('3000');
            }
        });
        if ($(".nav-link").removeClass("active")) {
            $(this).removeClass("active");
        }
        $(this).addClass("active");
    });

    var url = window.location;
    // Will only work if string in href matches with location
    $('ul.navbar-nav a[href="'+ url +'"]').parent().addClass('active');

    // Will also work for relative and absolute hrefs
    $('ul.navbar-nav a').filter(function() {
        return this.href == url;
    }).parent().addClass('active');

    // Add active class to the current button in Navbar (highlight it)
    var header = document.getElementById("myDIV");
    var btns = header.getElementsByClassName("nav-link");
    for (var i = 0; i < btns.length; i++) {
      btns[i].addEventListener("click", function () {
        var current = document.getElementsByClassName("active");
        current[0].className = current[0].className.replace(" active", "");
        this.className += " active";
      });
    }

    //Add active class to the current button (highlight it)
    var header = document.getElementById("myDIV");
    var btns = header.getElementsByClassName("btn");
    for (var i = 0; i < btns.length; i++) {
      btns[i].addEventListener("click", function () {
        var current = document.getElementsByClassName("active");
        if (current.length > 0) {
          current[0].className = current[0].className.replace(" active", "");
        }
        this.className += " active";
      });
    }

    //spinner jquery--quantity
    jQuery('<div class="quantity-nav"><div class="quantity-button quantity-up">+</div><div class="quantity-button quantity-down">-</div></div>').insertAfter('.quantity input');
    jQuery('.quantity').each(function () {
      var spinner = jQuery(this),
        input = spinner.find('input[type="number"]'),
        btnUp = spinner.find('.quantity-up'),
        btnDown = spinner.find('.quantity-down'),
        min = input.attr('min'),
        max = input.attr('max');
      btnUp.click(function () {
        var oldValue = parseFloat(input.val());
        if (oldValue >= max) {
          var newVal = oldValue;
        } else {
          var newVal = oldValue + 1;
        }
        spinner.find("input").val(newVal);
        spinner.find("input").trigger("change");
      });
      btnDown.click(function () {
        var oldValue = parseFloat(input.val());
        if (oldValue <= min) {
          var newVal = oldValue;
        } else {
          var newVal = oldValue - 1;
        }
        spinner.find("input").val(newVal);
        spinner.find("input").trigger("change");
      });
    });

    //shop jquery--card head
    $('.card-header').click(function () {
      $(this).find('i').toggleClass('fas fa-angle-down  	fas fa-angle-up');
    });

    //Tab
    $("#tile-1 .nav-tabs a").click(function () {
      var position = $(this).parent().position();
      var width = $(this).parent().width();
//      $("#tile-1 .slider").css({ "left": + position.left, "width": width });
    });
    var actWidth = $("#tile-1 .nav-tabs").find(".active").parent("li").width();
    var actPosition = $("#tile-1 .nav-tabs .active").position();
//    $("#tile-1 .slider").css({ "left": + actPosition.left, "width": actWidth });
});