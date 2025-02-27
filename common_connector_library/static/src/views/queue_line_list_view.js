/** @odoo-module **/

import { registry } from "@web/core/registry";
import { listView } from "@web/views/list/list_view";
import { ListRenderer } from "@web/views/list/list_renderer";
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart } from "@odoo/owl";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

import { QueueLineEptDashBoard } from '@common_connector_library/views/queue_line_dashboard';

export class QueueLineEptDashboardRenderer extends ListRenderer {};

QueueLineEptDashboardRenderer.template = 'common_connector_library.QueueLineEptListView';


QueueLineEptDashboardRenderer.components= Object.assign({}, ListRenderer.components, {QueueLineEptDashBoard});

export const QueueLineEptDashBoardListView = {
    ...listView,
    Renderer: QueueLineEptDashboardRenderer,
};

registry.category("views").add("queue_line_ept_dashboard", QueueLineEptDashBoardListView);
