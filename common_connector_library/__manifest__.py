# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
{
    'name': 'Common Connector Library',
    'version': '18.0.0.7',
    'category': 'Sales',
    'license': 'OPL-1',
    'author': 'Emipro Technologies Pvt. Ltd.',
    'website': 'http://www.emiprotechnologies.com',
    'maintainer': 'Emipro Technologies Pvt. Ltd.',
    'summary': """Develop generalize method to process different operations & auto workflow process to manage
    order process automatically.""",
    'depends': ['stock_delivery', 'sale_management'],
    'data': ['security/ir.model.access.csv',
             'data/ir_sequence.xml',
             'data/ir_cron.xml',
             'data/digest_data.xml',
             'views/stock_quant_package_view.xml',
             'views/common_log_book_view.xml',
             'views/account_fiscal_position.xml',
             'views/common_product_image_ept.xml',
             'views/product_view.xml',
             'views/product_template.xml',
             'views/sale_order_view.xml',
             'views/sale_workflow_process_view.xml',
             'data/automatic_workflow_data.xml',
             'views/common_log_lines_ept.xml',
             'views/digest_views.xml',
             'views/delivery_carrier_view.xml',
             'views/res_partner_view.xml',
             'wizard/stock_return_picking.xml',
             ],
    'installable': True,
    'price': 20.00,
    'currency': 'EUR',
    'images': ['static/description/Common-Connector-Library-Cover.jpg'],
    # cloc settings
    'cloc_exclude': ['**/*.xml', ],
    'assets': {
        'web.assets_backend': [
            '/common_connector_library/static/src/views/**/*',
        ],
    },
}

