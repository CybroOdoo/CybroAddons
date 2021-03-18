(function () {
      var elements;
      var windowHeight;

      function init() {
        elements = document.querySelectorAll('.hidden');
        windowHeight = window.innerHeight;
      }

      function checkPosition() {
        for (var i = 0; i < elements.length; i++) {
          var element = elements[i];
          var positionFromTop = elements[i].getBoundingClientRect().top;

          if (positionFromTop - windowHeight <= 0) {
            element.classList.add('fade-in-element');
            element.classList.remove('hidden');
          }
        }
      }

      window.addEventListener('scroll', checkPosition);
      window.addEventListener('resize', init);

      init();
      checkPosition();
    })();
// <!-- heading animation -->


    (function () {
      var elements;
      var windowHeight;

      function init() {
        elements = document.querySelectorAll('.he');
        windowHeight = window.innerHeight;
      }

      function checkPosition() {
        for (var i = 0; i < elements.length; i++) {
          var element = elements[i];
          var positionFromTop = elements[i].getBoundingClientRect().top;

          if (positionFromTop - windowHeight <= 0) {
            element.classList.add('tracking-in-expand');
            element.classList.remove('he');
          }
        }
      }

      window.addEventListener('scroll', checkPosition);
      window.addEventListener('resize', init);

      init();
      checkPosition();
    })();





//  <!-- text animation -->


//  <script>
    (function () {
      var elements;
      var windowHeight;

      function init() {
        elements = document.querySelectorAll('.he');
        windowHeight = window.innerHeight;
      }

      function checkPosition() {
        for (var i = 0; i < elements.length; i++) {
          var element = elements[i];
          var positionFromTop = elements[i].getBoundingClientRect().top;

          if (positionFromTop - windowHeight <= 0) {
            element.classList.add('.animation-elementH , .animation-element');
            element.classList.remove('he');
          }
        }
      }

      window.addEventListener('scroll', checkPosition);
      window.addEventListener('resize', init);

      init();
      checkPosition();
    })();