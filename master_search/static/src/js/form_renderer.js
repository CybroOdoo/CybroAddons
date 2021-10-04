odoo.define('master_search.FormRenderer', function(require) {
"use strict";

    var FormRenderer = require('web.FormRenderer');
    var framework = require('web.framework');

    FormRenderer.include({
        events: _.extend({}, FormRenderer.prototype.events, {
            'click .oe_search_tab': '_onSearchTabClick',
            'click .oe_search_btn': '_onSearchButtonClick',
            'keyup .search_input': '_onKeypressSearch',
            'click .re_search': '_onHistoryClick',
        }),
        // Research on history click
        _onHistoryClick: function(ev){
            var history_key = ev.currentTarget.parentElement.firstChild.innerText;
            var edit_flag = $(".search_input").hasClass('o_input')
            // search if in edit mode
            if (edit_flag){
                $(".search_input").val(history_key)
                                    .trigger('change');
                $('.oe_search_btn').trigger('click');
            }
            else{
                // trigger edit mode if search screen
                $('.o_form_button_edit').trigger('click');
                //var search_input = $(".search_input").length
                //if (search_input <= 0 ){$('.o_form_button_edit').trigger('click');}
            }
        },
        // Trigger search while enter is pressed and process input
        _onKeypressSearch: function(ev){
            var search_string = $(".search_input").val();
            if(search_string.includes("*") == true){
                $(".not-allowed").css("display", 'block');
                // remove * from the input
                $(".search_input")
                                .val(search_string.replace('*', ''))
                                .trigger('change');
            }
            else{$(".not-allowed").css("display", 'none');}
            if (ev.which == 13){$('.oe_search_btn').trigger('click');}
        },
         // block UI while searching
        _onSearchButtonClick: function(ev){
            if( $(".search_input").val() != ''){framework.blockUI();}
        },

        // collapse and expand tabs
        _onSearchTabClick: function(ev){
            var targetDiv = ev.currentTarget.parentElement.children[1]
            var targetIcon = ev.currentTarget.getElementsByClassName('fa')[0]
            if (targetDiv){
                if(targetDiv.style.display == "block") {
                    console.log(targetDiv.style.display, "ddddddd")
                    targetDiv.style.display = "none";
                    targetIcon.className = "fa fa-caret-down"
                }
                else {
                    console.log(targetDiv.style.display, "sssssss")
                    targetDiv.style.display = "block";
                    targetIcon.className = "fa fa-caret-up"
                }
            }
        },

        // override existing form renderer function
        _renderView: function () {
            var self = this;

            // render the form and evaluate the modifiers
            var defs = [];
            var colour_list = []
            this.defs = defs;
            this.inactiveNotebooks = [];
            var $form = this._renderNode(this.arch).addClass(this.className);
            delete this.defs;

            return Promise.all(defs).then(() => this.__renderView()).then(function () {
                self._updateView($form.contents());
                if (self.state.res_id in self.alertFields) {
                    self.displayTranslationAlert();
                }
                self.trigger_up('edit_mode');
            }).then(function(){
                if (self.lastActivatedFieldIndex >= 0) {
                    self._activateNextFieldWidget(self.state, self.lastActivatedFieldIndex);
                }
                if (self._isInDom) {
                    _.forEach(self.allFieldWidgets, function (widgets){
                        _.invoke(widgets, 'on_attach_callback');
                    });
                }
                // function for getting random light colors
                function getRandomColor() {
                    var color = "hsl(" + Math.random() * 360 + ", 100%, 75%)";
                    // avoid colour repetition
                    if(colour_list.indexOf(color) > -1){color = getRandomColor()}
                    colour_list.push(color);
                    return color;
                }
                // function for expanding tabs with result count
                function onSearchButtonClick(ev){
                    $('.oe_search_tab').each(function(i, obj) {
                        var result_count = parseInt(obj.getElementsByClassName('oe_tab_count')[0].innerHTML)
                        if (result_count > 0){
                            obj.click()
                        }
                    });
                }
                // Highlight all the words in result with different color
                var text = $(".search_input").val();
                if (text){
                    var keyword_list = []
                    var key_list = text.split(" ")
                    for (var i = 0; i< key_list.length; i++) {
                        keyword_list[i] = {'key': key_list[i], 'color':getRandomColor()}
                    }
                    for (var i = 0; i< keyword_list.length; i++) {
                        var key = keyword_list[i].key;
                        var color = keyword_list[i].color
                        var regex = new RegExp("("+key+")", "ig");
                        $('.o_data_cell').each(function(i, obj) {
                            var old_text = obj.innerHTML
                            if (!obj.firstChild || obj.firstChild.type != 'button'){
                                obj.innerHTML = old_text.replace(regex, "<span style='background-color: "+ color +";'>$1</span>");
                            }
                        });
                    }
                }
                // trigger search button click for expand tab with value
                if((self.$el.find(".search_input")).length > 0){onSearchButtonClick()}
                // unblock UI
                framework.unblockUI();
                // change document title on search refresh
                var search_input = $(".search_input").length
                if (search_input <= 0 ){document.title = 'Search';}
            }).guardedCatch(function () {
                $form.remove();
            });
        },
    });
});
