/** @odoo-module **/
import { NavBar } from '@web/webclient/navbar/navbar';
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { useState, onWillStart ,useRef} from "@odoo/owl";
import { session } from "@web/session";
import { jsonrpc } from "@web/core/network/rpc_service";

patch(NavBar.prototype, {
    setup() {
        super.setup();
        this.orm = useService("orm");
        this.wrong_pswd = false
        this.lock_state = useState({
            // Duration is expected to be given in minutes
            locked: true,
            lock_model: false
        });
        this.locked_ids = false
        this.password = useRef('password')
        this.warning = useRef('menu_warn')
        onWillStart(async () => {
            this.locked_ids = await this.orm.searchRead("res.users", [['id', '=', session.user_id[0]]], ["menus_to_lock_ids"]);
            this.new_ids = this.locked_ids[0].menu_to_lock_ids;
            this.users = await this.orm.call("res.users", "menu_lock_search", [
                session.user_id[0]
            ]);
        });
    },

    showPassword(){
        if (this.password.el.value){
           const type = this.password.el.getAttribute('type') === 'password' ? this.password.el.setAttribute('type','text'): this.password.el.setAttribute('type','password');
        }
    },

    onNavBarDropdownItemSelection(menu) {
        if (menu) {
            // Fix the syntax of 'not in'
            this.menu = menu
            this.lock = false
            jsonrpc('/locked_models',{'action':menu.actionID,'action_type':menu.actionModel}).then((result) => {
                this.lock_state.locked_model = result
                if(result || this.users.locked_menu_ids.includes(menu.id)){
                    this.lock_state.locked = false
                    if (this.users.locked_models){
                        this.lock_state.lock_model = result
                    }
                }
                else{
                     this.menuService.selectMenu(this.menu);
                }
            })
        }
    },
    async Confirm(){
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
                    self.item = true
                    self.menu_id = item.id
                }
            });
            if (self.item && self.menu.id == self.menu_id){
                 await this.menuService.selectMenu(this.menu)
                    this.lock_state.locked = true
            }
            else{
                this.wrong_pswd = true
                this.warning.el.classList.remove("d-none");
            }
        }
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
