/** @odoo-module **/
import { Component, useState, mount } from "@odoo/owl";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { patch } from "@web/core/utils/patch";
var Dialog = require('web.Dialog');
var core = require('web.core');
var QWeb = core.qweb;
var rpc = require('web.rpc');
var _t = core._t;

//patching the menu items
patch(DropdownItem.prototype, "menu_lock", {
    //onclick function of menu item
    async onClick(ev) {
        var _super = this._super;
        ev.preventDefault()
        var session = require('web.session');
        var userId = session.uid;
        var currentMenu = this.props.dataset.section
        //rpc query to get values about password lock from res.users
        await rpc.query({
            model: 'res.users',
            method: 'menu_lock_search',
            args: [
                [userId]
            ],
        }).then(function(data) {
            //checking the current menu in menus to lock
            var menu = data.multi_lock_ids.filter(obj => {
                return parseInt(obj.id) === parseInt(currentMenu)
            })
            //if current menu is lock menu
            if (menu.length != 0 && menu[0].id && menu[0].password) {
                //Open dialog box to login
                var dialog = new Dialog(this, {
                    title: "Menu Security PIN",
                    $content: $(QWeb.render('menuLockPopup', {
                        role: 'alert',
                    })),
                    size: 'medium',
                    buttons: [{
                            text: _t("confirm"),
                            classes: 'btn-primary check_password',
                            click: false,
                        },
                        {
                            text: _t("Cancel"),
                            close: true
                        },
                    ],
                });
                dialog.opened().then(() => {
                    //show and hide the password on click of eye icon.
                    dialog.$el.find('.toggle_eye').click(function(){
                        var securityPin = dialog.$el.find('#password')[0];
                        if (securityPin.type === "password") {
                            securityPin.type = "text";
                        } else {
                            securityPin.type = "password";
                        }
                    })
                    //dialog box confirm button function, if matches
                    //successfully logins to the menu, otherwise show error warning.
                    dialog.buttons[0].click = function(event) {
                        var current_pwd = dialog.$el.find('#password').val()
                        //if password matches close the modal and enter into the
                        //model
                        if (current_pwd == menu[0].password) {
                            dialog.close();
                            _super(ev);
                        } else {
                            dialog.$el.find('#wrong_password_alert').show();
                        }
                    };
                });
                dialog.open();
            } else {
                _super(ev);
            }
        })
    },
});