openerp.send_message_direct_composer = function (session) {
    var mail = session.mail;
    mail.ThreadComposeMessage = mail.ThreadComposeMessage.extend({
        bind_events: function () {
                var self = this;
                this._super();
                this.$('.oe_compose_post').on('click', _.bind( this.on_compose_fullmail, this, this.id ? 'reply' : 'comment'));
            },
    });
};