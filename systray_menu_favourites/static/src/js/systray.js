/** @odoo-module **/
import SystrayMenu from 'web.SystrayMenu';
import Widget from 'web.Widget';
import BasicController from 'web.BasicController';
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

   async willStart() {
        console.log('values')
        rpc.query({
            model: 'button.store',
            method: 'search_button',
            args: [],
            }).then(function (Result) {
                for(var i = 0; i < Result.length ; i++){
                    var main = document.createElement("span");
                    main.classList.add("main_button");
                    var btn = document.createElement("button");
                    btn.type = "button";
                    btn.innerHTML = Result[i].name;
                    btn.setAttribute("id",Result[i].button_id);
                    btn.classList.add("search_view_click");
                    main.style.margin='5px'
                    var close_button = document.createElement("button");
                    close_button.setAttribute("id","close_button");
                    close_button.innerHTML ='X';
                    main.style.margin='5px'
                    main.append(btn);
                    main.append(close_button);
                    $('.button_element').append(main);
                }
            });
   },

   click_fav: function(){
       document.getElementById('popup').style.display='block';
       document.getElementById('add_fav').style.display='none';
   },

    _onInput: function(){
        var vals = $(".input").val();
    },

    _onClick: function(e){
        var input = $(".input").val();
        document.getElementById('drop_list').style.display='block';
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
                $('.dropdown_view').empty();
                $('.dropdown_view').append(Div);
            })
    },
    _MouseOver: function(ev){
        var data_id = ev.target.id
        document.getElementById(data_id).style.background='#D3D3D3';
    },
    _MouseOut: function(ev){
        var data_id = ev.target.id
        document.getElementById(data_id).style.background='white';
    },

    _Click: function(ev){
        var self = this;
        var vals = ev.currentTarget.textContent;
        var n = vals.lastIndexOf('/');
        var result = vals.substring(n + 1);
        var main = document.createElement("span");
        main.classList.add("main_button");
        var btn = document.createElement("button");
        btn.type = "button";
        btn.innerHTML = result;
        btn.setAttribute("id",ev.target.id);
        btn.classList.add("search_view_click");
        var close_button = document.createElement("button");
        close_button.setAttribute("id","close_button");
        close_button.innerHTML ='X';
        main.style.margin='5px'
        main.append(btn);
        main.append(close_button);
        $('.button_element').append(main);
        document.getElementById('drop_list').style.display='none';
        document.getElementById('popup').style.display='none';
        $("#add_fav").show();
        rpc.query({
            model: 'button.store',
            method: 'create_button',
            args: [result, ev.target.id],
            })

    },

    click_view: function(ev){
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
                view_mode: Result.view,
                views: [[false, Result.view]],
                target: Result.target
            });

        });
    },
    _Close : function(ev){
        var element = ev.target.parentElement.firstChild.id;
        rpc.query({
            model: 'button.store',
            method: 'remove_view',
            args: [element],
            })
        ev.target.parentElement.remove();
    },


});

SystrayMenu.Items.push(SystrayWidget);
export default SystrayWidget;

