/** @odoo-module **/
var core = require('web.core');
const rpc = require("web.rpc");
const Dialog = require('web.Dialog');
import { CommandPalette } from "@web/core/commands/command_palette";
import { patch } from 'web.utils';
import { useService } from "@web/core/utils/hooks";
var _t = core._t;
//Patching the CommandPalette for adding condition while using "!" command
patch(CommandPalette.prototype, 'text_commander/static/src/js/command_palette.js', {
        setup() {
        this._super()
        this.action = useService("action");
    },
    //Here we patch the CommandPalette to access commands from the user
    onKeyDown(ev) {
            if (ev.key == 'Enter' && this.state.namespace == '!'){
                var self = this
                if (this.state.searchValue.split(" ")[0] == 'Open'){
                    const regex = /^Open.*\/.*$/;
                    const regex1 = /^Open.*(?:of|in).*$/;
                    const regex2 = /^Open.*/
                    var searchValue = this.state.searchValue
                    if (regex.test(searchValue)){
                        var parts = searchValue.split("/");
                        var model = parts[0].replace("Open ", "");
                        rpc.query({
                            model:'ir.model',
                            method:'check_model',
                            args:[model]
                        }).then(function(res){
                            if(res.length!=0){
                                self.model = res[0]['model']
                                self.model_name = res[0]['name']['en_US']
                                var data = {
                                    'model':self.model,
                                    'record':parts[1],
                                    'regex':1,
                                }
                                rpc.query({
                                    model:'ir.model',
                                    method:'get_records',
                                    args:[data]
                                }).then(function(res){
                                    if (res.length !=1){
                                        self.action.doAction({
                                        name:self.model_name,
                                        type: 'ir.actions.act_window',
                                        res_model: self.model,
                                        domain: [["id", "in", res]],
                                        views: [[false, "list"], [false, "form"]],
                                        view_mode: "list,form",
                                        target: "current",
                                    });
                                    }
                                    else{
                                         self.action.doAction({
                                            type: "ir.actions.act_window",
                                            res_model: self.model,
                                            views: [[false, 'form']],
                                            target: 'current',
                                            res_id:res[0]
                                        });
                                    }
                                    self.props.close()
                                })
                            }
                            else{
                                self.props.close()
                                var buttons = [
                                    {
                                        text: _t("Ok"),
                                        classes: 'btn-primary',
                                        close: true,
                                    },
                                ];
                                new Dialog(self, {
                                        size: 'medium',
                                        buttons: buttons,
                                        $content: $('<div>', {
                                            text:model +  _t(" model not found")
                                        }),
                                    }).open();
                            }
                        })
                    }
                    else if(regex1.test(searchValue)){
                    const pattern = /^Open\s(.*)\s(?:of|in).*$/
                    const match = searchValue.match(pattern);
                    if (match){
                        rpc.query({
                        model:'ir.model',
                        method:'check_model',
                        args:[match[1]]
                        }).then(function(res){
                            if (res.length!=0){
                                self.model = res[0]['model']
                                self._fields_check(self.model)
                                var data = {
                                    'model':self.model,
                                }
                            }
                            else{
                                self.props.close()
                                var buttons = [
                                    {
                                        text: _t("Ok"),
                                        classes: 'btn-primary',
                                        close: true,
                                    },
                                ];
                                new Dialog(self, {
                                    size: 'medium',
                                    buttons: buttons,
                                    $content: $('<div>', {
                                        text:match[1] +  _t(" model not found")
                                    }),
                                }).open();
                            }
                    })
                    }
                }
                    else if(regex2.test(searchValue)){
                        const reg = /^Open\s*/i;
                        const parts = searchValue.split(reg);
                        rpc.query({
                            model:'ir.model',
                            method:'check_model',
                            args:[parts[1]]
                        }).then(function(res){
                            if (res.length!=0){
                                self.action.doAction({
                                    name:res[0]['name']['en_US'],
                                    type: 'ir.actions.act_window',
                                    res_model: res[0]['model'],
                                    views: [[false, "list"], [false, "form"]],
                                    view_mode: "list,form",
                                    target: "current",
                                });
                                self.props.close();
                            }
                            else{
                                self.props.close()
                                var buttons = [
                                    {
                                        text: _t("Ok"),
                                        classes: 'btn-primary',
                                        close: true,
                                    },
                                ];
                                new Dialog(self, {
                                    size: 'medium',
                                    buttons: buttons,
                                    $content: $('<div>', {
                                        text:parts[1] +  _t(" model not found")
                                    }),
                                }).open();
                            }
                        })

                    }
                else{
                    self.props.close()
                    var buttons = [
                        {
                            text: _t("Ok"),
                            classes: 'btn-primary',
                            close: true,
                        },
                    ];
                    new Dialog(self, {
                        size: 'medium',
                        buttons: buttons,
                        $content: $('<div>', {
                            text:_t("not matching command")
                        }),
                    }).open();
                }
                }
                else if(this.state.searchValue.split(" ")[0] == 'Create'){
                    const regex = /^Create.*/
                    const searchValue = this.state.searchValue
                    if (regex.test(searchValue)){
                        const reg = /^Create\s*/i;
                        const parts = searchValue.split(reg);
                        rpc.query({
                            model:'ir.model',
                            method:'check_model',
                            args:[parts[1]]
                        }).then(function(res){
                            if (res.length!=0){
                                self.action.doAction({
                                    type: "ir.actions.act_window",
                                    res_model: res[0]['model'],
                                    views: [[false, 'form']],
                                    target: 'current',
                                });
                                self.props.close();
                            }
                            else{
                                self.props.close()
                                var buttons = [
                                    {
                                        text: _t("Ok"),
                                        classes: 'btn-primary',
                                        close: true,
                                    },
                                ];
                                new Dialog(self, {
                                    size: 'medium',
                                    buttons: buttons,
                                    $content: $('<div>', {
                                        text:parts[1] +  _t(" model not found")
                                    }),
                                }).open();
                            }
                        })
                    }
                    else{
                        self.props.close()
                        var buttons = [
                            {
                                text: _t("Ok"),
                                classes: 'btn-primary',
                                close: true,
                            },
                        ];
                        new Dialog(self, {
                            size: 'medium',
                            buttons: buttons,
                            $content: $('<div>', {
                                text:_t("command not found")
                            }),
                        }).open();
                    }
                }
                else{
                    self.props.close()
                    var buttons = [
                        {
                            text: _t("Ok"),
                            classes: 'btn-primary',
                            close: true,
                        },
                    ];
                    new Dialog(self, {
                        size: 'medium',
                        buttons: buttons,
                        $content: $('<div>', {
                            text:_t("command not found")
                        }),
                    }).open();
                }
            }
    },
    //Check fields
    _fields_check(model){
        var self = this
        const searchValue = this.state.searchValue
        const pattern = /^Open\s.*\s(of|in)\s(.*)$/
        const match = searchValue.match(pattern)
        if (match){
            const string = match[2].split(" ")
            var field_string = ""
                var data = {
                    'model':model,
                    'field_string':string,
                    'regex':2,
                }
                rpc.query({
                    model:'ir.model',
                    method:'check_fields_model',
                    args:[data]
                }).then(function(res){
                    if (res.length!=0){
                        data['field_string'] = match[2].replace(res[0]['del'],"")
                        data['field'] = res[0]['name']
                        data['field_type'] = res[0]['ttype']
                        data['field_relation'] = res[0]['relation']
                        rpc.query({
                            model:'ir.model',
                            method:'get_records',
                            args:[data]
                        }).then(function(res){
                            self.action.doAction({
                                    name:'Records',
                                    type: 'ir.actions.act_window',
                                    res_model: model,
                                    domain: [["id", "in", res]],
                                    views: [[false, "list"], [false, "form"]],
                                    view_mode: "list,form",
                                    target: "current",
                                })
                        })
                        self.props.close()
                    }
                    else{
                        self.props.close()
                        var buttons = [
                            {
                                text: _t("Ok"),
                                classes: 'btn-primary',
                                close: true,
                            },
                        ];
                        new Dialog(self, {
                                    size: 'medium',
                                    buttons: buttons,
                                    $content: $('<div>', {
                                        text:_t("field not found")
                                    }),
                                }).open();
                    }
                })
        }
    },
    //Executing the command
    async executeCommand(command) {
        if (this.state.namespace != '!'){
            const config = await command.action();
            if (config) {
                this.setCommandPaletteConfig(config);
            }
            else {
                this.props.close();
            }
        }
    }
});
