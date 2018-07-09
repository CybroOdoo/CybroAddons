odoo.define('point_of_sale.pos_chatter', function (require) {
"use strict";
var chrome = require('point_of_sale.chrome');
var core = require('web.core');
var chat_manager = require('mail.chat_manager');
var window_manager = require('mail.window_manager');
var ajax = require('web.ajax');
var gui = require('point_of_sale.gui');
var popup = require('point_of_sale.popups');
var PosBaseWidget = require('point_of_sale.BaseWidget');
var QWeb = core.qweb;
var _t = core._t;

chrome.Chrome.include({
    events: {
            "click .pos-message": "on_click_pos_message",
        },
    renderElement: function(){
        var self = this;
        this.filter = false;
        chat_manager.bus.on("update_channel_unread_counter", this, this.update_counter);
        chat_manager.is_ready.then(this.update_counter.bind(this));
        return this._super();
    },

    is_open: function () {
        return this.$el.hasClass('open');
    },

    update_counter: function () {
        var counter = chat_manager.get_unread_conversation_counter();
        this.$('.o_notification_counter').text(counter);
        this.$el.toggleClass('o_no_notification', !counter);
        this.$el.toggleClass('o_unread_chat', !!chat_manager.get_chat_unread_counter());
        if (this.is_open()) {
            this.update_channels_preview();
        }
    },

    update_channels_preview: function () {
        var self = this;
        chat_manager.is_ready.then(function () {
            var channels = _.filter(chat_manager.get_channels(), function (channel) {
                if (self.filter === 'chat') {
                    return channel.is_chat;
                } else if (self.filter === 'channels') {
                    return !channel.is_chat && channel.type !== 'static';
                } else {
                    return channel.type !== 'static';
                }
            });
            chat_manager.get_channels_preview(channels).then(self._render_channels_preview.bind(self));
        });
    },

    _render_channels_preview: function (channels_preview) {
        channels_preview.sort(function (c1, c2) {
            return Math.min(1, c2.unread_counter) - Math.min(1, c1.unread_counter) ||
                   c2.is_chat - c1.is_chat ||
                   c2.last_message.date.diff(c1.last_message.date);
        });

        _.each(channels_preview, function (channel) {
            channel.last_message_preview = chat_manager.get_message_body_preview(channel.last_message.body);
            if (channel.last_message.date.isSame(new Date(), 'd')) {  // today
                channel.last_message_date = channel.last_message.date.format('LT');
            } else {
                channel.last_message_date = channel.last_message.date.format('lll');
            }
        });
        this.gui.show_popup('message',{list:channels_preview});
    },

    on_click_pos_message: function () {
        var self = this;
        if (this.gui.current_popup) {
            this.gui.close_popup();
        }
        else{
             this.update_channels_preview();
        }
    },

    on_click_new_message: function () {
            chat_manager.bus.trigger('open_chat');
        },

});


var MessageWidget = PosBaseWidget.extend({
    template:'MessageWidget',
    events: {
            "click .o_mail_channel_preview": "on_click_message_item",
            "click .pos-new_message": "on_click_new_message",
            "click .pos-filter": "on_click_filter",
        },
    renderElement: function(){
        var self = this;
        return this._super();
    },
    show: function(options){
        options = options || {};
        var self = this;
        this._super(options);
        this.list    = options.list    || [];
        this.renderElement();

    },
    on_click_new_message: function () {
        this.gui.close_popup();
        chat_manager.bus.trigger('open_chat');
        },

    on_click_filter: function (event) {
        event.stopPropagation();
        this.$(".pos-filter").removeClass('pos-selected');
        var $target = $(event.currentTarget);
        $target.addClass('pos-selected');
        this.filter = $target.data('filter');
        this.update_channels_preview();
    },

    update_channels_preview: function () {
        var self = this;
        this.$('.o_mail_navbar_dropdown_channels').html(QWeb.render('Spinner'));
         chat_manager.is_ready.then(function () {
            var channels = _.filter(chat_manager.get_channels(), function (channel) {
                if (self.filter === 'chat') {
                    return channel.is_chat;
                } else if (self.filter === 'channels') {
                    return !channel.is_chat && channel.type !== 'static';
                } else {
                    return channel.type !== 'static';
                }
            });
            chat_manager.get_channels_preview(channels).then(self._render_channels_preview.bind(self));
        });
    },

    _render_channels_preview: function (channels_preview) {

    channels_preview.sort(function (c1, c2) {
        return Math.min(1, c2.unread_counter) - Math.min(1, c1.unread_counter) ||
               c2.is_chat - c1.is_chat ||
               c2.last_message.date.diff(c1.last_message.date);
    });

    _.each(channels_preview, function (channel) {
        channel.last_message_preview = chat_manager.get_message_body_preview(channel.last_message.body);
        if (channel.last_message.date.isSame(new Date(), 'd')) {  // today
            channel.last_message_date = channel.last_message.date.format('LT');
        } else {
            channel.last_message_date = channel.last_message.date.format('lll');
        }
    });
    this.$('.o_mail_navbar_dropdown_channels').html(QWeb.render('mail.chat.ChannelsPreview', {
                channels: channels_preview,
            }));
},

    close: function(){
        if (this.$el) {
            this.$el.addClass('oe_hidden');
        }
    },

    on_click_message_item: function(event){
        event.stopPropagation();
        var $target = $(event.currentTarget);
        var channel_id = $target.data('channel_id');
        var channel = chat_manager.get_channel(channel_id);
            if (channel) {
                this.gui.close_popup();
                chat_manager.open_channel(channel);
            }
    },
});

gui.define_popup({name:'message', widget: MessageWidget});


});
