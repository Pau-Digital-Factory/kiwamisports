# See LICENSE file for full copyright and licensing details.

import time
import logging
# import threading
from odoo import api, fields, models
from odoo.models import MAGIC_COLUMNS
from . import odoo_proxy
from . import synchro_data

_logger = logging.getLogger(__name__)

MAPING_SEARCH = synchro_data.MAPING_SEARCH
MIN_DATE = synchro_data.MIN_DATE


class BaseSynchroObjDepend(models.Model):
    """Class many2many hiearchy depend object."""
    _name = "synchro.obj.depend"
    _description = "Relation order unter object"

    child_id = fields.Many2one('synchro.obj', 'child')
    parent_id = fields.Many2one('synchro.obj', 'parent')


class BaseSynchroObj(models.Model):
    """Class to store the migration configuration by object."""
    _name = "synchro.obj"
    _description = "Register Class"
    _order = 'sequence'

    name = fields.Char(
        string='Name',
        required=True
    )
    auto_create = fields.Boolean(
        string='Create',
    )
    auto_update = fields.Boolean(
        string='Update',
    )
    auto_search = fields.Boolean(
        string='Search',
    )
    domain = fields.Char(
        string='Remote Domain',
        required=True,
        default='[]'
    )
    search_field = fields.Char(
        string='Search field',
        help='define a search field if it is not name, example: code, default_code...'
    )
    server_id = fields.Many2one(
        'synchro.server',
        string='Server',
        required=True
    )
    model_id = fields.Many2one(
        'ir.model',
        string='Object to synchronize',
    
    )
    model_name = fields.Char(
        string='Remote Object name',
        required=True
    )
    action = fields.Selection(
        [('download', 'Download'),
         ('upload', 'Upload'),
         ('both', 'Both')],
        string='Direction (deprecated)',
        required=True,
        default='download'
    )
    sequence = fields.Integer(
        string='Sequence'
    )
    active = fields.Boolean(
        string='Active',
        default=True
    )
    synchronize_date = fields.Datetime(
        string='Latest Synchronization'
    )
    line_id = fields.One2many(
        'synchro.obj.line',
        'obj_id',
        string='IDs Affected',
        ondelete='cascade'
    )
    avoid_ids = fields.One2many(
        'synchro.obj.avoid',
        'obj_id',
        domain=[('synchronize', '=', False)],
        string='All fields.',

    )
    field_ids = fields.One2many(
        'synchro.obj.avoid',
        'obj_id',
        domain=[('synchronize', '=', True)],
        string='Fields to synchronize',

    )
    child_ids = fields.Many2many(
        comodel_name='synchro.obj',
        relation='synchro_obj_depend',
        column1='parent_id',
        column2='child_id',
        string='Childs',
        ondelete='cascade'
        )

    note = fields.Html("Notes")
    default_value = fields.Text("Defaults values")
    sync_limit = fields.Integer("Load limite by cron", default=1)

    state = fields.Selection(
            [('draft', 'Draft'),
            ('manual', 'Manual'),
            ('auto', 'Auto'),
            ('synchronise', 'Synchronise'),
            ('cancel', 'Cancelled')
            ], string='State', index=True, default='draft')

    def unlink(self):
        "unlink line before"
        for obj in self:
            obj.field_ids.unlink()
            obj.avoid_ids.unlink()
            obj.line_id.unlink()

        ret = super(BaseSynchroObj, self).unlink()
        return ret

    def get_default_value(self):
        " Use default_get"
        for obj in self:
            list_fields = []
            for field_line in obj.field_ids:
                list_fields.append(field_line.field_id.name)
            values = obj.model_id.default_get(list_fields)
            obj.default_value = "%s" % (values)

    @api.onchange('model_id')
    def onchange_field(self):
        "return the name"
        self.model_name = self.model_id.model or ''

    def update_field(self):
        "update the list of local field"
        for obj in self:
            map_fields = obj.server_id.get_map_fields()
            obj.avoid_ids.unlink()
            obj.field_ids.unlink()
            for field_rec in obj.model_id.field_id:
                if field_rec.store and field_rec.name not in MAGIC_COLUMNS:

                    name_V7 = field_rec.name
                    if obj.name in list(map_fields.keys()):
                        if name_V7 in list(map_fields[obj.name].keys()):
                            name_V7 = map_fields[obj.name][name_V7]

                    field_value = {
                        'obj_id': obj.id,
                        'field_id': field_rec.id,
                        'name': name_V7,
                        }
                    self.env['synchro.obj.avoid'].create(field_value)

    def update_remote_field(self, except_fields=[]):
        "update the field who can be synchronized"
        for obj in self:
            remote_odoo = odoo_proxy.RPCProxy(obj.server_id)
            remote_fields = remote_odoo.get(self.model_name).fields_get()

            for local_field in obj.avoid_ids | obj.field_ids:
                if local_field.name in list(remote_fields.keys()):
                    local_field.check_remote = True
                    local_field.remote_type = remote_fields[local_field.name]['type']
                    if local_field.remote_type not in ['one2many']:
                        if local_field.name not in except_fields:
                            local_field.synchronize = True

    def unlink_mapping(self):
        for obj in self:
            obj.line_id.unlink()

    def load_remote_record(self, limit=10):
        "Load remote record"
        limit = self.env.context.get('limit', 0) or limit

        for obj in self:
            already_ids = obj.get_synchronazed_remote_ids()
            domain = [('id', 'not in', already_ids)]

            remote_domain = eval(obj.domain)
            if remote_domain:
                domain += remote_domain
            obj_ids = obj.remote_search(domain)

            if limit and limit < 0:
                pass
            elif limit and len(obj_ids) > limit:
                obj_ids = obj_ids[:limit]

            for obj_id in obj_ids:
                obj_vals = obj.remote_read([obj_id])
                _logger.info("\write_local_value;%s;%s\n%s" % (obj.model_id.model, obj_id, obj_vals))
                obj.write_local_value(obj_vals)

            obj.synchronize_date = fields.Datetime.now()

    def check_childs(self):
        "check the child of this object"
        for obj in self:
            object_list = []
            child_ids = self.env['synchro.obj']
            for rec_field in obj.field_ids:
                if rec_field.field_id.ttype in ['many2one', 'many2many']:
                    obj_name = rec_field.field_id.relation
                    condition = [('model_id.model', '=', obj_name),
                                 ('server_id', '=', obj.server_id.id)]
                    obj_ids = self.search(condition)
                    child_ids |= obj_ids
                    if not obj_ids:
                        object_list.append(obj_name)
            child_ids |= obj.server_id.create_obj(object_list)
            obj.write({'child_ids': [(6, 1, child_ids.ids)]})

    def remote_read(self, remote_ids, remote_fields=[]):
        "read the value of the remote object filter on remote_ids"
        self.ensure_one()
        remote_odoo = odoo_proxy.RPCProxy(self.server_id)
        remote_fields = remote_fields or self.field_ids.mapped('name')
        remote_value = remote_odoo.get(self.model_name).read(
                        remote_ids, remote_fields)
        return remote_value

    def remote_search(self, domain=[]):
        "read the value of the remote object filter on remote_ids"
        self.ensure_one()
        remote_odoo = odoo_proxy.RPCProxy(self.server_id)
        remote_obj = remote_odoo.get(self.model_name)
        remote_domain = eval(self.domain)
        remote_ids = remote_obj.search(remote_domain + domain)
        return remote_ids

    def read_groupby_ids(self, groupby_field, groupby_domain=[]):
        "Return list of remote ids by domain filter"
        self.ensure_one()
        remote_odoo = odoo_proxy.RPCProxy(self.server_id)
        remote_obj = remote_odoo.get(self.model_name)
        remote_domain = eval(self.domain) + groupby_domain

        read_groupby = remote_obj.read_group(remote_domain, [groupby_field], [groupby_field])
        response = []
        for item in read_groupby:
            if item.get(groupby_field):
                remote_id = item[groupby_field][0]
                response.append(remote_id)
        return response

    def default_search_field(self):
        "return the default search field to do mapping"
        self.ensure_one()
        maping_search = MAPING_SEARCH

        if maping_search.get(self.model_name):
            search_field = maping_search[self.model_name]
        else:
            search_field = ['name']
        return search_field

    def search_local_id(self, remote_ids):
        "get the local id associated with remote_ids, save in obj.line"
        # Return a dic {remote_id: local_id, ...}
        self.ensure_one()
        res = {}
        # Get the significative search field like code, name... and read the remote value
        search_fields = self.default_search_field()
        if 'name' in search_fields:
            remote_values = self.remote_read(remote_ids, search_fields)
        else:
            # Add name only to have human description
            remote_values = self.remote_read(remote_ids, search_fields + ['name'])

        for remote_value in remote_values:
            remote_id = remote_value['id']
            local_id = False
            res[remote_id] = False
            description = remote_value.get('name', '???')

            # Construct the condition from the search_fields and search
            condition = []
            description = ''
            for search_field in search_fields:
                search_value = remote_value.get(search_field)
                description = '%s ' % (search_value) + description
                condition.append((search_field, '=', search_value))



            local_ids = self.env[self.model_id.model].search(condition)
            local_id = local_ids and (len(local_ids) == 1) and local_ids[0].id or False


            line_condition = [
                    ('obj_id', '=', self.id),
                    ('remote_id', '=', remote_id)]
            obj_line_ids = self.env['synchro.obj.line'].search(line_condition)
            mapping_line = obj_line_ids and obj_line_ids[0] or obj_line_ids

            if not mapping_line:
                mapping_vals = {
                        'local_id': False,
                        'remote_id': remote_id,
                        'description': description,
                        'obj_id': self.id
                        }
                mapping_line = obj_line_ids.create(mapping_vals)

            if local_id:
                res[remote_id] = local_id
                mapping_line.local_id = local_id

        return res

    def get_void_local_ids(self):
        "return id list of line with no local_id"
        self.ensure_one()
        condition = [('local_id', '=', 0), ('obj_id', '=', self.id)]
        local_ids = self.env['synchro.obj.line'].search(condition)
        res = local_ids.mapped('remote_id')
        return res

    def get_remote_id(self, local_id):
        "Get remote id if exist"
        self.ensure_one()
        condition = [('local_id', '=', local_id), ('obj_id', '=', self.id)]
        remote_ids = self.env['synchro.obj.line'].search(condition)
        if remote_ids:
            return remote_ids[0].remote_id
        else:
            return False

    def get_local_id(self, remote_id, no_create=False, no_search=False, check_local_id=True):
        "return the local_id associated with the remote_id"
        self.ensure_one()
        condition = [('remote_id', '=', remote_id), ('obj_id', '=', self.id)]
        local_ids = self.env['synchro.obj.line'].search(condition)

        if check_local_id:
            # Check if there is a local object pointing by these ids
            checking_local_ids = self.env['synchro.obj.line']
            for checking_local_id in local_ids:
                try:
                    if self.env[self.model_id.model].browse(checking_local_id.local_id):
                        checking_local_ids |= checking_local_id
                except:
                    checking_local_id.unlink()

            local_ids = checking_local_ids

        if local_ids:
            if local_ids[0].local_id:
                return local_ids[0].local_id
            else:
                return False
        else:
            if self.auto_search and not no_search:
                result = self.search_local_id([remote_id])
                if result.get(remote_id):
                    return result[remote_id]

            if self.auto_create and not no_create:

                remote_vals = self.remote_read([remote_id])
                if remote_vals:
                    remote_value = self.exception_value_create(remote_vals[0])
                    local_vals = self.get_local_value(remote_value)
                    new_obj = self.env[self.model_id.model].with_context(skip_account_move_synchronization =True,check_move_validity=False,synchro=True).create(local_vals)
                    # Update line
                    local_ids = self.env['synchro.obj.line'].search(condition)
                    if local_ids:
                        local_ids.write({'local_id': new_obj.id})
                    else:
                        line_vals = {
                            'local_id': new_obj.id,
                            'remote_id': remote_id,
                            'obj_id': self.id
                            }
                        self.env['synchro.obj.line'].create(line_vals)

                    return new_obj.id
                else:
                    return False
            else:
                return False

    def get_many2x_field(self):
        "get list of field type many2x"
        many2x_field = {}

        for sync_field in self.field_ids:
            if sync_field.field_id.ttype in ['many2one', 'many2many']:
                many2x_field[sync_field.name] = {
                    'type': sync_field.field_id.ttype,
                    'model': sync_field.field_id.relation}
        return many2x_field

    def get_ids_many2x(self, remote_values):
        "check id in many2x field"
        self.ensure_one()
        many2x_model = {}
        many2x_field = self.get_many2x_field()

        for remote_field in list(many2x_field.keys()):
            many2x_model[many2x_field[remote_field]['model']] = []

        for remote_value in remote_values:
            for remote_field in list(many2x_field.keys()):
                if many2x_field[remote_field]['type'] == 'many2one':
                    if remote_value[remote_field]:
                        if remote_value[remote_field][0] not in many2x_model[many2x_field[remote_field]['model']]:
                            many2x_model[many2x_field[remote_field]['model']].append(remote_value[remote_field][0])
                if many2x_field[remote_field]['type'] == 'many2many':
                    for remote_id in remote_value[remote_field]:
                        if remote_id not in many2x_model[many2x_field[remote_field]['model']]:
                            many2x_model[many2x_field[remote_field]['model']].append(remote_id)
        return many2x_model

    def check_ids_many2x(self, remote_values):
        "Check ids to load"
        self.ensure_one()
        many2x_model = self.get_ids_many2x(remote_values)

        for model_name in list(many2x_model.keys()):
            sync_obj = self.server_id.get_obj(model_name)
            remote_ids = list(many2x_model[model_name])
            for remote_id in remote_ids:
                if sync_obj.get_local_id(remote_id, no_create=True, no_search=True):
                    many2x_model[model_name].remove(remote_id)
        return many2x_model

    def get_local_value(self, remote_value):
        """get local database the values for man2x field
            values: [{'id': 1, 'name': 'My object name', ....}, {'id': 2, ...}]
            the id field is the remote id and must be set
        """
        self.ensure_one()
        local_value = {}

        for sync_field in self.field_ids:
            if sync_field.field_id.ttype in ['many2one']:
                if remote_value.get(sync_field.name):
                    many2_remote_id = remote_value.get(sync_field.name)[0]
                    many2_obj = self.server_id.get_obj(sync_field.field_id.relation)
                    many2_local_id = many2_obj.get_local_id(many2_remote_id)
                    if many2_local_id:
                        field_name = sync_field.field_id.name
                        local_value.update({field_name: many2_local_id})

            elif sync_field.field_id.ttype in ['many2many']:
                many2_remote_ids = remote_value.get(sync_field.name)
                if many2_remote_ids:
                    many2_obj = self.server_id.get_obj(sync_field.field_id.relation)
                    many2_local_ids = []
                    for many2_remote_id in many2_remote_ids:
                        many2_local_id = many2_obj.get_local_id(many2_remote_id)
                        if many2_local_id:
                            many2_local_ids.append(many2_local_id)
                    if many2_local_ids:
                        field_name = sync_field.field_id.name
                        local_value.update({field_name: [(6, 0, many2_local_ids)]})

            elif sync_field.field_id.ttype in ['date']:
                field_value = remote_value.get(sync_field.name)
                if isinstance(field_value, str):
                    field_value = fields.Date.from_string(field_value)
                field_name = sync_field.field_id.name
                local_value.update({field_name: field_value})

            else:
                field_value = remote_value.get(sync_field.name)
                field_name = sync_field.field_id.name
                local_value.update({field_name: field_value})

        return local_value

    def exception_value_write(self, remote_value):
        "hook exception for value"
        self.ensure_one()

        if self.model_name == 'res.partner':
            type_value = remote_value.get('type')
            if type_value and type_value not in ['invoice', 'contact', 'delivery', 'other']:
                remote_value['type'] = 'contact'

        return remote_value

    def exception_value_create(self, remote_value):
        "hook exception for value"
        self.ensure_one()

        if self.model_name == 'account.move':
            if remote_value.get('state'):
                #no possible to create a done state
                remote_value['state'] = 'draft'

        remote_value = self.exception_value_write(remote_value)
        return remote_value

    def exception_value(self, remote_value):
        "hook exception for value"
        self.ensure_one()

        if self.model_name == 'hr_timesheet.sheet':
            if not remote_value.get('review_policy'):
                remote_value['review_policy'] = 'hr'

        elif self.model_name == 'res.partner':
            type_value = remote_value.get('type')
            if type_value and type_value not in ['invoice', 'contact', 'delivery', 'other']:
                remote_value['type'] = 'contact'

        elif self.model_name == 'sale.order':

            state = remote_value.get('state', '')
            if state in ['draft', 'sent', 'sale', 'done', 'cancel']:
                pass
            elif state in ['waiting_date', 'confirmed', 'progress', 'manual', 'shipping_except', 'invoice_except']:
                remote_value['state'] = 'sent'
            else:
                remote_value['state'] = 'draft'

        elif self.model_name == 'purchase.order':
            state = remote_value.get('state', '')
            if state in ['draft', 'sent', 'to_approve', 'sale', 'done', 'cancel']:
                pass
            elif state in ['confirmed']:
                remote_value['state'] = 'to_approve'
            elif state in ['waiting_date', 'confirmed', 'progress', 'manual', 'shipping_except', 'invoice_except']:
                remote_value['state'] = 'done'
            else:
                remote_value['state'] = 'draft'

        return remote_value

    def write_local_value(self, remote_values):
        """write in local database the values, the values is a list of dic vals
            values: [{'id': 1, 'name': 'My object name', ....}, {'id': 2, ...}]
            the id field is the remote id and must be set
        """
        self.ensure_one()

        for remote_value in remote_values:
            remote_id = remote_value.get('id')
            local_id = self.get_local_id(remote_id, no_create=True)

            if local_id and self.auto_update:
                # Write
                remote_value = self.exception_value_write(remote_value)
                local_value = self.get_local_value(remote_value)
                browse_obj = self.env[self.model_id.model].browse(local_id)
                browse_obj.sudo().with_context(skip_account_move_synchronization =True,check_move_validity=False,synchro=True).write(local_value)
            elif self.auto_create:
                # Create
                remote_value = self.exception_value_create(remote_value)
                local_value = self.get_local_value(remote_value)
                new_obj = self.env[self.model_id.model].sudo().with_context(skip_account_move_synchronization =True,check_move_validity=False,synchro=True).create(local_value)
                local_id = new_obj.id
                condition = [('remote_id', '=', remote_id), ('obj_id', '=', self.id)]
                local_ids = self.env['synchro.obj.line'].search(condition)
                if local_ids:
                    local_ids.with_context(skip_account_move_synchronization =True,check_move_validity=False,synchro=True).write({'local_id': local_id})
                else:
                    local_ids.with_context(skip_account_move_synchronization =True,check_move_validity=False,synchro=True).create({
                                    'local_id': local_id,
                                    'remote_id': remote_id,
                                    'obj_id': self.id,
                                    'description': '%s' % (remote_value.get('name', '???'))
                                    })

    @api.model
    def get_synchronazed_remote_ids(self):
        "return all remote id"
        self.ensure_one()
        line_ids = self.env['synchro.obj.line'].search([('obj_id', '=', self.id)])
        return line_ids.mapped('remote_id')


class BaseSynchroObjAvoid(models.Model):
    """Class to avoid the base synchro object."""
    _name = "synchro.obj.avoid"
    _description = "Fields to not synchronize"

    name = fields.Char(
        string='Remote Name',
        required=True
    )
    remote_type = fields.Char(
        string='Remote Type'
    )
    obj_id = fields.Many2one(
        'synchro.obj',
        string='Object',
        required=True,
        ondelete='SET NULL',
    )
    field_id = fields.Many2one(
        'ir.model.fields',
        ondelete='SET DEFAULT',
        string='local field',
       
    )
    synchronize = fields.Boolean('synchronyse')
    check_remote = fields.Boolean('Remote checking')

    def button_synchronize(self):
        "to synchronize"
        for obj_avoid in self:
            obj_avoid.synchronize = True

    def button_unsynchronize(self):
        "to synchronize"
        for obj_avoid in self:
            obj_avoid.synchronize = False


class BaseSynchroObjField(models.Model):
    """Class Fields to synchronize."""
    _name = "synchro.obj.field"
    _description = "Fields to synchronize"

    name = fields.Char(
        string='Remote field name',
        required=True
    )
    field_id = fields.Many2one(
        'ir.model.fields',
        string='local field',
        ondelete='SET DEFAULT',
        required=True,
    )
    obj_id = fields.Many2one(
        'synchro.obj',
        string='Object',
        required=True,
        ondelete='SET DEFAULT',
    )

    @api.onchange('field_id')
    def onchange_field(self):
        "return the name"
        self.name = self.field_id.name or ''


class BaseSynchroObjLine(models.Model):
    """Class to store object line in base synchro."""
    _name = "synchro.obj.line"
    _description = "Synchronized record"

    @api.model
    def _selection_target_model(self):
        models = self.env['ir.model'].search([])
        return [(model.model, model.name) for model in models]

    name = fields.Datetime(
        string='Date',
        required=True,
        default=lambda *args: time.strftime('%Y-%m-%d %H:%M:%S')
    )
    obj_id = fields.Many2one(
        'synchro.obj',
        string='Object',
        required=True,
        ondelete='SET DEFAULT',
        index=True
    )
    description = fields.Char('description')
    local_id = fields.Integer(string='Local ID', index=True)
    remote_id = fields.Integer(string='Remote ID', index=True)
    server_id = fields.Many2one(related='obj_id.server_id', store=True)
    model_id = fields.Integer(related='obj_id.model_id.id', store=True, index=True)

    todo = fields.Boolean('Todo')

    resource_ref = fields.Reference(string='Record', selection='_selection_target_model', compute='_compute_resource_ref')

    @api.depends('obj_id', 'local_id')
    def _compute_resource_ref(self):
        for line in self:
            model_name = line.obj_id.model_id.model or False
            if model_name:
                line.resource_ref = '%s,%s' % (model_name, line.local_id or 0)
            else:
                line.resource_ref = False

    @api.onchange('local_id', 'remote_id')
    def onchange_local_id(self):
        if self.local_id and self.remote_id:
            self.todo = False
        else:
            self.todo = True
