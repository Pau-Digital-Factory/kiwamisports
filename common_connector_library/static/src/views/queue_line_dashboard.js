/** @odoo-module */
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart } from "@odoo/owl";
import { makeContext } from "@web/core/context";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { rpc } from "@web/core/network/rpc";
import { loadJS } from "@web/core/assets";

export class QueueLineEptDashBoard extends Component {

    setup() {
        super.setup();
        this.orm = useService("orm");
        this.action = useService("action");
        this.rpc = rpc;

        onWillStart(async () => {
            await loadJS("/web/static/lib/jquery/jquery.js");
            this.model = $(this.env.config.viewArch).attr('dashboard_model')

            if ($(this.env.config.viewArch).find('field[name="name"]').attr('context') && JSON.parse($(this.env.config.viewArch).find('field[name="name"]').attr('context')).dashboard_model) {
                this.model = JSON.parse($(this.env.config.viewArch).find('field[name="name"]').attr('context')).dashboard_model
                this.queue_line_model = JSON.parse($(this.env.config.viewArch).find('field[name="name"]').attr('context')).queue_line_model
                this.queue_type_shipped = JSON.parse($(this.env.config.viewArch).find('field[name="name"]').attr('context')).shipped
                this.queue_type_unshipped = JSON.parse($(this.env.config.viewArch).find('field[name="name"]').attr('context')).unshipped
                this.queue_type_wfs = JSON.parse($(this.env.config.viewArch).find('field[name="name"]').attr('context')).wfs
            }

            if (this.model){

                var context = {}
                if (this.queue_type_unshipped) {
                    context.unshipped = true
                } else if (this.queue_type_shipped){
                    context.shipped = true
                } else if (this.queue_type_wfs){
                    context.wfs = true
                }
                this.values = await this.orm.call(this.model, "retrieve_dashboard", [], {
                    context: context,
                });
            }
        });
    }

    /**
     * This method clears the current search query and activates
     * the filters found in `filter_name` attribute from button pressed
     */
    setSearchContext(ev) {

        const filter_name = ev.currentTarget.getAttribute("filter_name");
        const filters = filter_name.split(",");
        const searchItems = this.env.searchModel.getSearchItems((item) =>
            filters.includes(item.name)
        );
        this.env.searchModel.query = [];
        for (const item of searchItems) {
            this.env.searchModel.toggleSearchItem(item.id);
        }
    }


    /**
     * This method clears the current search query and activates
     * the action found in given model name abd display there records
     */

    async onActionClicked(e) {

        e.preventDefault();
        var $action = $(e.currentTarget);
        var model = this.queue_line_model;
        var context = JSON.parse($action.attr('context'));

        model && this.values && this.action.doAction({
            name: $action.attr('title'),
            res_model: model,
            domain: [['id', 'in', this.values[context['action']][1]]],
            context: context,
            views: [[false, 'list'], [false, 'form']],
            type: 'ir.actions.act_window',
            view_mode: "list"
        });

    }

}

QueueLineEptDashBoard.template = "common_connector_library.QueueLineDashboard";
