/** @odoo-module **/
import { CommandPalette } from "@web/core/commands/command_palette";
import { patch } from "@web/core/utils/patch";
import rpc from 'web.rpc';
patch(CommandPalette.prototype, '@web/core/commands/command_palette', {
    setup() {
        this._super.apply();
    },
    //This function is used to recognize the voice
    async recordVoice(event) {
        if (location.href.includes('http:')){
            var response =  await rpc.query({
                                model: 'voice.recognition',
                                method: 'recognize_speech',
                                 args: [,],
                                })
            if (response){
                this.state.searchValue = response
            }
            else{
                 this.state.searchValue = "Your voice could not be recognizing......"
            }
        }
    },
})