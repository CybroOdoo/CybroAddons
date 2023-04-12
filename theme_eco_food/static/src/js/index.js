odoo.define('theme_eco_food.quantity', function(require){
    'use strict';

//    <!-- Navbar transition -->
        $(document).ready(function () {
            var s = $(".topbar");
            var pos = s.position();
            $('#wrapwrap').scroll(function () {
                var windowpos = $('#wrapwrap').scrollTop();
                if (windowpos >= pos.top & windowpos >= 100) {
                    s.addClass("fadeInDown");
                    s.addClass("topbar_margin");
                } else {
                    s.removeClass("fadeInDown");
                    s.removeClass("topbar_margin");
                }
            });
        });


//    <!-- Banner Carousels1 -->

$(document).ready(function () {
$(".featured_eco_food").owlCarousel(
                {
                    items: 1,
                    loop: true,
                    margin: 30,
                    stagePadding: 30,
                    smartSpeed: 450,
                    autoplay: true,
                    autoPlaySpeed: 1000,
                    autoPlayTimeout: 1000,
                    autoplayHoverPause: true,
                    dots: false,
                    nav: true,
                    responsiveClass: true,
                }
            );
        });

//    <!-- Banner Carousels1 -->
        const $slider = $('.my-slider')
        const SLIDER_TIMEOUT = 5000
        $slider.owlCarousel({
            items: 1,
            nav: false,
            dots: false,
            autoplay: true,
            autoplayTimeout: SLIDER_TIMEOUT,
            autoplayHoverPause: false,
            loop: true,
            onInitialized: ({ target }) => {
                const animationStyle = `-webkit-animation-duration:${SLIDER_TIMEOUT}ms;animation-duration:${SLIDER_TIMEOUT}ms`
                const progressBar = $(
                    `<div class="slider-progress-bar"><span class="progress" style="${animationStyle}"></span></div>`
                )
                $(target).append(progressBar)
            },
            onChanged: ({ type, target }) => {
                if (type === 'changed') {
                    const $progressBar = $(target).find('.slider-progress-bar')
                    const clonedProgressBar = $progressBar.clone(true)
                    $progressBar.remove()
                    $(target).append(clonedProgressBar)
                }
            }
        });
//    <!-- Banner carousel2 -->
        $(document).ready(function () {
            var owl = $('.owl-theme1');
            $(".owl-theme1").owlCarousel({});
            function setAnimation(_elem, _InOut) {
                var animationEndEvent = 'webkitAnimationEnd mozAnimationEnd MSAnimationEnd oanimationend animationend';
                _elem.each(function () {
                    var $elem = $(this);
                    var $animationType = 'animated ' + $elem.data('animation-' + _InOut);
                    $elem.addClass($animationType).one(animationEndEvent, function () {
                        $elem.removeClass($animationType); // remove animate.css Class at the end of the animations
                    });
                });
            }
            // Fired before current slide change
            owl.on('change.owl.carousel', function (event) {
                var $currentItem = $('.owl-item', owl).eq(event.item.index);
                var $elemsToanim = $currentItem.find("[data-animation-out]");
                setAnimation($elemsToanim, 'out');
            });
            // Fired after current slide has been changed
            owl.on('changed.owl.carousel', function (event) {
                var $currentItem = $('.owl-item', owl).eq(event.item.index);
                var $elemsToanim = $currentItem.find("[data-animation-in]");
                setAnimation($elemsToanim, 'in');
            })
        });

////    <!-- slider with thumb -->
        $(document).ready(function () {
            var bigimage = $("#big");
            var thumbs = $("#thumbs");
            //var totalslides = 10;
            var syncedSecondary = true;
            bigimage
                .owlCarousel({
                    items: 1,
                    slideSpeed: 2000,
                    margin: 30,
                    singleItem: true,
                    nav: false,
                    autoplay: false,
                    dots: false,
                    loop: true,
                    responsiveRefreshRate: 200,
                    responsive: {
                        0: {
                            items: 1,
                        },
                        768: {
                            items: 1,
                        },
                        992: {
                            items: 1,
                        }
                    },
                })
                .on("changed.owl.carousel", syncPosition);
            thumbs
                .on("initialized.owl.carousel", function () {
                    thumbs
                        .find(".owl-item")
                        .eq(0)
                        .addClass("current");
                })
                .owlCarousel({
                    items: 4,
                    dots: false,
                    nav: false,
                    responsive: {
                        0: {
                            items: 4,
                        },
                        768: {
                            items: 4,
                        },
                        992: {
                            items: 4,
                        }
                    },
                    smartSpeed: 200,
                    slideSpeed: 500,
                    slideBy: 3,
                    margin: 10,
                    responsiveRefreshRate: 100
                })
                .on("changed.owl.carousel", syncPosition2);
            function syncPosition(el) {
                //if loop is set to false, then you have to uncomment the next line
                //var current = el.item.index;
                //to disable loop, comment this block
                var count = el.item.count - 1;
                var current = Math.round(el.item.index - el.item.count / 2 - 0.5);
                if (current < 0) {
                    current = count;
                }
                if (current > count) {
                    current = 0;
                }
                //to this
                thumbs
                    .find(".owl-item")
                    .removeClass("current")
                    .eq(current)
                    .addClass("current");
                var onscreen = thumbs.find(".owl-item.active").length - 1;
                var start = thumbs
                    .find(".owl-item.active")
                    .first()
                    .index();
                var end = thumbs
                    .find(".owl-item.active")
                    .last()
                    .index();
                if (current > end) {
                    thumbs.data("owl.carousel").to(current, 100, true);
                }
                if (current < start) {
                    thumbs.data("owl.carousel").to(current - onscreen, 100, true);
                }
            }
            function syncPosition2(el) {
                if (syncedSecondary) {
                    var number = el.item.index;
                    bigimage.data("owl.carousel").to(number, 100, true);
                }
            }
            thumbs.on("click", ".owl-item", function (e) {
                e.preventDefault();
                var number = $(this).index();
                bigimage.data("owl.carousel").to(number, 300, true);
            });
        });
////    <!-- Quantity -->
        $(document).ready(function () {
        var ajax= require('web.ajax');
            $('.del-cart-eco-food').click(function(){
                var line_id = $(this).closest('.c_wrapper').find('.cart_line_id').val()
                var line = $(this).closest('.c_wrapper').hide()
                ajax.jsonRpc('/cart/del/my/product', 'call',{'line_id': line_id })
                .then(function (data) {
                    line.hide()
                });

            })

            const minus = $('.quantity-down');
            const plus = $('.quantity-up');
            minus.click(function (e) {
                e.preventDefault();
                var prev_total = $(this).closest('.row').find('.total .oe_currency_value')
                var unit_price = $(this).closest('.row').find('.p_one .oe_currency_value').text().replaceAll(',', '')
                var id = '#' + $(this).attr('id')
                var input = $('.quantity__input' + id);
                var value = input.val()
                if (value > 1) {
                    value--;
                    var line_id  = parseInt($(this).attr('id'))
                    ajax.jsonRpc('/cart_quantity_minus', 'call',{'line_id': line_id})
                    .then(function (data) {

                    });
                }

                var cur_total = value * parseFloat(unit_price)
                prev_total.text(update_line_total_price(cur_total))
                input.val(value);
                var subtotal = $('#cart-subtotal').find('.oe_currency_value')
                var sum = 0
                $(".c_wrapper .total").each(function(){
                    var line_total = $(this).find('.oe_currency_value').text().replaceAll(',', '')
                    sum += parseFloat(line_total)
                })
                subtotal.text(update_line_total_price(sum))


            });
            plus.click(function (e) {
                var prev_total = $(this).closest('.row').find('.total .oe_currency_value')
                var unit_price = $(this).closest('.row').find('.p_one .oe_currency_value').text().replaceAll(',', '')
                var id = '#' + $(this).attr('id')
                var input = $('.quantity__input' + id);
                var value = input.val()
                e.preventDefault();
                var value = input.val();
                value++;
                var line_id  = parseInt($(this).attr('id'))
                ajax.jsonRpc('/cart_quantity_plus', 'call',{'line_id': line_id})
                 .then(function (data) {});
                 var cur_total = value * parseFloat(unit_price)
                prev_total.text(update_line_total_price(cur_total))
                input.val(value);
                input.val(value);
            })
            function update_line_total_price(price){
                var total_price_text = price.toLocaleString()
                if ( total_price_text.split('.').length > 1 ){
                    if(total_price_text.split('.')[1].length < 2){
                        total_price_text += '0'
                    }
                }else{total_price_text += '.00'}
                return total_price_text
            }

            $('.o_add_wishlist').click(function () {
               $( "#my-nav-wish" ).load(window.location.href + " #my-nav-wish" );
            })
        });

////    <!-- New Arrival Slider -->
        $(document).ready(function () {
            $(".new_arrivel-carousel").owlCarousel(
                {
                    items: 6,
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
                        },
                        576: {
                            items: 2,
                        },
                        768: {
                            items: 3,
                        },
                        992: {
                            items: 6,
                        }
                    },
                }
            );
        });
////    <!-- Testimonial Slider -->
        $(document).ready(function () {
            $(".test-carousel").owlCarousel(
                {
                    items: 2,
                    loop: true,
                    margin: 40,
                    stagePadding: 0,
                    smartSpeed: 450,
                    autoplay: false,
                    autoPlaySpeed: 3000,
                    autoPlayTimeout: 1000,
                    autoplayHoverPause: true,
                    dots: false,
                    nav: false,
                    responsive: {
                        0: {
                            items: 1,
                        },
                        768: {
                            items: 2,
                        },
                        992: {
                            items: 2,
                        }
                    },
                }
            );
        });
////    <!-- Client Slider -->
        $(document).ready(function () {
            $(".client-carousel").owlCarousel(
                {
                    items: 5,
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
                }
            );
        });
});
