/** @odoo-module **/

import { SearchBar } from "@web/search/search_bar/search_bar";
import { patch } from "@web/core/utils/patch";
import rpc from 'web.rpc';
var microphone = false
patch(SearchBar.prototype, '@web/search/search_bar/search_bar', {
    setup() {
        this._super(...arguments);
    },
    //This function is used to recognize the voice in the search bar
    async recordVoiceBar(event) {
        this.microphone = true
        if (location.href.includes('http:')){
            var response =  await rpc.query({
                                model: 'voice.recognition',
                                method: 'recognize_speech',
                                args: [,],
            })
            if (response){
                this.response = response
            }
            else{
                this.response= "False"
                var w_response = confirm("can't recognize try again....")
            }
        }
    },
    onSearchInput(ev) {
        if (this.microphone == true){
            if(this.response != "False"){
                ev.target.value = this.response;
            }
            else{
                ev.target.value = "Your Voice can't recognize please try again.";
            }
        }
        const query = ev.target.value
        if (query.trim()) {
            this.computeState({ query, expanded: [], focusedIndex: 0, subItems: [] });
        } else if (this.items.length) {
            this.resetState();
        }
    }
})
