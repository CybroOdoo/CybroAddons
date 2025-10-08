/* @odoo-module*/
import { registry } from '@web/core/registry';
import { Component , useRef , useState, onWillStart ,onMounted} from '@odoo/owl'
import { useService } from "@web/core/utils/hooks";
import { MailBody } from './MailBody'
import { SentMail } from './SentMail'
import { MessageView } from './MessageView'
import { ComposeMail } from './ComposeMail'
import { ImportDialog } from './AttachmentMail'
import { session } from "@web/session";
/**
 * odooMail component for handling mail-related functionalities.
 * @extends Component
 */
class odooMail extends  Component {
    setup() {
        this.mailState = useState({
            loadLogo: "",
            loadMail: [],
            getCount: "",
            outBox: "",
            mode: "tree",
            formData: {},
            mailType: "all"
        })
        this.dialogService = useService("dialog")
        this.root = useRef('root');
        this.action = useService('action')
        this.orm = useService('orm')
        this.selectedMails = []
        onMounted(() => {
            this.allMailView()
        })
        onWillStart(async ()=> {
            this.mailState.loadLogo = await this.orm.call('mail.icon','load_logo',[])
//            this.allMailView()
            this.getCount()
        })
    }
     /**
     * Method to get the count of different mail categories.
     */
    async getCount(){
        this.mailState.getCount = await this.orm.call('mail.mail','get_mail_count',[])
    }
    /**
     * Method to compose a new mail.
     */
    async composeMail(){
     this.dialogService.add(ComposeMail, {
        loadMail: (mail) => {
            this.mailState.loadMail.unshift(mail)
            this.getCount()
        }
     })
    }
    /**
     * Method triggered on click of the "Select All" checkbox.
     * @param {Object} ev - Event object.
     */
    onClickSelectAll(ev) {
        const checked = ev.target.checked
        this.env.bus.trigger("SELECT:ALL", { checked })
    }
    /**
     * Getter method to get props for MailBody component.
     * @returns {Object} - Props for MailBody component.
     */
    get mailProps() {
        return {
            onSelectMail: this.onSelectMail.bind(this),
            starMail: this.starMail.bind(this),
            openMail: this.openMail.bind(this),
            mailType: this.mailType,
        }
    }
       /**
     * Method to reset the mail view.
     */
    resetView(){
        this.mailState.formData = {}
        this.mailState.mode = "tree"
    }
    /**
     * Method to open a specific mail.
     * @param {Object} mail - Mail object.
     */
    openMail(mail) {
        this.mailState.formData = mail
        this.mailState.mode = "form"
    }
     /**
     * Method to star or unstar a mail.
     * @param {Number} mail - Mail ID.
     * @param {Boolean} type - Type of action (star or unstar).
     */
    starMail(mail, type){
        if (type) {
            this.mailState.getCount.starred_count ++
        }
        else this.mailState.getCount.starred_count --
    }
     /**
     * Method triggered on selecting or deselecting a mail.
     * @param {Number} mailId - Mail ID.
     * @param {Boolean} check - Checked or not.
     */
    onSelectMail(mailId, check) {
        if (check) {
            this.selectedMails.push(mailId)
        }
        else {
            this.selectedMails.filter(item => item !== mailId)
        }
    }
    /**
     * Getter method to get the mail type.
     * @returns {String} - Current mail type.
     */
    get mailType() {
        return this.mailState.mailType
    }
      /**
     * Method to archive selected mails.
     * @param {Object} event - Event object.
     */
    async archiveMail(event){
          if (this.selectedMails.length){
                this.mailState.loadMail = this.mailState.loadMail.filter(item => !this.selectedMails.includes(item.id))
                 await this.orm.call('mail.mail','archive_mail',[this.selectedMails])
                 this.getCount()
                 this.selectedMails = []
            }
    }
    /**
     * Method to refresh the page.
     * @param {Object} event - Event object.
     */
    refreshPage(event){
      window.location.reload()
    }
     /**
     * Method to delete selected mails.
     * @param {Object} event - Event object.
     */
    async deleteMail(event){
            if (this.selectedMails.length){
                this.mailState.loadMail = this.mailState.loadMail.filter(item => !this.selectedMails.includes(item.id))
                 await this.orm.call('mail.mail','delete_mail',[this.selectedMails])
                 this.getCount()
                 this.selectedMails = []
            }
    }
    /**
     * Method to view all mails.
     */
    async allMailView(){
            await $(this.root.el.querySelector('.all_mail')).addClass('active');
            $(this.root.el.querySelector('.archieved-mail')).removeClass('active');
            $(this.root.el.querySelector('.sent-mail')).removeClass('active');
            $(this.root.el.querySelector('.outbox')).removeClass('active');
            $(this.root.el.querySelector('.sent')).removeClass('active');
        this.mailState.mailType = 'all'
        this.resetView()
        this.mailState.loadMail = await this.orm.searchRead('mail.mail',[['create_uid', '=', session.uid]],[], { order: "create_date desc"})
    }
      /**
     * Method to view starred mails.
     */
    async starredMail(){
        $(this.root.el.querySelector('.sent-mail')).addClass('active');
        $(this.root.el.querySelector('.archieved-mail')).removeClass('active');
        $(this.root.el.querySelector('.outbox')).removeClass('active');
        $(this.root.el.querySelector('.sent')).removeClass('active');
        $(this.root.el.querySelector('.all_mail')).removeClass('active');
        this.mailState.mailType = "starred"
        this.resetView()
        this.mailState.loadMail = await this.orm.call('mail.mail','get_starred_mail',[])
    }
     /**
     * Method to view archived mails.
     */
    async archivedMail(){
        $(this.root.el.querySelector('.archieved-mail')).addClass('active');
        $(this.root.el.querySelector('.sent-mail')).removeClass('active');
        $(this.root.el.querySelector('.outbox')).removeClass('active');
        $(this.root.el.querySelector('.sent')).removeClass('active');
        $(this.root.el.querySelector('.all_mail')).removeClass('active');
        this.mailState.mailType = 'archive'
        this.resetView()
        this.mailState.loadMail = await this.orm.call('mail.mail','get_archived_mail',[])
    }
     /**
     * Method to view outbox mails.
     */
   async outboxMailView(){
   $(this.root.el.querySelector('.outbox')).addClass('active');
   $(this.root.el.querySelector('.archieved-mail')).removeClass('active');
   $(this.root.el.querySelector('.sent-mail')).removeClass('active');
   $(this.root.el.querySelector('.sent')).removeClass('active');
   $(this.root.el.querySelector('.all_mail')).removeClass('active');
    this.mailState.mailType = "outbox"
    this.resetView()
    this.mailState.loadMail = await this.orm.searchRead('mail.mail',[['create_uid', '=', session.uid],['state', '=', 'exception']],[], { order: "create_date desc"})
    }
      /**
     * Method to view sent mails.
     */
    async sentMail(){
       $(this.root.el.querySelector('.sent')).addClass('active');
       $(this.root.el.querySelector('.archieved-mail')).removeClass('active');
       $(this.root.el.querySelector('.sent-mail')).removeClass('active');
       $(this.root.el.querySelector('.outbox')).removeClass('active');
       $(this.root.el.querySelector('.all_mail')).removeClass('active');
    this.resetView()
    this.mailState.loadMail = await this.orm.searchRead('mail.mail',[['create_uid', '=', session.uid],['state', '=', 'sent']],[], { order: "create_date desc"})
    }
    /**
     * Method to redirect to the calendar view.
     */
     redirectCalender(){
     this.action.doAction({
                name: "Calender",
                type: 'ir.actions.act_window',
                res_model: 'calendar.event',
                view_mode: 'calendar,tree',
                view_type: 'calendar',
                views: [[false, 'calendar'], [false, 'tree']],
                target: 'current',
            });
    }
     /**
     * Method to redirect to the notes view.
     */
    redirectNote(){
    this.action.doAction({
               name: "Notes",
                type: 'ir.actions.act_window',
                res_model: 'note.note',
                view_mode: 'kanban,form,tree,activity',
                view_type: 'kanban',
                views: [[false, 'kanban'], [false, 'form'], [false, 'tree'], [false, 'activity']],
                target: 'current',
            });
    }
     /**
     * Method to redirect to the contacts view.
     */
    redirectContacts(){
    this.action.doAction({
                name: "Contacts",
                type: 'ir.actions.act_window',
                res_model: 'res.partner',
                view_mode: 'kanban,form,tree,activity',
                view_type: 'kanban',
                views: [[false, 'kanban'], [false, 'form'], [false, 'tree'], [false, 'activity']],
                target: 'current',
            });
    }
    /**
     * Method to search mails based on user input.
     */
    searchMail(){
      var value= this.root.el.querySelector(".header-search-input").value.toLowerCase()
      var inboxItems = this.root.el.querySelectorAll(".inbox-message-item");
      inboxItems.forEach(item => {
      var itemText = item.textContent.toLowerCase();
      item.style.display = itemText.includes(value) ? "" : "none";
    })
    }
}
odooMail.template = 'OdooMail'
odooMail.components = {
    MailBody, SentMail, ComposeMail,MessageView,ImportDialog
}
registry.category('actions').add('odoo_mail', odooMail);
