odoo.define('theme_autofly.theme.js', function (require) {
'use strict';
    var flag = 0;
    $(document).ready(function () {
        var sticker = $(".sticker");
        $('#wrapwrap').scroll(function () {
            if (($('#wrapwrap').scrollTop() >= sticker.position().top) & ($('#wrapwrap').scrollTop() >= 100)) {
                sticker.addClass("fadeInDown");
                sticker.addClass("bg_white");
                sticker.addClass("b_shadow");
            } else {
                sticker.removeClass("fadeInDown");
                sticker.removeClass("bg_white");
                sticker.removeClass("b_shadow");
            }
        });
    });
    $(document).ready(function () {
            $(".owl-theme1").owlCarousel(
                {
                    items: 3,
                    loop: true,
                    margin: 40,
                    stagePadding: 0,
                    smartSpeed: 450,
                    autoplay: false,
                    autoPlaySpeed: 3000,
                    autoPlayTimeout: 1000,
                    autoplayHoverPause: true,
                    dots: false,
                    nav: true,
                    responsive: {
            0: {
              items: 1,
              nav: false,
            },
            600: {
              items: 2,
              nav: false,
            },
            1000: {
              items: 3,
              nav: true,
              loop: false,
            },
          },
                }
            );
        });
        $('#wrapwrap').scroll(function () {
            if(!$("#counter-box").length > 0) return;
            if (flag == 0 && $(window).scrollTop() > $("#counter-box").offset().top - window.innerHeight) {
                $(".counter").each(function () {
                    var $this = $(this),
                        countTo = $this.attr("data-number");
                    $({
                        countNum: $this.text()
                    }).animate(
                        {
                            countNum: countTo
                        },
                        {
                            duration: 5000,
                            easing: "swing",
                            step: function () {
                                $this.text(
                                    Math.ceil(this.countNum).toLocaleString("en")
                                );
                            },
                            complete: function () {
                                $this.text(
                                    Math.ceil(this.countNum).toLocaleString("en")
                                );
                            }
                        }
                    );
                });
                flag = 1;
            }
        });
});