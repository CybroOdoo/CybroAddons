odoo.define('theme_the_chef.theme_the_chef', function (require) {
  $(document).ready(function () {
    $("#slider").owlCarousel(
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
        navText: ['<i class="fa fa-angle-left"></i>', '<i class="fa fa-angle-right"></i>']
      }
    );
  });
  function counter() {
    var buttons = $('.owl-dots button');
    buttons.each(function (index, item) {
      $(item).find('span').text(index + 1);
    });
  }

  $(document).ready(function () {
    $("#slider2").owlCarousel(
      {
        // animateOut: 'slideOutDown',
        // animateIn: 'flipInX',
        items: 1,
        loop: true,
        // margin: 30,
        // stagePadding: 30,
        smartSpeed: 450,
        autoplay: true,
        autoPlaySpeed: 1000,
        autoPlayTimeout: 1000,
        autoplayHoverPause: true,
        onInitialized: counter,
        dots: true,
      }
    );
  });
  function counter() {
    var buttons = $('.owl-dots button');
    buttons.each(function (index, item) {
      $(item).find('span').index + 1;
    });
  }

  var inputEle = document.getElementById('timeInput');


  function onTimeChange() {
    var timeSplit = inputEle.value.split(':'),
      hours,
      minutes,
      meridian;
    hours = timeSplit[0];
    minutes = timeSplit[1];
    if (hours > 12) {
      meridian = 'PM';
      hours -= 12;
    } else if (hours < 12) {
      meridian = 'AM';
      if (hours == 0) {
        hours = 12;
      }
    } else {
      meridian = 'PM';
    }
    alert(hours + ':' + minutes + ' ' + meridian);
  }
});