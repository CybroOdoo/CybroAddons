/** @odoo-module **/

import { Component } from "@odoo/owl";
import { Layout } from "@web/search/layout";
import { useService } from "@web/core/utils/hooks";
import { useModel } from "@web/model/model";
import { SearchBar } from "@web/search/search_bar/search_bar";
import { useSearchBarToggler } from "@web/search/search_bar/search_bar_toggler";
import { CogMenu } from "@web/search/cog_menu/cog_menu";
import { Pager } from "@web/core/pager/pager";
import { usePager } from "@web/search/pager_hook";
import { MapRenderer } from "./map_renderer";

export class MapController extends Component {
    static template = "odoo_web_map.MapController";
    static components = { Layout, MapRenderer, SearchBar, CogMenu, Pager };
    static props = {
        "*": true,
    };

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.searchBarToggler = useSearchBarToggler();

        this.pager = usePager(() => {
            return {
                offset: this.model.metaData.offset || 0,
                limit: this.model.metaData.limit || 80,
                total: this.model.metaData.count || 0,
                onUpdate: async ({ offset, limit }) => {
                    await this.model.load({ offset, limit });
                    this.render();
                },
            };
        });

        this.model = useModel(this.props.Model, {
            resModel: this.props.resModel,
            domain: this.props.domain,
            context: this.props.context,
            limit: 30,
            offset: 0,
            config: this.props.archInfo, // Pass parsed arch info to model
        });
    }

    get display() {
        return {
            ...this.props.display,
        };
    }

    get pagerProps() {
        return this.pager.props;
    }



    openRecord(record) {
        this.action.switchView("form", { resId: record.id });
    }


}
