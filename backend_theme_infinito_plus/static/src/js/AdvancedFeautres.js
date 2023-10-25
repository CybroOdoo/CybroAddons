odoo.define('backend_theme_infinito_plus.AdvancedFeatures', function (require) {
  "use strict";
  var AdvancedFeatures = require('backend_theme_infinito.AdvancedFeatures');
  var session = require('web.session');
  var ajax = require('web.ajax');
  var Dialog = require('web.Dialog');
  var core = require('web.core');
  var rpc = require('web.rpc');
  var _t = core._t;
  //Overriding the AdvancedFeatures component for adding new features to module
  AdvancedFeatures.include({
    events: _.extend({}, AdvancedFeatures.prototype.events, {
      'change #chatBoxPosition': 'onPositionChange',
      'change #infinito_font_select': 'onFontChange',
      'click #infinito_font_select_google': '_onAddGoogleFontClick',
      'change #animatedView': 'onAnimationChange'
    }),
    //Initializes the Chat Widget settings.
    init: function (parent, type) {
      this._super.apply(this, arguments);
      this.chatBoxPosition = ['Top Right', 'Top Left', 'Bottom Right', 'Bottom Left'];
      this.infinitoAnimation = ['Default', 'Scale', 'Slide in'];    },
    //This function is responsible for rendering the Chat Widget data and initializing the settings.
    async renderData() {
      this._super.apply(this, arguments);
      this.chat_style = [];
      rpc.query({
        model: "infinito.google.font",
        method: 'search_read',
        args: [],
      }).then((res) =>{
        var selectElement = this.$el.find('#infinito_font_select');
        var font_id = session.infinitoGoogleFont
        res.forEach(function(option){
            var newOption = $("<option>").text(option['name']).val(option['id']).addClass('form-select infinito-form-select google-font');
            selectElement.find("option:eq(1)").before(newOption);
            if (font_id == option['id']){
                newOption.prop('selected', true);
            }
        })
      });
      if (this.type == 'user'){
        this.$el.find("#fonts_container").prop("class","button_properties d-none");
        }
      else{
        this.$el.find("#fonts_container").prop("class","button_properties d-block");
      }
      this.$el.find('#infinito_font_select').val(session.infinitoGoogleFont);
      let position_content = '';
      for (let position of this.chatBoxPosition) {
        position_content += `<option value="${position}">${position}</option>`;
      }
      this.$el.find('#chatBoxPosition').html(position_content);
      this.$el.find('#chatBoxPosition').val(session.chatBoxPosition);

      let animationContent = '';
      let index = 0
      for (let animation of this.infinitoAnimation) {
        animationContent += `<option value="${index}">${animation}</option>`;
        index +=1;
      }
      this.$el.find('#animatedView').html(animationContent);
      this.$el.find('#animatedView').val(session.infinitoAnimation)
      this.$el.find('#navbarRefreshToggler').prop('checked', session.infinitoRefresh);
    },
    //This function is responsible for saving the changes made to the Chat Widget settings.
    async _SaveChanges() {
      this._super.apply(this, arguments);
      let vals = {
        'infinitoRefresh': this.$el.find('#navbarRefreshToggler').is(':checked'),
        'chatBoxPosition': this.$el.find('#chatBoxPosition').val(),
        'infinitoAnimation': this.$el.find('#animatedView').val(),
        'animations' : this.animated_id,
        'infinitoGoogleFont' :  this.font_id ? this.font_id : 0,
      };
      var chat_style = this.chat_style;
      session.chatBoxPosition = vals.chatBoxPosition;
      session.infinitoAnimation = vals.infinitoAnimation;
      session.infinitoRefresh = vals.infinitoRefresh
      var style = [];
      if (vals.animations === '1') {
        style.push('infinito_kanban_scale');
      } else if (vals.animations === '0') {
        style.push('infinito_kanban_shake');
      } else if (vals.animations === '2') {
        style.push('infinito_kanban_slide_in');
      }
      if (style.length != 0){
        await ajax.jsonRpc('/theme_studio/animation_styles', 'call', { 'style': JSON.stringify(style)});
        }
      if (chat_style.length !== 0) {
        await ajax.jsonRpc('/theme_studio/save_styles_plus', 'call', { 'new_style': JSON.stringify(chat_style) });
      }
      if (vals.infinitoGoogleFont.length !== 0){
        await ajax.jsonRpc('/theme_studio/font_style', 'call', { font_id: vals.infinitoGoogleFont });}
      if (this.type == 'global'){
        await ajax.jsonRpc('/theme_studio/set_advanced_plus_data', 'call', {vals})
      }
      if(this.type == 'user'){
        await ajax.jsonRpc('/theme_studio/set_advanced_plus_data_user', 'call', {vals}).then((_) => {
            this._Close(); })
      }
    },
    //ChatBox position change function.
    async onPositionChange(ev) {
      let val = ev.target.value;
      const positionMap = {
        'Top Right': { 'top': '10px', 'left': 'auto' },
        'Top Left': { 'top': '10px', 'left': '10px', 'right': 'auto' },
        'Bottom Left': { 'left': '10px', 'bottom': '10px', 'top': 'auto', 'right': 'auto' },
        'Bottom Right': { 'right': '10px', 'bottom': '10px', 'top': 'auto', 'left': 'auto' }
      };
      this.chat_style = [positionMap[val]] || [];
    },
    //Animation change function.
    onAnimationChange: function(ev) {
        this.animated_id = ev.target.value;
    },
    //Font change function.
    onFontChange: function(ev){
        let options = ev.target.options
        let selected = this.$(options[options.selectedIndex])
        if(selected.hasClass('add-font')){
            this.addGoogleFont()
        }
        else if(selected.hasClass('system-font')){
            this.font_id = 0}
        else {
            this.font_id = parseInt(selected.val())}
    },
     //AddGoogleFont - Function to open a dialog for adding a Google Font and save it to the backend.
    addGoogleFont: function(){
        const dialog = new Dialog(this, {
            title: _t("Add a Google Font"),
            $content: $(core.qweb.render('backend_theme_infinito_plus.dialog.addGoogleFont')),
            // open a wizard for selecting google font
            buttons: [
                {   text: _t("Save & Reload"),
                    classes: 'btn-primary',
                    click: async () => {
                        const inputEl = dialog.el.querySelector('.o_input_google_font');
                        let m = inputEl.value.match(/\bfamily=([\w+]+)/);
                        // validation of link
                        if(m){
                        const font = m[1].replace(/\+/g, ' ');
                        var self = this;
                        rpc.query({
                            model: "infinito.google.font",
                            method: 'save_google_fonts',
                            args: [[font,m.input]],
                        }).then(function (data) {
                            window.location.reload();
                        });
                        }
                    },
                },
                {
                    text: _t("Discard"),
                    close: true,},],
        });
        dialog.open();
    }
  });
  return AdvancedFeatures;
});
