   <script>
        $(document).ready(function () {
            $(".owl-theme2").owlCarousel(
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
                    nav: false,
                    responsive: {
                        0: {
                            items: 1,
                            nav: false
                        },
                        600: {
                            items: 2,
                            nav: false
                        },
                        1000: {
                            items: 3,
                            nav: true,
                            loop: false
                        }
                    }
                }
            );
        });
    </script>