# See LICENSE file for full copyright and licensing details.

#Configuration data,

# minimum date to search, can be use to limit the load of data
MIN_DATE = '2000-01-01'

# corresponding field, this dictionary content the current mapping of fields identified betwen version
MAP_FIELDS_V7 = {'account.invoice': {
                    'invoice_line_ids': 'invoice_line',
                    'tax_line_ids': 'tax_line',
                    'payment_term_id': 'payment_term'},
                'account.invoice.line': {'invoice_line_tax_ids': 'invoice_line_tax_id'},
                'account.payment': {'communication': 'name', 'name': 'number'}
                }
MAP_FIELDS_V10 = {}

MAP_FIELDS = {'7': MAP_FIELDS_V7,
             '8': {},
             '9': {},
             '10': MAP_FIELDS_V10,
             '11': {},
             '12': {},
             '13': {},
             '14': {},
             '15': {},
             }

# Default field to use when searching the corresponding object
MAPING_SEARCH = {
            'res.currency': ['name'],
            'account.account': ['code'],
            'account.tax': ['name'],
            'account.journal': ['name'],
            'res.users': ['login'],
            'account.invoice': ['number'],
            }

# Option to use when the object is created in automatique mode
OPTIONS_OBJ = {
    'res.company': {'except_fields': ['parent_id', 'user_ids'], 'auto_update': True},
    'ir.module.module': {'domain': [('state', '=', 'installed')], 'auto_search': True},
    'res.currency': {'auto_search': True},
    'res.bank': {'auto_create': True},
    'res.partner.bank': {'auto_create': True},
    'res.groups': {'auto_search': True},
    'res.users': {'except_fields': ['alias_id', 'groups_id', 'action_id'], 'auto_search': True},
    'res.partner': {'except_fields': ['commercial_partner_id', 'message_follower_ids', 'signup_expiration',
            'signup_token', 'category_id'],
            'auto_search': True, 'auto_create': True},
    'uom.uom': {'auto_search': True},
    'product.category': {'auto_search': True, 'auto_create': True, 'auto_update': True},
    'product.template':  {'auto_create': True, 'auto_update': True},
    'product.product':  {'auto_create': True, 'auto_update': True},
    'account.tax': {'auto_search': True},
    'stock.location.route': {'auto_search': True},
    'product.color': {'auto_create': True, 'auto_update': True},
    'product.material': {'auto_create': True, 'auto_update': True},
    'product.manufacturing.area':	 {'auto_create': True, 'auto_update': True},
    'product.type': {'auto_create': True, 'auto_update': True},
    'res.country': {'auto_search': True},
    'res.country.state': {'auto_search': True, 'auto_create': True, 'auto_update': True},
    'res.partner.title': {'auto_search': True, 'auto_create': True, 'auto_update': True},
    'crm.team': {'auto_search': True, 'auto_create': True, 'auto_update': True},
    'account.journal': {'auto_search': True},

    }




