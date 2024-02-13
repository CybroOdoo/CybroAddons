/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.CustomerReviewProduct = publicWidget.Widget.extend({
    /**
     * The  methods defined here are used for adding the comments and rating at
     * the time of confirmation of orders and different styles were applied at
     * the time of occurrence of some events like button click, mouseout etc.
     */
    selector: '.master',
    events: {
        'mouseover .rating-component .star': '_ReviewHover',
        'mouseout .rating-component .star': '_ReviewOut',
        'click .rating-component .stars-box .star': '_SubmitReview',
        'click .compliment-container .fa-smile-wink': '_SubmitCompliment',
        'click .feedback-tags': '_SubmitFeedBack',
    },
    _ReviewHover: function (ev) {
        var onStar = parseInt($(ev.target).data("value"), 10);
        var children = this.$el[0].querySelector(".stars-box").children
        $(children).each(function (e) {
             if (e < onStar){
                    $(ev.target)[0].classList.add("hover");
             }
        })
    },
    _ReviewOut : function(e) {
        var children = this.$el[0].querySelector(".stars-box").children
        for (var i = 0; i < children.length; i++) {
            $(e.target)[0].classList.remove("hover");
        }
    },
    _SubmitReview : function (e) {
        var onStar = parseInt($(e.target).data("value"), 10);
        var stars = $(e.target).parent().children(".star");
        var ratingMessage = $(e.target).data("message");
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
        for (var i = 0; i < onStar; i++) {
            $(stars[i]).addClass("selected");
        }
        for (var i = 0; i > stars.length; i++) {
            $(stars[i]).removeClass("selected");
        }
        $(".status-msg .rating_msg").val(ratingMessage);
        $(".status-msg").html(ratingMessage);
        $("[data-tag-set]").hide();
        $("[data-tag-set=" + onStar + "]").show();
    },
    _SubmitCompliment  : function () {
        $(this).fadeOut("slow", function () {
                $(".list-of-compliment").fadeIn();
            });
    },
    _SubmitFeedBack : function (e) {
        var chosenTagsLength = $(e.target).parent("div.tags-box").find("input").length + 1;
        if ($(e.target).hasClass("chosen")) {
            $(e.target).removeClass("chosen");
            chosenTagsLength = chosenTagsLength - 2;
        } else {
            $(e.target).addClass("chosen");
            $(".button-box .done").removeAttr("disabled");
        }
        if (chosenTagsLength <= 0) {
            $(".button-box .done").attr("enabled", "false");
        }
    },
});
