
{
    'name': 'custom_kiwami',
    'version': '15.0.1.0.0',
    'summary': 'Technical module permet la synchronisation des information entre shopify et odoo et mettre des modification sur les documents PDF des Factures'
    ' project',
    'author': 'Abdelghani KHALIDI',
    'website': 'https://dkgroup.fr',
    'license': 'AGPL-3',
    'category': 'Generic Modules',
    'depends': ['base','shopify_ept','account'],
    'data': [
        # 'security/ir.model.access.csv',
        #'views/views.xml',
        #'views/templates.xml',
        'views/views.xml',
    ],
    'installable': True,
}
