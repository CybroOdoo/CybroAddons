/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";
publicWidget.registry.Scroll_button = publicWidget.Widget.extend({
    selector: '.website_scroll_buttons',
    events: {
       'click .scroll_to_bottom': '_onClickScrollBottom',
       'click .scroll_to_top': '_onClickScrollTop'
    },
    start(){
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
    _onClickScrollBottom(){
            this.$target.closest('body').animate({
                scrollTop: this.$target.closest(document).height()*10
           }, 2000);
    },
        /*Click on button, it move to top screen*/
    _onClickScrollTop(){
            this.$target.closest('body').animate({
                scrollTop: 0
            }, 400);
    },
})
