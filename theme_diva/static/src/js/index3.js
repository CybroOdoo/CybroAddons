        $(document).ready(function () {
            $("#slider2").owlCarousel(
                {

                    items: 3,
                    loop: true,
                    // margin: 30,
                    // stagePadding: 30,
                    smartSpeed: 450,
                    autoplay: true,
                    autoPlaySpeed: 1000,
                    autoPlayTimeout: 1000,
                    autoplayHoverPause: true,
                    // onInitialized: counter,
                    dots: true,
                    nav: true,
                    navText: ['<i class="bi bi-arrow-left-short"></i>    <span class="bi bi-arrow-left-circle"></span>', '<i class="bi bi-arrow-right-short"></i> <i class="bi bi-arrow-right-circle"></i>'],
                    animateOut: 'fadeOut',
                     responsive:{
                        0:{
                            items:1,
                            nav:true
                        },
                        600:{
                            items:2,
                            nav:false
                        },
                        1000:{
                            items:3,
                            nav:true,
                            loop:false
                        }
                    }

                }
            );
            $(".sustainable_wrapper").on({
            mouseover: function () {
                $(this).find("img:nth-child(1)").stop().animate({ opacity: 0 }, 600);
                $(this).find("img:nth-child(2)").stop().animate({ opacity: 1 }, 600);
            }, mouseout: function () {
                $(this).find("img:nth-child(1)").stop().animate({ opacity: 1 }, 600);
                $(this).find("img:nth-child(2)").stop().animate({ opacity: 0 }, 600);
            }
            });


        // function counter() {
        //     var buttons = $('.owl-dots button');
        //     buttons.each(function (item) {
        //         $(item).find('span').text(index + 1);
        //     });
        // }
            AOS.init({
            easing: 'ease-in-quad',
            });
        });

