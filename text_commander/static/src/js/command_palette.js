/** @odoo-module **/
import { Dialog } from "@web/core/dialog/dialog";
import { CommandPalette } from "@web/core/commands/command_palette";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
//Patching the CommandPalette for adding condition while using "!" command
patch(CommandPalette.prototype,{
        setup() {
        super.setup()
        this.orm = useService("orm");
        this.action = useService("action");
        this.dialog = useService("dialog")
    },
    //Here we patch the CommandPalette to access commands from the user
    async onKeyDown(ev) {
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
                        const res = await this.orm.call('ir.model', 'check_model', [model])
                            if(res.length!=0){
                                self.model = res[0]['model']
                                self.model_name = res[0]['name']['en_US']
                                var data = {
                                    'model':self.model,
                                    'record':parts[1],
                                    'regex':1,
                                }
                                this.orm.call(
                                    'ir.model',
                                    'get_records',
                                    [data],{}
                                ).then(function(res){
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
                                this.dialog.add(AlertDialog,
                                {
                                    body: _t("model not found"),
                                },

                            );
                            }
                    }
                    else if(regex1.test(searchValue)){
                    const pattern = /^Open\s(.*)\s(?:of|in).*$/
                    const match = searchValue.match(pattern);
                    if (match){
                        const result = await this.orm.call(
                        'ir.model',
                        'check_model',
                        [match[1]],{}
                        )
                        if (result.length!=0){
                            self.model = result[0]['model']
                            self._fields_check(self.model)
                            var data = {
                                'model':self.model,
                            }
                        }
                        else{

                            self.props.close()
                            this.dialog.add(AlertDialog,
                            {
                                body: _t("command not found"),
                            },

                        );
                        }
                    }
                }
                    else if(regex2.test(searchValue)){
                        const reg = /^Open\s*/i;
                        const parts = searchValue.split(reg);
                        const res = await this.orm.call(
                            'ir.model',
                            'check_model',
                            [parts[1]],{
                        })
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
                            this.dialog.add(AlertDialog,
                            {
                                body: _t("command not found"),
                            },

                        );
                        }
                    }
                else{
                    self.props.close()
                    this.dialog.add(AlertDialog,
                        {
                            body: _t("command not found"),
                        },

                    );

                }
                }
                else if(this.state.searchValue.split(" ")[0] == 'Create'){
                    const regex = /^Create.*/
                    const searchValue = this.state.searchValue
                    if (regex.test(searchValue)){
                        const reg = /^Create\s*/i;
                        const parts = searchValue.split(reg);
                        const res = await this.orm.call(
                            'ir.model',
                            'check_model',
                            [parts[1]],{
                        })
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
                            this.dialog.add(AlertDialog,
                            {
                                body: _t("model not found"),
                            },

                        );
                        }
                    }
                    else{
                        self.props.close()
                        this.dialog.add(AlertDialog,
                        {
                            body: _t("command not found"),
                        },

                        );

                    }
                }
                else{
                    self.props.close()
                    this.dialog.add(AlertDialog,
                    {
                        body: _t("command not found"),
                    },

                );
                }
            }
    },
    //Check fields
    async _fields_check(model){
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
            const res = await this.orm.call('ir.model','check_fields_model',[data], {})
                if (res.length!=0){
                    data['field_string'] = match[2].replace(res[0]['del'],"")
                    data['field'] = res[0]['name']
                    data['field_type'] = res[0]['ttype']
                    data['field_relation'] = res[0]['relation']
                    const record = await this.orm.call(
                        'ir.model',
                        'get_records',
                        [data],{})
                        self.action.doAction({
                                name:'Records',
                                type: 'ir.actions.act_window',
                                res_model: model,
                                domain: [["id", "in", record]],
                                views: [[false, "list"], [false, "form"]],
                                target: "current",
                            })
                    self.props.close()
                }
                else{
                    self.props.close()
                    this.dialog.add(AlertDialog,
                        {
                            body: _t("command not found"),
                        },

                    );
                }
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