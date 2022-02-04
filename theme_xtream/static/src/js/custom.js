    filterSelection("all")
    function filterSelection(c) {
        var x, i;
        x = document.getElementsByClassName("column");
        if (c == "all") c = "";
        for (i = 0; i < x.length; i++) {
            w3RemoveClass(x[i], "show");
            if (x[i].className.indexOf(c) > -1) w3AddClass(x[i], "show");
        }
    }
    function w3AddClass(element, name) {
        var i, arr1, arr2;
        arr1 = element.className.split(" ");
        arr2 = name.split(" ");
        for (i = 0; i < arr2.length; i++) {
            if (arr1.indexOf(arr2[i]) == -1) { element.className += " " + arr2[i]; }
        }
    }
    function w3RemoveClass(element, name) {
        var i, arr1, arr2;
        arr1 = element.className.split(" ");
        arr2 = name.split(" ");
        for (i = 0; i < arr2.length; i++) {
            while (arr1.indexOf(arr2[i]) > -1) {
                arr1.splice(arr1.indexOf(arr2[i]), 1);
            }
        }
        element.className = arr1.join(" ");
    }


    jQuery(document).ready(function () {
        // This button will increment the value
        $('.qtyplus').click(function (e) {
            // Stop acting like a button
            e.preventDefault();
            // Get the field name
            fieldName = $(this).attr('field');
            // Get its current value
            var currentVal = parseInt($('input[name=' + fieldName + ']').val());
            // If is not undefined
            if (!isNaN(currentVal)) {
                // Increment
                $('input[name=' + fieldName + ']').val(currentVal + 1);
            } else {
                // Otherwise put a 0 there
                $('input[name=' + fieldName + ']').val(0);
            }
        });
        // This button will decrement the value till 0
        $(".qtyminus").click(function (e) {
            // Stop acting like a button
            e.preventDefault();
            // Get the field name
            fieldName = $(this).attr('field');
            // Get its current value
            var currentVal = parseInt($('input[name=' + fieldName + ']').val());
            // If it isn't undefined or its greater than 0
            if (!isNaN(currentVal) && currentVal > 0) {
                // Decrement one
                $('input[name=' + fieldName + ']').val(currentVal - 1);
            } else {
                // Otherwise put a 0 there
                $('input[name=' + fieldName + ']').val(0);
            }
        });
    });

    $(document).ready(function () {
        $("#slider").owlCarousel(
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
        buttons.each(function (item) {
//          $(item).find('span').index + 1;
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
        buttons.each(function (item) {
            // $(item).find('span').text(index + 1);
        });
    }
