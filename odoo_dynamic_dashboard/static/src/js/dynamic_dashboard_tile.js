/** @odoo-module **/
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";
const { Component, xml } = owl;

export class DynamicDashboardTile extends Component {
    // Setup function of the class DynamicDashboardTile
    setup() {
        this.doAction = this.props.doAction.doAction;
        this.dialog = this.props.dialog;
        this.orm = this.props.orm;
    }
    // Function to get the configuration of the tile
    async getConfiguration(ev){
        ev.stopPropagation();
        ev.preventDefault();
        var id = this.props.widget.id
        await this.doAction({
              type: 'ir.actions.act_window',
              res_model: 'dashboard.block',
              res_id: id,
              view_mode: 'form',
              views: [[false, "form"]]
          });
    }
    // Function to remove the tile
    async removeTile(ev){
        ev.stopPropagation();
        ev.preventDefault();
        this.dialog.add(ConfirmationDialog, {
            title: _t("Delete Confirmation"),
            body: _t("Are you sure you want to delete this item?"),
            confirmLabel: _t("YES, I'M SURE"),
            cancelLabel: _t("NO, GO BACK"),
            confirm: async () => {
                await this.orm.unlink("dashboard.block", [this.props.widget.id]);
                location.reload();
            },
            cancel: () => {},
        });
    }
    // Function for getting records by double click
    async getRecords(){
        var model_name = this.props.widget.model_name;
        if (model_name){
            await this.doAction({
              type: 'ir.actions.act_window',
              res_model: model_name,
              view_mode: 'tree',
              views: [[false, "tree"]],
              domain: this.props.widget.domain,
          });
        }
    }
}
DynamicDashboardTile.template = xml `
    <div class="resize-drag tile"
        t-on-dblclick="getRecords"
        t-att-data-id="this.props.widget.id"
        t-att-data-x="this.props.widget.data_x"
        t-att-data-y="this.props.widget.data_y"
        t-att-style="this.props.widget.color+this.props.widget.text_color+ 'height:'+this.props.widget.height+';width:'+this.props.widget.width + '; transform: translate('+ this.props.widget.translate_x +', '+ this.props.widget.translate_y +');'">
        <div t-att-style="this.props.widget.color+this.props.widget.text_color"
            class="d-flex align-items-center  w-100  my-3">
            <a class="block_setting tile_edit tile-container__setting-icon" style="color:black;" t-on-click="(ev) => this.getConfiguration(ev)" >
                <i class="fa fa-edit"/>
            </a>
            <a class="block_delete tile_edit tile-container__delete-icon" style="color:black;" t-on-click="(ev) => this.removeTile(ev)">
                <i class="fa fa-times"/>
            </a>
            <div t-att-style="this.props.widget.icon_color"
                 class="tile-container__icon-container bg-white d-flex justify-content-center align-items-center">
                <i t-att-class="this.props.widget.icon"/>
            </div>
            <div t-att-style="this.props.widget.text_color"
                 class="tile-container__status-container">
                <h2 t-att-style="this.props.widget.text_color"
                    class="status-container__title">
                    <t t-esc="this.props.widget.name"/>
                </h2>
                <div class="status-container__figures d-flex flex-wrap align-items-baseline">
                    <h3 class="mb-0 mb-md-1 mb-lg-0 mr-1"
                        t-att-style="this.props.widget.val_color">
                        <t t-esc="this.props.widget.value"/>
                    </h3>
                </div>
            </div>
        </div>
    </div>`