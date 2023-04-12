$(document).ready(function() {
  var fixHeight = function() {
    $('.navbar-nav').css(
      'max-height',
      document.documentElement.clientHeight 
    );
  };
  fixHeight();
  $(window).resize(function() {
    fixHeight();
  });
  $('.navbar .navbar-toggler').on('click', function() {
    fixHeight();
  });
  $('.navbar-toggler, .overlay').on('click', function() {
    $('.mobileMenu, .overlay').toggleClass('open');
  });
});

// 