        $(document).ready(function () {
            $(".img_lazy").ImgLazyLoad({
                mobile: "640",
                qhd: "1680",
                offset: "-150",
                time: "550",
                animateOut: 'img_lazy'
            });
        });

        // Detect request animation frame
        var scroll = window.requestAnimationFrame ||
            // IE Fallback
            function (callback) { window.setTimeout(callback, 1000 / 90) };
        var elementsToShow = document.querySelectorAll('.show-on-scroll');
        function loop() {
            Array.prototype.forEach.call(elementsToShow, function (element) {
                if (isElementInViewport(element)) {
                    element.classList.add('is-visible');
                }
            });
            scroll(loop);
        }
        // Call the loop for the first time
        loop();
        // Helper function from: http://stackoverflow.com/a/7557433/274826
        function isElementInViewport(el) {
            // special bonus for those using jQuery
            if (typeof jQuery === "function" && el instanceof jQuery) {
                el = el[0];
            }
            var rect = el.getBoundingClientRect();
            return (
                (rect.top <= 0
                    && rect.bottom >= 0)
                ||
                (rect.bottom >= (window.innerHeight || document.documentElement.clientHeight) &&
                    rect.top <= (window.innerHeight || document.documentElement.clientHeight))
                ||
                (rect.top >= 0 &&
                    rect.bottom <= (window.innerHeight || document.documentElement.clientHeight))
            );
        }


    // Detect request animation frame
    var scroll = window.requestAnimationFrame ||
      // IE Fallback
      function (callback) { window.setTimeout(callback, 1000 / 90) };
    var elementsToShow = document.querySelectorAll('.wrapp');
    function loop() {
      Array.prototype.forEach.call(elementsToShow, function (element) {
        if (isElementInViewport(element)) {
          element.classList.add('wrappit');
        }
      });
      scroll(loop);
    }
    // Call the loop for the first time
    loop();
    // Helper function from: http://stackoverflow.com/a/7557433/274826
    function isElementInViewport(el) {
      // special bonus for those using jQuery
      if (typeof jQuery === "function" && el instanceof jQuery) {
        el = el[0];
      }
      var rect = el.getBoundingClientRect();
      return (
        (rect.top <= 0
          && rect.bottom >= 0)
        ||
        (rect.bottom >= (window.innerHeight || document.documentElement.clientHeight) &&
          rect.top <= (window.innerHeight || document.documentElement.clientHeight))
        ||
        (rect.top >= 0 &&
          rect.bottom <= (window.innerHeight || document.documentElement.clientHeight))
      );
    }

    <!-- Nav -->
        var _gaq = _gaq || [];
        _gaq.push(['_setAccount', 'UA-36251023-1']);
        _gaq.push(['_setDomainName', 'jqueryscript.net']);
        _gaq.push(['_trackPageview']);
        (function () {
            var ga = document.createElement('script'); ga.type = 'text/javascript'; ga.async = true;
            ga.src = ('https:' == document.location.protocol ? 'https://ssl' : 'http://www') + '.google-analytics.com/ga.js';
            var s = document.getElementsByTagName('script')[0]; s.parentNode.insertBefore(ga, s);
        })();

        // When the user scrolls down 80px from the top of the document, resize the navbar's padding and the logo's font size
        window.onscroll = function () { scrollFunction() };
        function scrollFunction() {
            if (document.body.scrollTop > 80 || document.documentElement.scrollTop > 80) {
                document.getElementById("new").style.top = "0px";
            } else {
                document.getElementById("new").style.top = "205px";
            }
        }

    <!-- email validation -->

        function myFunction() {
            var email;
            email = document.getElementById("textEmail").value;
            var reg = /^([A-Za-z0-9_\-\.])+\@([A-Za-z0-9_\-\.])+\.([A-Za-z]{2,4})$/;
            if (reg.test(textEmail.value) == false) {
                document.getElementById("demo").style.color = "#535353";
                document.getElementById("demo").style.padding = "8px 0px";
                document.getElementById("demo").innerHTML = " The email you entered isn't valid.." + email;
                return false;
            } else {
                document.getElementById("demo").style.color = "#50449c";
                document.getElementById("demo").style.padding = "8px 0px";
                document.getElementById("demo").innerHTML = "<i class='fas fa-hand-point-right'></i> <strong>  WOOHOO</strong> You subscribed successfully.. " + email;
            }
            return true;
        }

    <!-- Footer collapse -->

        var acc = document.getElementsByClassName("accordion");
        var i;
        for (i = 0; i < acc.length; i++) {
            acc[i].addEventListener("click", function () {
                this.classList.toggle("active");
                var panel = this.nextElementSibling;
                if (panel.style.display === "block") {
                    panel.style.display = "none";
                } else {
                    panel.style.display = "block";
                }
            });
        }

    <!-- magnifier -->

        var mzOptions = {
            expand: 'fullscreen',
            rightClick: 'true',
            zoomOn: 'true',
            zoomMode: 'magnifier'
        };


        $('#zoom_05').ezPlus({
            zoomType: 'inner',
            cursor: 'crosshair'
        });

        $(document).ready(function () {
            var quantitiy = 0;
            $('.quantity-right-plus').click(function (e) {
                // Stop acting like a button
                e.preventDefault();
                // Get the field name
                var quantity = parseInt($('#quantity').val());
                // If is not undefined
                $('#quantity').val(quantity + 1);
                // Increment
            });
            $('.quantity-left-minus').click(function (e) {
                // Stop acting like a button
                e.preventDefault();
                // Get the field name
                var quantity = parseInt($('#quantity').val());
                // If is not undefined
                // Increment
                if (quantity > 0) {
                    $('#quantity').val(quantity - 1);
                }
            });
        });

        AOS.init({
            duration: 800,
            once: true
        });

    <!-- Preloader -->

        $(document).ready(function () {
            setTimeout(function () {
                $('#ctn-preloader').addClass('loaded');
                $('body').removeClass('no-scroll-y');
                if ($('#ctn-preloader').hasClass('loaded')) {
                    $('#preloader').delay(1000).queue(function () {
                        $(this).remove();
                    });
                }
            }, 3000);
        });


    <!-- Dynamic color changer -->


        const color1 = document.querySelector(".color1");
        const color2 = document.querySelector(".color2");
        const primaryColorInput = document.querySelector(".primaryColor");
        const secondarColorInput = document.querySelector(".secondoryColor"); //secondary
        const buttonColorInput = document.querySelector(".buttonColor"); //
        const footerColorInput = document.querySelector(".footerColor"); //
        let root = document.documentElement;


        eventSetter(color1, "input", (e) => { setPrimaryGradient( color1.value, color2.value) });
        eventSetter(color2, "input", (e) => { setPrimaryGradient( color1.value, color2.value) });
        eventSetter(primaryColorInput, "input", (e) => { setSolidColor( '--primar-color', primaryColorInput.value) });
        eventSetter(secondarColorInput, "input", (e) => { setSolidColor( '--secondary-color', secondarColorInput.value) });
        eventSetter(buttonColorInput, "input", (e) => { setSolidColor( '--button-color', buttonColorInput.value) });
        eventSetter(footerColorInput, "input", (e) => { setSolidColor( '--footer-color', footerColorInput.value) });
        // attching setSolidColor function for 'input' event on secondarColorInput element


        //event listnet add helper
        function eventSetter(el, event, fn) {
            el.addEventListener(event, fn);
        }

        function setPrimaryGradient( color1, color2) {
            let root = document.documentElement;
            root.style.setProperty('--primar-gradient-color-one', color1);
            root.style.setProperty('--primar-gradient-color-two', color2);
        };

        //solid color setter
        function setSolidColor(cssProperty, color) {
            let root = document.documentElement;
            root.style.setProperty(cssProperty, color)
        }




<!-- Change Direction -->


document.getElementById('directionSwitch').addEventListener('click', function() {
  var docDirection = document.documentElement.dir;
  var isRTL = (docDirection === 'rtl');
  document.documentElement.dir = isRTL ? 'ltr' : 'rtl';

});

