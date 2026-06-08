/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

const ReviewNotification = publicWidget.Widget.extend({
    selector: '.order_comment_template',
    events: {
        'mouseover .star': '_onMouseoverRating',
        'mouseout .star': '_onMouseOutRating',
        'click .star': 'onClickStar',
        'click .feedback-tags': 'onClickFeedback',
        'click .done': 'onClickDone'
    },
    /**
     * The methods defined here are used for adding the comments and rating at
     * the time of confirmation of orders and different styles were applied at
     * the time of occurrence of some events like button click, mouseout etc.
     */
    _onMouseoverRating: function (ev) {
        var onStar = parseInt(ev.currentTarget.getAttribute("value"), 10);
        this.$(".star").each(function (e) {
            if (e < onStar) {
                $(this).addClass("hover");
            } else {
                $(this).removeClass("hover");
            }
        });
    },
    /**
    while mouse out remove the class "hover"
    */
    _onMouseOutRating: function (ev) {
        this.$(".star").each(function (e) {
            $(this).removeClass("hover");
        });
    },
    /**
    selecting the clicked star and enabling submit if rating >= 1
    */
    onClickStar: function (event) {
        var onStar = parseInt(event.currentTarget.getAttribute("value"), 10);
        var stars = this.$(".star");
        var ratingMessage = event.currentTarget.getAttribute("data-message");
        this.$('.rating-component .star-rate .rate-value').val(onStar);
        this.$(".button-box .done").show();
        // Enable done button for any star rating
        this.$(".button-box .done").removeAttr("disabled");
        for (var i = 0; i < stars.length; i++) {
            stars[i].classList.remove("selected");
        }
        for (var i = 0; i < onStar; i++) {
            stars[i].classList.add("selected");
        }
        this.$(".status-msg .rating_msg").val(ratingMessage);
        this.$(".status-msg").html(ratingMessage);
        this.$("[data-tag-set]").hide();
        this.$("[data-tag-set=" + onStar + "]").show();
    },
    /**
    click feedback section changing the style
    */
    onClickFeedback: function (event) {
        var chosenTagsLength = this.$(".tags-box").find("input").length + 1;
        if (this.$(event.currentTarget).hasClass("chosen")) {
            this.$(event.currentTarget).removeClass("chosen");
            chosenTagsLength = chosenTagsLength - 2;
        } else {
            this.$(event.currentTarget).addClass("chosen");
            this.$(".button-box .done").removeAttr("disabled");
        }
        if (chosenTagsLength <= 0) {
            this.$(".button-box .done").attr("enabled", "false");
        }
    },
    /**
    Submit the form when the done button is clicked
    */
    onClickDone: function (event) {
        event.preventDefault();
        var self = this;
        var rateValue = this.$('.rate-value').val();
        var comment = this.$('input[name="comment"]').val() || '';
        var orderId = this.$('#order_id').val();

        // Validate required fields
        if (!rateValue || !orderId) {
            return;
        }

        // Show loading state
        this.$(".rating-component").hide();
        this.$(".feedback-tags").hide();
        this.$(".button-box").hide();
        this.$(".submitted-box").show();
        this.$(".submitted-box .loader").show();

        // Submit the form
        var form = this.el.querySelector('form');
        if (form) {
            form.submit();
        }
    }
});

publicWidget.registry.my_account_screen = ReviewNotification;
export default ReviewNotification;