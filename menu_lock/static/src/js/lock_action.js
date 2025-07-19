/** @odoo-module **/
import { NavBar } from '@web/webclient/navbar/navbar';
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { useState, onWillStart ,useRef, onWillRender} from "@odoo/owl";
import { session } from "@web/session";
import { rpc } from "@web/core/network/rpc";

patch(NavBar.prototype, {
    setup() {
        super.setup();
        this.orm = useService("orm");
        this.wrong_pswd = false
        this.lock_state = useState({
            locked: true,
            lock_model: false,
        });
        this.locked_ids = false
        this.password = useRef('password')
        this.warning = useRef('menu_warn')
        onWillStart(async () => {
            this.locked_ids = await this.orm.searchRead("res.users", [['id', '=', session.storeData["res.partner"][1].userId]], ["menus_to_lock_ids"]);
            this.new_ids = this.locked_ids.menu_to_lock_ids;
            this.lock_state.users =this.users
        });
    },
    //Function for show password
    showPassword(){
        if (this.password.el.value){
           const type = this.password.el.getAttribute('type') === 'password' ? this.password.el.setAttribute('type','text'): this.password.el.setAttribute('type','password');
        }
    },

    onNavBarDropdownItemSelection(menu) {
        if (menu) {
            this.menu = menu
            this.lock = false
            //RPC Call to fetch the menu lock details from the res.users
             rpc(`/web/dataset/call_kw/res.users/menu_lock_search`, {
            model: 'res.users',
            method: 'menu_lock_search',
            args: [session.storeData["res.partner"][1].userId, menu.actionID, menu.actionModel],
            kwargs: {},
        }).then((result) => {
        this.users = result
        //  Popup will be shown if the selected menu is in the locked menus
        //  list or action model is in the locked model list
        if(this.users.locked_models || this.users.locked_menu_ids.includes(menu.id)){
                    this.lock_state.locked = false
                    if (this.users.locked_models){
                        this.lock_state.lock_model = this.users.locked_models
                    }
                }
                else
                {
                     this.menuService.selectMenu(this.menu);
                }
        });
        }
    },
    //Function for confirm password and access the menu
    async Confirm(){
//            ]);
        var self = this
        if (this.users.lock_type == 'single_password'){

            this.users.multi_lock_ids.forEach(function(item){
                    if (item.id == self.menu.id){
                        self.item = true
                    }
                });
            if (this.users.login_password == this.password.el.value && self.item){
                await this.menuService.selectMenu(this.menu)
                this.lock_state.locked = true
            }
            else{
                this.wrong_pswd = true
                this.warning.el.classList.remove("d-none");
            }
        }
        if (this.users.lock_type == 'multi_password'){
            this.users.multi_lock_ids.forEach(function(item){
                if (item.id == self.menu.id && item.password == self.password.el.value){
                    self.menuService.selectMenu(self.menu)
                    self.lock_state.locked = true
                }
                else{
                self.wrong_pswd = true
                self.warning.el.classList.remove("d-none");
            }
            });
        }
        //Control access for the locked models
        if(this.users.locked_models){
             if (this.users.login_password == this.password.el.value){
                await this.menuService.selectMenu(this.menu)
                this.lock_state.locked = true
            }
        }
    },
    CancelDialog() {
        this.lock_state.locked = true
    },
});
