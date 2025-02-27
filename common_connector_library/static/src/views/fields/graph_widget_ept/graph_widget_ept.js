/** @odoo-module **/

import { loadBundle } from "@web/core/assets";
import { registry } from "@web/core/registry";
import { getColor, hexToRGBA } from "@web/core/colors/colors";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

import { Component, onWillStart, useEffect, useRef } from "@odoo/owl";
import { cookie } from "@web/core/browser/cookie";
import { useService } from "@web/core/utils/hooks";
import { loadJS } from "@web/core/assets";

export class EmiproDashboardGraph extends Component {
    static template = "common_connector_library.EmiproDashboardGraph";
    static props = {
        ...standardFieldProps,
        graphType: String,
    };

    constructor() {
        super(...arguments);
        this.selectedOption = "";
    }

    setup() {
        super.setup();
        this.chart = null;
        this.orm = useService("orm");
        this.action = useService('action');
        this.canvasRef = useRef("canvas");
        this.data = ''
        if(this.props.record.data[this.props.name]) {
            this.data = JSON.parse(this.props.record.data[this.props.name]);
        }
        this.order_data = this.props.record.data
        if (this.order_data){
            this.match_key = Object.keys(this.order_data).find(function(key) {
                return key.includes('_order_data');
            });
            this.graph_data = this.match_key && this.order_data[this.match_key] ? JSON.parse(this.order_data[this.match_key]) : {}
            this.context = this.props.record.context
            this.props.graph_data = this.graph_data
        }
        onWillStart(async () => {
            await loadBundle("web.chartjs_lib")
            await loadJS("/web/static/lib/jquery/jquery.js");
        });

        useEffect(() => {
            this.renderChart();
            return () => {
                if (this.chart) {
                    this.chart.destroy();
                }
            };
        });
    }

    /**
     * Instantiates a Chart (Chart.js lib) to render the graph according to
     * the current config.
     */
    renderChart(currentTarget) {
        if (!currentTarget) {
            return;
        }
        if (this.chart) {
            this.chart.destroy();
        }
        let config;
        if (this.props.graphType === "line") {
            config = this.getLineChartConfig();
        }

        this.chart = new Chart(this.canvasRef.el, config);
        $(currentTarget).parent('div').find('.ep_graph_details .col-3 > h4 span').html(this.graph_data.currency_symbol + this.graph_data.total_sales)
        if(this.graph_data.total_sales && this.graph_data.order_data && this.graph_data.order_data.order_count){
            if(this.graph_data.order_data.order_count != 0){
                $(currentTarget).parent('div').find('.ep_graph_details .col-5 b').html(this.graph_data.currency_symbol + Math.round(this.graph_data.total_sales / this.graph_data.order_data.order_count))
            } else {
                $(currentTarget).parent('div').find('.ep_graph_details .col-5 b').html(this.graph_data.currency_symbol + this.graph_data.order_data.order_count)
            }
        }
        if(this.graph_data && this.graph_data.graph_sale_percentage && this.graph_data.sort_on != 'all'){
            $(currentTarget).parent('div').find('.ep_graph_details .col-4 img').attr('src', this.graph_data.graph_sale_percentage.type == 'positive' ? '/common_connector_library/static/src/img/growth-up.svg' : '/common_connector_library/static/src/img/growth-down.svg')
            $(currentTarget).parent('div').find('.ep_graph_details .col-4 h4').attr('style', this.graph_data.graph_sale_percentage.type == 'positive' ? 'color:#5cbc2a' : 'color:#ff5a5a')
            $(currentTarget).parent('div').find('.ep_graph_details .col-4 h4 b > span:first-child').html(this.graph_data.graph_sale_percentage.value)
        }

        $(currentTarget).parent('div').find('#instance_product > p:first-child').html(this.graph_data.product_date && this.graph_data.product_date.product_count ? this.graph_data.product_date.product_count: 0);
        $(currentTarget).parent('div').find('#instance_customer > p:first-child').html(this.graph_data.customer_data && this.graph_data.customer_data.customer_count ? this.graph_data.customer_data.customer_count : 0);
        $(currentTarget).parent('div').find('#instance_order > p:first-child').html(this.graph_data.order_data && this.graph_data.order_data.order_count ? this.graph_data.order_data.order_count : 0);
        $(currentTarget).parent('div').find('#instance_order_shipped > p:first-child').html(this.graph_data.order_shipped && this.graph_data.order_shipped.order_count ? this.graph_data.order_shipped.order_count : 0);
        $(currentTarget).parent('div').find('#instance_refund > p:first-child').html(this.graph_data.refund_data && this.graph_data.refund_data.refund_count ? this.graph_data.refund_data.refund_count : 0);
    }
    getLineChartConfig() {
        const labels = this.graph_data && this.graph_data.values && this.graph_data.values.map(function (pt) {
            return pt.x;
        });
        const color10 = getColor(10, cookie.get("color_scheme"));
        const borderColor = this.graph_data && this.graph_data.is_sample_data ? hexToRGBA(color10, 0.1) : color10;
        const backgroundColor = this.graph_data.is_sample_data
            ? hexToRGBA(color10, 0.05)
            : hexToRGBA(color10, 0.2);
        return {
            type: "line",
            data: {
                labels: labels,
                datasets: [
                    {
                        data: this.graph_data.values || '',
                        fill: "start",
                        label: this.graph_data.key || '',
                        backgroundColor: backgroundColor,
                        borderColor: borderColor,
                        borderWidth: 2,
                        pointStyle: 'line',
                    },
                ],
            },
            options: {
                plugins: {
                    legend: { display: false },
                     tooltip: {
                        intersect: false,
                        position: "nearest",
                        caretSize: 0,
                    },
                },
                scales: {
                    x: {
                        position: 'bottom'
                    },
                    y: {
                        position: 'left',
                        ticks: {
                            beginAtZero: true
                        },
                    }
                },
                maintainAspectRatio: false,
                elements: {
                    line: {
                        tension: 0.5,
                    },
                },
            },
        };
    }

    updateGraphData(newData, currentTarget) {
        this.graph_data = newData;
        this.renderChart(currentTarget);
    }

    onchangeSortOrderData(e) {
        var self = this;
        var context = {...this.context}
        context.sort = e.currentTarget.value
        var currentTarget = e.currentTarget
        return this.orm.call(
            this.props.record.resModel,
            "read",
            [this.props.record.resId], {context: context}
        ).then(function (result) {
            if(result.length) {
                self.updateGraphData(JSON.parse(result[0][self.match_key]), currentTarget);
            }
        })
    }

    /*Render action for  Products */
    _getProducts() {
        return this.action.doAction(this.graph_data.product_date.product_action);
    }

    /*Render action for  Customers */
    _getCustomers() {
        return this.action.doAction(this.graph_data.customer_data.customer_action);
    }

    /*Render action for  Sales Order */
    _getOrders() {
        return this.action.doAction(this.graph_data.order_data.order_action);
    }

    /*Render action for  shipped Order */
    _getShippedOrders() {
        return this.action.doAction(this.graph_data.order_shipped.order_action);
    }

    _getRefundOrders() {
        return this.action.doAction(this.graph_data.refund_data.refund_action);
    }

    _getReport() {
        var self = this;
        return this.orm.call(
            this.props.record.resModel,
            "open_report",
            [this.props.record.resId],
        ).then(function (result) {
            self.action.doAction(result)
        })
    }

    _getLog() {
        var self = this;
        return this.orm.call(
            this.props.record.resModel,
            "open_logs",
            [this.props.record.resId],
        ).then(function (result) {
            self.action.doAction(result)
        })
    }

    /*Render(Open)  Operations wizard*/
    _performOpration() {
        var self = this;
        return this.orm.call(
            this.props.record.resModel,
            "perform_operation",
            [this.props.record.resId],
        ).then(function (result) {
            self.action.doAction(result)
        })
    }
}

export const emiproDashboardGraph = {
    component: EmiproDashboardGraph,
    supportedTypes: ["text"],
    extractProps: ({ attrs }) => ({
        graphType: attrs.graph_type,
    }),
};

registry.category("fields").add("dashboard_graph_ept", emiproDashboardGraph);