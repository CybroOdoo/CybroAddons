odoo.define('product_360_degree_view_in_website.product_360_degree_view', function (require) {
    'use strict';
    var publicWidget = require('web.public.widget');
    var rpc = require('web.rpc');
    var pic_W = $('.list').width() / 2;
    var center_X = 0 + pic_W;
    var movestop = pic_W / 10;

    publicWidget.registry.product_view = publicWidget.Widget.extend({
        selector: '.360_degree_view',
        events: {
            'mousemove.list': 'Move360Image',
            'click .360_view': '_360ViewClick',
            'click .stop_view': '_stopViewClick',

        },
        setup: function () {
//        Calling the moveImg function
            this._super.apply(this, arguments);
            this.moveImg();
        },
        // Function for calculating the movements of the picture
        moveImg: function (m_X, m_Y, dir) {
            var index = Math.ceil(Math.abs(m_X - center_X) / movestop);
            if (dir) {
                this.$el.find('.list li').eq(index).show().siblings().hide();
            } else {
                this.$el.find('.list li').eq(18 - index).show().siblings().hide();
            }
        },
        // Mousemove of the image
        Move360Image: function (ev) {
            var mouse_X = ev.pageX;
            var mouse_Y = ev.pageY;
            if (mouse_X - center_X <= 0) {
                this.moveImg(mouse_X, mouse_Y, 'left');
            } else {
                this.moveImg(mouse_X, mouse_Y);
            }
        },
        // Click function of the image to change the 360 degree
        _360ViewClick: function (ev) {
            this.$el.find('.carousel-inner, .product_detail_img').css({ 'display': 'none' });
            this.$el.find('#image_360').css({ 'display': 'block' });
            this.$el.find('.360_view').addClass('d-none'); // Hide the 360 view button
            this.$el.find('.stop_view').removeClass('d-none'); // Show the stop button
        },
//        Function for the button stop
        _stopViewClick: function (ev) {
            this.$el.find('#image_360').css({ 'display': 'none' });
            this.$el.find('.product_detail_img').css({ 'display': 'block' });
            this.$el.find('.stop_view').addClass('d-none'); // Hide the stop button
            this.$el.find('.360_view').removeClass('d-none'); // Show the 360 view button
        },
    });
});
