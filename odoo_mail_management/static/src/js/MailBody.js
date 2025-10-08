/* @odoo-module*/
import { Component, useRef, useState ,markup} from '@odoo/owl'
import { useService } from "@web/core/utils/hooks";

/**
 * MailBody component for displaying mail details.
 * @extends Component
 */
export class MailBody extends  Component {
    setup() {
        this.ref = useRef('root')
        this.html_content = this.props.mail.body_html.replace(/<br>/g, '')

        this.orm = useService('orm')
        this.state = useState({
            starred: false,
        })
        this.env.bus.addEventListener("SELECT:ALL", (event) => {
            const { checked } = event.detail
            this.ref.el.querySelector(".mail_check_box").checked = checked
            this.props.onSelectMail(this.props.mail.id, checked)
        })
    }
    /**
     * Method triggered on click of the mail selection checkbox.
     * @param {Object} ev - Event object.
     */
    onClickSelect(ev) {
        const checked = ev.target.checked
        this.props.onSelectMail(this.props.mail.id, checked)
    }
     /**
     * Method to archive the mail.
     * @param {Object} event - Event object.
     */
     async archiveMail(event){
      var mail = this.props.mail.id
      await this.orm.call('mail.mail','archive_mail',[mail])
    }
    /**
     * Method to unarchive the mail.
     * @param {Object} event - Event object.
     */
     async unArchive(event){
      var mail = this.props.mail.id
       await this.orm.call('mail.mail','unarchive_mail',[mail])
      }
      /**
     * Method to resend the mail.
     * @param {Object} event - Event object.
     */
    async resendMail(){
      var mail = this.props.mail.id
      await this.orm.call('mail.mail','retry_mail',[mail])
    }
    /**
     * Method to delete the mail.
     * @param {Object} event - Event object.
     */
    async deleteMail(event){
       var mail = this.props.mail.id
       await this.orm.call('mail.mail','delete_checked_mail',[mail])
    }
    /**
     * Method to star or unstar the mail.
     * @param {Object} event - Event object.
     */
    async starMail(event){
        this.state.starred = !this.state.starred
        var mail = this.props.mail.id
        this.props.starMail(mail, this.state.starred)
        await this.orm.call('mail.mail','star_mail',[mail])
    }
    /**
     * Method to open the mail.
     * @param {Object} event - Event object.
     */
   async openMail(event){
     var mail = this.props.mail
     this.props.openMail(mail)
   }
}
MailBody.template = 'MailBody'
