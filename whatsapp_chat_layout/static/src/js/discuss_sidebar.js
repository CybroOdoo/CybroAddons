odoo.define('whatsapp_chat_layout.discuss_sidebar', function(require) {
    'use strict';
    const { onMounted } = owl.hooks;
    var rpc = require('web.rpc');
    const components = { DiscussSidebar: require('mail/static/src/components/discuss_sidebar/discuss_sidebar.js')};
    const { patch } = require('web.utils');
    /**
    Patching the components. DiscussSidebar for changing the default view
    */
    patch(components.DiscussSidebar, 'im_livechat/static/src/components/discuss_sidebar/discuss_sidebar.js', {
        setup() {
            this._super.apply();
            onMounted(() => {
                this.sidebar()
            })
        },
        // Function for getting the current user image
        async sidebar() {
            var self = this
            //Call rpc to get current user image.
            await rpc.query({
                model: "res.users",
                method: "get_user_image",
            }).then(function(result) {
                let image = document.createElement('div')
                image.innerHTML = '<img class="o_Composer_currentPartner rounded-circle o_object_fit_cover"style="margin-top: 21px;margin-left: 10px;width: 45px;height: 45px;"src="data:image/png;base64,' + result + '">'
                self.el.querySelector('#img').appendChild(image);
            });
        },
        // Click function of mail button
        _onClickMail(ev) {
            console.log(this)
            this.el.querySelector('.mail').classList.remove("d-none");
            this.el.querySelector('.channel').classList.add("d-none");
            this.el.querySelector('.chat').classList.add("d-none");
        },
         // Click function of chat button
        _onClickChat(ev) {
            this.el.querySelector('.chat').classList.remove("d-none");
            this.el.querySelector('.mail').classList.add("d-none");
            this.el.querySelector('.channel').classList.add("d-none");
        },
         // Click function of channel button
        _onClickChannel(ev) {
            this.el.querySelector('.channel').classList.remove("d-none");
            this.el.querySelector('.mail').classList.add("d-none");
            this.el.querySelector('.chat').classList.add("d-none");
        }
    });
});
