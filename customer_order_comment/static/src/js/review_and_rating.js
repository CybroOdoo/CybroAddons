odoo.define('customer_order_comment.review_and_rating', function(require){
    'use strict';

    /**
     * The  methods defined here are used for adding the comments and rating at
     * the time of confirmation of orders and different styles were applied at
     * the time of occurrence of some events like button click, mouseout etc.
     */

    $(".rating-component .star").on("mouseover", function () {
        var onStar = parseInt($(this).data("value"), 10);
        $(this).parent().children("i.star").each(function (e) {
            if (e < onStar) {
                $(this).addClass("hover");
            } else {
                $(this).removeClass("hover");
            }
        });

    }).on("mouseout", function () {
        $(this).parent().children("i.star").each(function (e) {
            $(this).removeClass("hover");
        });
    });

    $(".rating-component .stars-box .star").on("click", function () {
        var onStar = parseInt($(this).data("value"), 10);
        var stars = $(this).parent().children("i.star");
        var ratingMessage = $(this).data("message");
        $('#order_id').val($('.monetary_field').data('oe-id'))
        var msg = onStar;
        $('.rating-component .star-rate .rate-value').val(msg);
        $(".fa-smile-wink").show();
        $(".button-box .done").show();
        if (onStar === 5) {
            $(".button-box .done").removeAttr("disabled");
        } else {
            $(".button-box .done").attr("disabled", "true");
        }
        for (var i = 0; i < stars.length; i++) {
            $(stars[i]).removeClass("selected");
        }
        for (var i = 0; i < onStar; i++) {
            $(stars[i]).addClass("selected");
        }
        $(".status-msg .rating_msg").val(ratingMessage);
        $(".status-msg").html(ratingMessage);
        $("[data-tag-set]").hide();
        $("[data-tag-set=" + onStar + "]").show();
    });

    $(".feedback-tags  ").on("click", function () {
        var chosenTagsLength = $(this).parent("div.tags-box").find("input").length + 1;
        if ($(this).hasClass("chosen")) {
            $(this).removeClass("chosen");
            chosenTagsLength = chosenTagsLength - 2;
        } else {
            $(this).addClass("chosen");
            $(".button-box .done").removeAttr("disabled");
        }
        if (chosenTagsLength <= 0) {
            $(".button-box .done").attr("enabled", "false");
        }
    });

    $(".compliment-container .fa-smile-wink").on("click", function () {
        $(this).fadeOut("slow", function () {
            $(".list-of-compliment").fadeIn();
        });
    });

    $(".done").on("click", function () {
        $(".rating-component").hide();
        $(".feedback-tags").hide();
        $(".button-box").hide();
        $(".submitted-box").show();
        $(".submitted-box .loader").show();
        setTimeout(function () {
            $(".submitted-box .loader").hide();
            $(".submitted-box .success-message").show();
        }, 1500);
    });
});