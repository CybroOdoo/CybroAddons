    $(document).ready(function () {
      $(".owl-carousel").owlCarousel(
        {
          // animateOut: 'slideOutDown',
          // animateIn: 'flipInX',
          items: 1,
          loop: true,
          margin: 0,
          stagePadding: 0,
          smartSpeed: 450,
          autoplay: true,
          autoPlaySpeed: 1000,
          autoPlayTimeout: 1000,
          autoplayHoverPause: true,
          onInitialized: counter,
          dots: true,
          nav: true,
          navText: ['<i class="fa fa-angle-left" aria-hidden="false"></i>', '<i class="fa fa-angle-right" aria-hidden="false"></i>'],
          animateOut: 'fadeOut'
        }
      );
    });
    function counter() {
      var buttons = $('.owl-dots button');
      buttons.each(function (index, item) {
        // $(item).find('span').text(index + 1);
      });
    }


