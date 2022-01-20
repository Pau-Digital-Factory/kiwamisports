# See LICENSE file for full copyright and licensing details.

import logging
from odoo import api, fields, models
from odoo.tools.translate import _
from . import synchro_data

MAP_FIELDS = synchro_data.MAP_FIELDS
OPTIONS_OBJ = synchro_data.OPTIONS_OBJ


class BaseSynchroServer(models.Model):
    """Class to store the information regarding server."""
    _name = "synchro.server"
    _description = "Synchronized server"

    name = fields.Char(
        string='Server name',
        required=True
    )
    server_protocol = fields.Selection(
        [('http', 'HTTP'),
         ('https', 'HTTPS'),
         ('https_1', 'HTTPS TLSv1'),
         ('https_1_1', 'HTTPS TLSv1_1'),
         ('https_1_2', 'HTTPS TLSv1_2'),
         ],
        string='Protocol',
        default='http',
        required=True
    )
    server_url = fields.Char(
        string='Server URL',
        required=True
    )
    server_port = fields.Integer(
        string='Server Port',
        required=True,
        default=8069
    )
    server_db = fields.Char(
        string='Server Database',
        required=True
    )
    login = fields.Char(
        string='User Name',
        required=True
    )
    password = fields.Char(
        string='Password',
        required=True
    )
    server_version = fields.Selection(
        [('6', 'Version 6.1'),
         ('7', 'Version 7.0'),
         ('8', 'Version 8.0'),
         ('9', 'Version 9.0'),
         ('10', 'Version 10.0'),
         ('11', 'Version 11.0'),
         ('12', 'Version 12.0'),
         ('13', 'Version 13.0'),
         ('14', 'Version 14.0'),
         ('15', 'Version 15.0'),
         ],
        string='Version',
        default='14',
        required=True
    )

    obj_ids = fields.One2many(
        'synchro.obj',
        'server_id',
        string='Models',
        ondelete='cascade'
    )

    def get_map_fields(self):
        " Return a mapping field to do by odoo object, it's a pre-configuration by version"
        self.ensure_one()
        if self.server_version:
            return MAP_FIELDS.get(self.server_version, {})
        else:
            return {}

    def get_obj(self, model_name=''):
        "return the object with model_name"
        self.ensure_one()
        obj_condition = [('model_id.model', '=', model_name),
                         ('server_id', '=', self.id)]
        obj_ids = self.env['synchro.obj'].search(obj_condition)

        if not obj_ids:
            obj_ids = self.create_obj([model_name])
        return obj_ids and obj_ids[0] or obj_ids

    def create_obj(self, object_list):
        "create object to synchronyze"
        res = self.env['synchro.obj']
        for server in self:
            for base_object in object_list:
                if not server.obj_ids.search([
                                    ('model_id.model', '=', base_object),
                                    ('server_id', '=', server.id)]):

                    model_condition = [('model', '=', base_object)]
                    model_ids = self.env['ir.model'].search(model_condition)
                    if model_ids:
                        obj_vals = {
                            'name': base_object,
                            'model_name': base_object,
                            'server_id': server.id,
                            'sequence': model_ids[0].id,
                            'model_id': model_ids[0].id,
                            }
                        new_obj = self.env['synchro.obj'].create(obj_vals)
                        new_obj.update_field()
                        res |= new_obj
                    else:
                        raise Warning(_('This object is not available: %s' % (base_object)))
        return res

    def remote_company_ids(self):
        "initialized domain for remote company, used when there are multicompany"
        # Domain company
        self.ensure_one()
        obj_company_ids = self.obj_ids.search([
                    ('model_id.model', '=', 'res.company'),
                    ('server_id', '=', self.id)])

        if not obj_company_ids:
            raise Warning(_('''There is no company to migrate. Please add one on mapping'''))

        company_ids = []
        for obj in obj_company_ids:
            for line in obj.line_id:
                if line.local_id:
                    company_ids.append(line.remote_id)

        return company_ids

    def migrate_obj(self, obj_name, options={}):
        "migrate standard objet"
        self.ensure_one()
        options = options or OPTIONS_OBJ.get(obj_name, {})
        obj_obj = self.get_obj(obj_name)

        if options.get('auto_search'):
            obj_obj.auto_search = True
        if options.get('auto_create'):
            obj_obj.auto_create = True
        if options.get('auto_update'):
            obj_obj.auto_update = True
        if options.get('domain'):
            obj_obj.domain = options.get('domain')

        except_fields = options.get('except_fields', [])
        obj_obj.update_remote_field(except_fields=except_fields)
        obj_obj.check_childs()
        obj_obj.state = 'manual'
        return obj_obj

    def migrate_base(self):
        "migrate base object"
        self.ensure_one()

        company_obj = self.migrate_obj('res.company')
        self.migrate_obj('ir.module.module')
        self.migrate_obj('res.currency')
        bank_obj = self.migrate_obj('res.bank')
        self.migrate_obj('res.partner.bank')
        self.migrate_obj('res.groups')
        self.migrate_obj('res.users')
        self.migrate_obj('res.partner')

        remote_company_ids = self.remote_company_ids()
        company_values = company_obj.remote_read(remote_company_ids)
        company_obj.write_local_value(company_values)

        bank_ids = bank_obj.remote_search([])
        for bank_id in bank_ids:
            bank_obj.get_local_id(bank_id)

