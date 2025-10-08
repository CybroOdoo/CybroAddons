/* @odoo-module*/
import { Component } from '@odoo/owl';
import { useService } from "@web/core/utils/hooks";
import { useState, onMounted, markup, useRef} from "@odoo/owl";


/**
 * MessageView component for displaying a message.
 * @extends Component
 */
export class MessageView extends  Component {
    setup(){
        this.root = useRef("root-mail")
        this.action = useService("action");
        this.html_content = markup(this.props.mail.body_html)
        this.orm = useService("orm");
        this.state = useState({
            attachments: {},
            data: [],

        })
        onMounted(this.fetch_data);
    }
    async fetch_data(){
        var self = this
        for (const ids in this.props.mail.attachment_ids) {
             var value = this.props.mail.attachment_ids
                await this.orm.call("ir.attachment", "get_fields", [value], {}).then((result) => {
                    self.state.attachments = result
                });
        }
    }
    onClickImage(value){
     this.action.doAction({
            type: "ir.actions.act_url",
            url: "/web/content/" + value+ "?download=true",
        });
    }

}
MessageView.template = 'MessageView'
