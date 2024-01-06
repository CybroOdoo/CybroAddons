odoo.define('website_scroll_buttons.scroll_button', function(require){
    "use strict"
    /* In the function check the document height and set the visibility for buttons
    when the scroll bar move from scrollTop. And add click function for scroll bar
    move from top to bottom and bottom to top.*/
    var PublicWidget = require('web.public.widget');
    var Template = PublicWidget.Widget.extend({
        selector: '.website_scroll_buttons',
        events: {
            'click .scroll_to_bottom': '_onClickScrollBottom',
            'click .scroll_to_top': '_onClickScrollTop'
        },
        /*Start function is for check the conditions for showing the buttons.*/
        start: function(){
           if (this.$target.closest('#wrapwrap')[0].scrollHeight > window.innerHeight){
            var self = this
            this.$target.closest('#wrapwrap').scroll(function() {
            if (self.$target.closest(this).scrollTop() > window.innerHeight*0.1){
            self.$el.find(".scroll_icon_bottom").show();
             self.$el.find(".scroll_icon").show();
            }
            })
           }
        },
        /*Click on button, it move to bottom of the screen*/
        _onClickScrollBottom: function(){
            this.$target.closest('body').animate({
                scrollTop: this.$target.closest(document).height()*10
           }, 2000);
        },
        /*Click on button, it move to top screen*/
        _onClickScrollTop: function(){
            this.$target.closest('body').animate({
                scrollTop: 0
            }, 400);
        },
    })
    PublicWidget.registry.website_scroll_buttons = Template;
    return Template;
})
