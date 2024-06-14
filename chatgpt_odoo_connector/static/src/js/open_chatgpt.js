/** @odoo-module **/
const { Component, useState, useExternalListener, xml } = owl;
import { registry } from "@web/core/registry";
/* Extending the component and creating class OpenChatGPT */
export class OpenChatGPT extends Component {
    constructor() {
        super(...arguments);
        this.state = useState({
            message: '',
            response: ''
        });
        this.Send = this.Send.bind(this);
        this.Cancel = this.Cancel.bind(this);
        this.onWindowEnter = this.onWindowEnter.bind(this);
        useExternalListener(window, "click", this.onWindowClick);
        useExternalListener(window, "keydown", this.onWindowEnter);
    }
    /* Getting the response based on the message provided */
    async Send(ev){
        if (ev.state.message.trim()){
            this.state.response = await this.props.rpc.query({
                model: 'open.chatgpt',
                method: 'get_response',
                args: [ev.state.message],
            })
        }
    }

    /* Function for inserting the response to the description field */
    insert(){
        var content = this.state.response
        const lines = content.split('\n').filter(line => line.trim().length);
        const fragment = document.createDocumentFragment();
        for (const line of lines) {
            const block = document.createElement(line.startsWith('Title: ') ? 'h2' : 'p');
            block.innerText = line;
            fragment.appendChild(block);
        }
        this.props.self.el.appendChild(fragment);
        this.Cancel()
    }

    /* Function for cancelling */ 
    Cancel(){
        var element = document.querySelector('.popChatGPT');
        element.remove();
    }

    /* Function for closing the widget while clicking outside */
    onWindowClick(ev) {
        var element = document.querySelector('.popChatGPT');
        if (element && !element.contains(ev.target)){
            element.remove();
        }
    }
    /* Function for calling the function Send */
    onWindowEnter(ev){
        var element = document.querySelector('.popChatGPT');
        if (element && ev.key == 'Enter'){
            this.Send(this)
        }
    }
}

OpenChatGPT.template = xml`
    <div class="popChatGPT">
        <div style="display: flex; align-items: end;margin-top:-20px;">
            <img src="chatgpt_odoo_connector/static/src/Icons/icon.png" height="35px"/>
            <div class="h2 heading">ChatGPT</div>
        </div>
        <hr/>
        <div class="mb-3">
            <label for="message" class="form-label" style="color:white;">Message</label>
            <div style="display: flex;">
                <input type="text" class="custom-input" id="message" placeholder="Enter message"
                    t-model="state.message"/>
                <button class="btn btn-success" style="border-radius:0px 12px 12px 0px;" t-on-click="() => Send(this)">
                    <i class="fa fa-paper-plane"></i>
                </button>
            </div>
        </div>
        <label for="response" class="form-label" style="color:white;" t-if="state.response">Response</label>
        <div t-if="state.response">
            <div class="mb-3">
                <textarea id="response" class="custom-text" rows="4" t-model="state.response"></textarea>
            </div>
        </div>
        <div style="display: flex;justify-content: space-around;">
            <button class="btn btn-primary custom" t-if="state.response" t-on-click="insert">Insert</button>
            <button class="btn btn-secondary custom" t-on-click="Cancel">Cancel</button>
        </div>
    </div>`;
registry.category("actions").add("chatGPT", OpenChatGPT);
