odoo.define('all_in_one_website_kit.customer_order_comment', function(require) {
    'use strict';
    var PublicWidget = require('web.public.widget');
    var Template = PublicWidget.Widget.extend({
        selector: '.order_comment_template',
        events: {
            'mouseover .star': '_onMouseoverRating',
            'mouseout .star': '_onMouseOutRating',
            'click .star': 'onClickStar',
            'click .feedback-tags': 'onClickFeedback',
            'click .done': 'onClickDone'
        },
        /**
         * The  methods defined here are used for adding the comments and rating at
         * the time of confirmation of orders and different styles were applied at
         * the time of occurrence of some events like button click, mouseout etc.
         */
        _onMouseoverRating: function(ev) {
            var onStar = parseInt(ev.currentTarget.getAttribute("value"), 10);
            this.$(".star").each(function(e) {
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
        _onMouseOutRating: function(ev) {
            this.$(".star").each(function(e) {
                $(this).removeClass("hover");
            })
        },
        /**
        selecting the clicked star
        */
        onClickStar: function(event) {
            var onStar = parseInt(event.currentTarget.getAttribute("value"), 10);
            var stars = this.$(".star");
            var ratingMessage = event.currentTarget.getAttribute("data-message")
            this.$('#order_id').val($('.monetary_field').data('oe-id'))
            this.$('.rating-component .star-rate .rate-value').val(onStar);
            this.$(".fa-smile-wink").show();
            this.$(".button-box .done").show();
            if (onStar === 5) {
                this.$(".button-box .done").removeAttr("disabled");
            } else {
                this.$(".button-box .done").attr("disabled", "true");
            }
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
        onClickFeedback: function(event) {
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
        changing the style while clicking on done button
        */
        onClickDone: function(event) {
            this.$(".rating-component").hide();
            this.$(".feedback-tags").hide();
            this.$(".button-box").hide();
            this.$(".submitted-box").show();
            this.$(".submitted-box .loader").show();
            setTimeout(function() {
                this.$(".submitted-box .loader").hide();
                this.$(".submitted-box .success-message").show();
            }, 1500);
        }
    });
    PublicWidget.registry.my_account_screen = Template;
    return Template;
})