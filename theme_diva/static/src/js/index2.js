$(document).ready(function () {
            $('#slide-testimonal').owlCarousel({
                margin: 0,
                center: true,
                loop: true,
                nav: false,
                center: true,
                lazyLoad: true,
                loop: true,
                smartSpeed: 450,
                autoplay: false,
                autoPlaySpeed: 1000,
                autoPlayTimeout: 1000,
                autoplayHoverPause: true,

                dots: true,
                responsiveClass: true,
                responsive: {
                    0: {
                        items: 1
                    },
                    768: {
                        items: 2,
                        margin: 15,
                    },
                    1000: {
                        items: 3,
                    }
                }
            });
            $("#owl-theme2").owlCarousel({
                items: 3,
                loop: true,
                margin: 30,
                stagePadding: 0,
                smartSpeed: 450,
                autoplay: false,
                lazyLoad: true,
                autoPlaySpeed: 1000,
                autoPlayTimeout: 1000,
                autoplayHoverPause: true,
                dots: false,
                nav: true,
                navText: ['<i class="fa fa-angle-left" aria-hidden="false"></i>', '<i class="fa fa-angle-right" aria-hidden="false"></i>'],
                responsiveClass: true,
                responsive: {
                    0: {
                        items: 1
                 },
                    768: {
                        items: 2
                    },
                    1000: {
                        items: 3
                    }
                }
            });

            $("#owl-theme3").owlCarousel({
                items: 1,
                loop: true,
                margin: 30,
                stagePadding: 0,
                smartSpeed: 450,
                autoplay: false,
                lazyLoad: true,
                autoPlaySpeed: 1000,
                autoPlayTimeout: 1000,
                autoplayHoverPause: true,
                dots: true,
                nav: false,
                navText: ['<i class="fa fa-angle-left" aria-hidden="true"></i>', '<i class="fa fa-angle-right" aria-hidden="true"></i>'],
            }
            );
            $("#owl-theme4").owlCarousel({
                items: 5,
                loop: true,
                margin: 30,
                stagePadding: 0,
                smartSpeed: 450,
                autoplay: false,
                lazyLoad: true,
                autoPlaySpeed: 1000,
                autoPlayTimeout: 1000,
                autoplayHoverPause: false,
                dots: false,
                nav: false,
                responsiveClass: true,
                responsive: {
                    0: {
                        items: 2
                    },
                    768: {
                        items: 3
                    },
                    1000: {
                        items: 4
                    }
                }
            });
 });
