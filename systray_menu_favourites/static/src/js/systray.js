/** @odoo-module **/
import { useService, useBus } from "@web/core/utils/hooks";
import { Component,onWillStart,useRef} from "@odoo/owl";
import { session } from "@web/session";
import { registry } from "@web/core/registry";
import { Dropdown } from "@web/core/dropdown/dropdown";
export class SystrayWidget extends Component {
    async setup() {
        super.setup(...arguments);
        this.rpc = useService('rpc');
        this.orm = useService('orm');
        this.action = useService("action");
        this.popup= useRef("popup")
        this.add_fav = useRef("add_fav")
        this.input = useRef("inputField")
        this.dropList = useRef("dropList")
        this.dropdownView = useRef("dropdownView")
        this.button_element = useRef("buttonElement")
    onWillStart(async () => {
    //        Update the details of button after refresh the page and
    //it will be collected using the id and restore it from the database
        var self = this;
        this.orm.call('button.store','action_search',[]
        ).then(function (Result) {
                for(var i = 0; i < Result.length ; i++){
                    var main = document.createElement("span");
                    main.classList.add("main_button");
                    var button = document.createElement("button");
                    button.type = "button";
                    button.innerHTML = Result[i].name;
                    button.setAttribute("id",Result[i].button);
                    button.classList.add("search_view_click");
                    main.style.margin='5px'
                    var close_button = document.createElement("button");
                    close_button.setAttribute("id","close_button");
                    close_button.innerHTML ='X';
                    main.style.margin='5px'
                    main.append(button);
                    main.append(close_button);
                    this.button_element.el.append(main);
                }
            });
   });
   }
   async click_fav(ev){
    //   Show the input field
       this.popup.el.style.display='block'
       this.input.el.value = "";
       this.add_fav.el.style.display='none'
   }
    async _onInput(){
    //    Update the input data
        var vals = this.input.el.value;
    }
     async _onClick(){
    //Show the dropdown list of all related menus,
    //which retrieve from the corresponding model
        var self = this;
        var input = self.input.el.value;
        this.dropList.el.style.display='block'
        this.orm.call("ir.ui.menu", "search_read", [[['name', 'ilike', input],['action', '!=', null]]
        ]).then(function(Result) {
                var Div = document.createElement('div');
                for(var i = 0; i < Result.length ; i++){
                    var tag = document.createElement('div');
                    tag.classList.add("search_tag");
                     tag.addEventListener('click', self._Click.bind(self));
                     tag.addEventListener('mouseover', self._MouseOver);
                     tag.addEventListener('mouseout', self._MouseOut);
                    var result = document.createTextNode(Result[i].complete_name);
                    tag.setAttribute("id",Result[i].id);
                    tag.append(result);
                    Div.append(tag);
                }
                  self.dropdownView.el.innerHTML = '';
                  self.dropdownView.el.append(Div);
            })
    }
    _MouseOver(ev) {
        const data_id = ev.target.id;
        document.getElementById(data_id).style.background = "#D3D3D3";
    }

    _MouseOut(ev) {
        const data_id = ev.target.id;
        document.getElementById(data_id).style.background = "white";
    }
    async _Click(ev){
    //    Add the button for menu when click the menu from the dropdown list
        var self = this;
        var vals = ev.currentTarget.textContent;
        var num = vals.lastIndexOf('/');
        var result = vals.substring(num + 1);
        var main = document.createElement("span");
        main.classList.add("main_button");
        var button = document.createElement("button");
        button.type = "button";
        button.innerHTML = result;
        button.setAttribute("id",ev.target.id);
        button.classList.add("search_view_click");
        button.onclick = () => { var self = this
        var data_id = ev.target.id
        this.env.services.orm.call('ir.ui.menu','search_views',[data_id]
        ).then(function (Result) {
             self.env.services.action.doAction({
                type: 'ir.actions.act_window',
                name: Result.name,
                res_model: Result.model,
                view_mode: Result.view_mode,
                views: [[false, 'list'], [false, 'form'], [false, 'kanban']],
                target: 'main',
            });

        });
        }
        button.addEventListener('click', self.click_view.bind(self));
        var close_button = document.createElement("button");
        close_button.setAttribute("id","close_button");
        close_button.innerHTML ='X';
        main.style.margin='5px'
        close_button.addEventListener('click', self._Close.bind(self));
        main.append(button);
        main.append(close_button);
        this.button_element.el.append(main);
        this.dropList.el.style.display='none'
        this.popup.el.style.display='none'
        this.add_fav.el.style.display='block'
    }
    async click_view(ev){
    //  Show the view when we click the button, the corresponding menu will show
        var self = this
        var data_id = ev.target.id
         this.orm.call('ir.ui.menu','search_views',[data_id]
        ).then(function (Result) {
            self.env.services.action.doAction({
                type: 'ir.actions.act_window',
                name: Result.name,
                res_model: Result.model,
                view_mode: Result.view_mode,
                views: [[false, 'list'], [false, 'form'], [false, 'kanban']],
                target: 'main',
            });
        });
    }
    async _Close(ev){
    //  Remove the button when we click the close symbol
        var element = ev.target.parentElement.firstChild.id;
        this.env.services.orm.call('button.store','action_remove_view',[element])
        ev.target.parentElement.remove();
    }
    }
SystrayWidget.components = { Dropdown };
    export const systrayItem = {
    Component: SystrayWidget,
};
SystrayWidget.template = "systray_menu_favourites.SystrayShortcut"
registry.category("systray").add("SystrayMenu", systrayItem, { sequence: 0 });
