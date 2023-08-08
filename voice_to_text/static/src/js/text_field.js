/** @odoo-module **/

import { TextField } from "@web/views/fields/text/text_field";
import { patch } from "@web/core/utils/patch";
import rpc from 'web.rpc';
patch(TextField.prototype,'@web/views/fields/text/text_field',{
    setup() {
    this._super.apply();
    },
        // This function is used to recognize voice on the text fields
    async recordText(ev){
        var self = this
        var browser = await rpc.query({
                                model: 'voice.recognition',
                                method: 'get_the_browser',
                                args: [,],
        }).then(function (data) {
            if (data =='chrome'){
                let final_transcript = "";
                if ("webkitSpeechRecognition" in window) {
                    let speechRecognition = new webkitSpeechRecognition();
                    if(speechRecognition){
                        speechRecognition.continuous = true;
                         navigator.mediaDevices.getUserMedia({
                            audio: true}).then(
                            speechRecognition.start())
                         speechRecognition.onresult = (e) => {
                            for (let i = e.resultIndex; i < e.results.length; ++i) {
                                if (e.results[i].isFinal) {
                                    final_transcript += e.results[i][0].transcript;
                                } else {
                                    interim_consttranscript += event.results[i][0].transcript;
                                }
                            }
                            if(final_transcript){
                                var field = this.__owl__.bdom.parentEl.attributes.name.nodeValue
                                var model = this.props.record.resModel
                                var browser =  rpc.query({
                                    model: 'voice.recognition',
                                    method: 'update_field',
                                    args: [,field,model,final_transcript],
                                })

                            }

                         }
                    }
                 }
            }
            else if(data=='all_browser') {
                var field = self.__owl__.bdom.parentEl.attributes.name.nodeValue
                var model = self.props.record.resModel
                var id = self.env.model.__bm_load_params__.res_id
                var browser =  rpc.query({
                                    model: 'voice.recognition',
                                    method: 'update_field',
                                    args: [,field,model,false,id],
                })
            }
        })

    }
})



