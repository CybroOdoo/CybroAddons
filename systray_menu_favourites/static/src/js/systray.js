/** @odoo-module **/
import SystrayMenu from 'web.SystrayMenu';
import Widget from 'web.Widget';
import rpc from 'web.rpc';

var SystrayWidget = Widget.extend({
   template: 'SystrayShortcut',
   events: {
       'click .systray_favourites':'click_fav',
       'click .search_view': '_onClick',
       'input .input': '_onInput',
       'click .search_tag':'_Click',
       'click .search_view_click':'click_view',
       'mouseover .search_tag':'_MouseOver',
       'mouseout .search_tag' : '_MouseOut',
       'click #close_button' : '_Close',
   },
    /**
     * @override
     */
   async willStart() {
    //        Update the details of button after refresh the page and
    //it will be collected using the id and restore it from the database
        var self = this;
        rpc.query({
            model: 'button.store',
            method: 'action_search',
            args: [],
            }).then(function (Result) {
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
                    self.$('.button_element').append(main);
                }
            });
   },
   click_fav: function(){
    //   Show the input field
       this.$("#popup").css("display","block");
       document.getElementById("search").value = "";
       this.$("#add_fav").css("display","none")
   },
    _onInput: function(){
    //    Update the input data
        var vals = this.$(".input").val();
    },
    _onClick: function(){
    //Show the dropdown list of all related menus,
    //which retrieve from the corresponding model
        var self = this;
        var input = this.$(".input").val();
        this.$("#drop_list").css("display","block");
        rpc.query({
           model: 'ir.ui.menu',
           method: 'search_read',
           args: [[['name', 'ilike', input],['action', '!=', null]]],
            }).then(function (Result) {
                var Div = document.createElement('div');
                for(var i = 0; i < Result.length ; i++){
                    var tag = document.createElement('div');
                    tag.classList.add("search_tag");
                    var result = document.createTextNode(Result[i].complete_name);
                    tag.setAttribute("id",Result[i].id);
                    tag.append(result);
                    Div.append(tag);
                }
                self.$('.dropdown_view').empty();
                self.$('.dropdown_view').append(Div);
            })
    },
    _MouseOver: function(ev){
    //    Change the background color when mouse moves
        var data_id = ev.target.id
        this.$("#" + data_id).css("background","#D3D3D3");
    },
    _MouseOut: function(ev){
    //    Change the background color when mouse moves
        var data_id = ev.target.id
        this.$("#" + data_id).css("background","white");
    },
    _Click: function(ev){
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
        var close_button = document.createElement("button");
        close_button.setAttribute("id","close_button");
        close_button.innerHTML ='X';
        main.style.margin='5px'
        main.append(button);
        main.append(close_button);
        this.$('.button_element').append(main);
        this.$("#drop_list").css("display","none");
        this.$("#popup").css("display","none");
        this.$("#add_fav").show();
        rpc.query({
            model: 'button.store',
            method: 'action_create',
            args: [result, ev.target.id],
            })
    },
    click_view: function(ev){
    //  Show the view when we click the button, the corresponding menu will show
        var self = this
        var data_id = ev.target.id
        rpc.query({
            model: 'ir.ui.menu',
            method: 'search_views',
            args: [data_id],
            }).then(function (Result) {
             self.do_action({
                type: 'ir.actions.act_window',
                name: Result.name,
                res_model: Result.model,
                view_mode: Result.view_mode,
                views: [[false, 'list'], [false, 'form'], [false, 'kanban']],
                target: 'main',
            });

        });
    },
    _Close : function(ev){
    //  Remove the button when we click the close symbol
        var element = ev.target.parentElement.firstChild.id;
        rpc.query({
            model: 'button.store',
            method: 'action_remove_view',
            args: [element],
            })
        ev.target.parentElement.remove();
    },
});
SystrayMenu.Items.push(SystrayWidget);
export default SystrayWidget;
