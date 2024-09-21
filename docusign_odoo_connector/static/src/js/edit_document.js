odoo.define('docusign_odoo.edit_document', function (require) {
"use strict";
var rpc = require('web.rpc');
var basic_fields = require('web.basic_fields');
var id;

    basic_fields.FieldPdfViewer.include({
        init: function () {
        this._super.apply(this, arguments);
        this.PDFViewerApplication = false;
        id = this.res_id;
        this.count = 0;
        this.tabs1 = []
    },
     _render: function () {
        var self = this;
        var $iFrame = this.$('.o_pdfview_iframe');
        var email_count = []
        var add_email_count = []
            if(this.recordData.email_id){
                email_count.push(this.recordData.email_id.data.display_name)}
        $iFrame.on('load', function () {
            $iFrame.contents().find('*').css('user-select', 'none');
            $iFrame.contents().find('#viewer').on('dblclick', function(e){
                this.count ++;
                var pageno;
                var rect_doc;
                if($(e.target.parentNode).attr('class') == 'textLayer'){
                    pageno = $(e.target.parentNode.parentNode).data('pageNumber');
                    rect_doc = e.target.parentNode.getBoundingClientRect();
                }
                else{
                    pageno = $(e.target.parentNode).data('pageNumber');
                    rect_doc = e.target.getBoundingClientRect();
                }
                var values = ["<Select Fields>", "FullName", "Email", "Company", "Signature", "Text"];
                var select = document.createElement("select");
                select.name = "fields";
                var data = {}
                var rect;
                var rect = e.currentTarget.getBoundingClientRect();
                var recipients_list = []
                for(var j=0; j<email_count.length;j++){
                    recipients_list.push(email_count[j])}
                for (let i = 0; i < email_count.length; i++){
                    self.tabs1.push({fullNameTabs:[],signHereTabs:[],emailTabs:[],companyTabs:[],textTabs:[],dateSignedTabs:[]})
                    for (const val of values)
                    {
                        var option = document.createElement("option");
                        option.value = val + ' by ' + recipients_list[i];
                        option.text = val + ' by ' + recipients_list[i];
                        option.id = i+1;
                        select.appendChild(option);
                    }
                }
                var option_date = document.createElement("option");
                option_date.value = 'Date';
                option_date.text = 'Date';
                select.appendChild(option_date);
                select.setAttribute("style", "width:130px; position:absolute; z-index: 999");
                var z = e.clientX - rect.x;
                var y = e.clientY - rect.y;
                var z_doc = e.clientX - rect_doc.x;
                var y_doc = e.clientY - rect_doc.y;
                select.style.left = z + 'px';
                select.style.top = y  + 'px';
                $(select).on('change', function(event){
                    var x_extra = (z_doc * 1.34) - z_doc;
                    var y_extra = (y_doc * 1.34) - y_doc;
                    var doc_x = z_doc - x_extra;
                    var doc_y = y_doc - y_extra;
                    var data = {"xPosition":parseInt(doc_x),"yPosition":parseInt(doc_y),"tabLabel":parseInt(doc_x+doc_y),"documentId":"1","pageNumber":pageno}
                    for(var li of self.tabs1){
                        for(var dict in li){
                            var arr = li[dict];
                            for(var value in arr){
                                if(JSON.stringify(arr[value]) == JSON.stringify(data)){
                                    li[dict].splice(value, 1);
                                }
                            }
                        }
                    }
                    var whole_string = select.value;
                    var split_string = whole_string.split(' by ')
                    for (let i = 0; i <email_count.length; i++){
                        if(select.value == 'Date'){
                            self.tabs1[i].dateSignedTabs.push(data);
                        }
                        if (recipients_list[i] ==  split_string[1]){
                            if(select.value == 'FullName' + ' by ' + recipients_list[i]){
                                self.tabs1[i].fullNameTabs.push(data);
                            }
                            else if(select.value == 'Signature' + ' by ' + recipients_list[i]){
                                self.tabs1[i].signHereTabs.push(data);
                            }
                            else if(select.value == 'Email' + ' by ' + recipients_list[i]){
                                self.tabs1[i].emailTabs.push(data);
                            }
                            else if(select.value == 'Company' + ' by ' + recipients_list[i]){
                                self.tabs1[i].companyTabs.push(data);
                            }
                            else if(select.value == 'Text' + ' by ' + recipients_list[i]){
                                self.tabs1[i].textTabs.push(data);
                            }
                        }
                    }
                    rpc.query({
                        model: 'send.document',
                        method: 'get_json_data',
                        args: [, self.tabs1, id],
                    })
                });
               $iFrame.contents().find("#viewer").append(select);
        });
        });
        this._super();
    },
    });
});
