from odoo import api, fields, models, tools, _
from odoo.osv import expression
from odoo.exceptions import AccessError
from odoo.addons.shopify_ept import shopify



class Shopifysale_order_line(models.Model):
     _inherit = "sale.order.line"
     def get_sale_order_line_multiline_description_sale(self, product):
        """ Compute a default multiline description for this sales order line.

        In most cases the product description is enough but sometimes we need to append information that only
        exists on the sale order line itself.
        e.g:
        - custom attributes and attributes that don't create variants, both introduced by the "product configurator"
        - in event_sale we need to know specifically the sales order line as well as the product to generate the name:
          the product is not sufficient because we also need to know the event_id and the event_ticket_id (both which belong to the sale order line).
        """
        
        
        if not self.product_id:
            return ''
        if self.order_id.partner_id.country_id.code == "FR":
               return product.get_product_multiline_description_sale() + self._get_sale_order_line_multiline_description_variants()

        color = ""
        taille = ""
        if self.product_id.product_template_variant_value_ids:
          for m in self.product_id.product_template_variant_value_ids:
            phrase = m.attribute_id.name
            if m.attribute_id.id in [2,3,4]:
                color = ", Color: "+ m.name
            else:
                taille = m.name

        values = []
        if self.product_id.type_product:
            type_perso = str(self.product_id.type_product)
        else:
            type_perso = " "
        if self.product_id.product_template_variant_value_ids:
           lieu = self.product_id.name +" \n \n Taille :"+taille+" QTY: "+str(self.product_uom_qty)+" \n \n Type : "+type_perso + color +", made in France by Kiwami 9 rue ampere 64121 Montardon"
        else: 
          lieu = " \n \n QTY: "+str(self.product_uom_qty)+" \n \n Type : "+type_perso +", made in France by Kiwami 9 rue ampere 64121 Montardon"
          if product.partner_ref:
             values.append(product.partner_ref)
        values.append(lieu)    
        if product.description_sale: 
                values.append(product.description_sale)
        return '\n'.join(values)

     @api.onchange('product_uom_qty')
     def _onchange_quantity_desc_for_export(self):
       if not self.product_id:
             self.name = ''
       if self.order_id.partner_id.country_id.code == "FR":
               self.name =  str(self.product_id.get_product_multiline_description_sale()) + str(self._get_sale_order_line_multiline_description_variants())
       else:

        color = ""
        taille = ""
        if self.product_id.product_template_variant_value_ids:
          for m in self.product_id.product_template_variant_value_ids:
            phrase = m.attribute_id.name
            if m.attribute_id.id in [2,3,4]:
                color = ", Color: "+ m.name
            else:
                taille = m.name

        values = []
        if self.product_id.type_product:
            type_perso = str(self.product_id.type_product)
        else:
            type_perso = " "
        if self.product_id.product_template_variant_value_ids:
           lieu = self.product_id.name +" \n \n Taille :"+taille+" QTY: "+str(self.product_uom_qty)+" \n \n Type : "+type_perso + color +", made in France by Kiwami 9 rue ampere 64121 Montardon"
        else: 
          lieu = " \n \n QTY: "+str(self.product_uom_qty)+" \n \n Type : "+type_perso+", made in France by Kiwami 9 rue ampere 64121 Montardon"
          if self.product_id.partner_ref:
             values.append(self.product_id.partner_ref)
        values.append(lieu)    
        if self.product_id.description_sale: 
                values.append(self.product_id.description_sale)
        self.name =  '\n'.join(values)



class ShopifyProductProducttemplate(models.Model):
     _inherit = "product.template"
     type_product = fields.Char()

class Salelineremovereferencefrom_invoice(models.Model):
    _inherit = "product.product"

    def name_get(self):
        # TDE: this could be cleaned a bit I think

        def _name_get(d):
            name = d.get('name', '')
            code =  False
            if code:
                name = '[%s] %s' % (code,name)
            return (d['id'], name)

        partner_id = self._context.get('partner_id')
        if partner_id:
            partner_ids = [partner_id, self.env['res.partner'].browse(partner_id).commercial_partner_id.id]
        else:
            partner_ids = []
        company_id = self.env.context.get('company_id')

        # all user don't have access to seller and partner
        # check access and use superuser
        self.check_access_rights("read")
        self.check_access_rule("read")

        result = []

        # Prefetch the fields used by the `name_get`, so `browse` doesn't fetch other fields
        # Use `load=False` to not call `name_get` for the `product_tmpl_id`
        self.sudo().read(['name', 'default_code', 'product_tmpl_id'], load=False)

        product_template_ids = self.sudo().mapped('product_tmpl_id').ids

        if partner_ids:
            supplier_info = self.env['product.supplierinfo'].sudo().search([
                ('product_tmpl_id', 'in', product_template_ids),
                ('name', 'in', partner_ids),
            ])
            # Prefetch the fields used by the `name_get`, so `browse` doesn't fetch other fields
            # Use `load=False` to not call `name_get` for the `product_tmpl_id` and `product_id`
            supplier_info.sudo().read(['product_tmpl_id', 'product_id', 'product_name', 'product_code'], load=False)
            supplier_info_by_template = {}
            for r in supplier_info:
                supplier_info_by_template.setdefault(r.product_tmpl_id, []).append(r)
        for product in self.sudo():
            variant = product.product_template_attribute_value_ids._get_combination_name()

            name = variant and "%s (%s)" % (product.name, variant) or product.name
            sellers = self.env['product.supplierinfo'].sudo().browse(self.env.context.get('seller_id')) or []
            if not sellers and partner_ids:
                product_supplier_info = supplier_info_by_template.get(product.product_tmpl_id, [])
                sellers = [x for x in product_supplier_info if x.product_id and x.product_id == product]
                if not sellers:
                    sellers = [x for x in product_supplier_info if not x.product_id]
                # Filter out sellers based on the company. This is done afterwards for a better
                # code readability. At this point, only a few sellers should remain, so it should
                # not be a performance issue.
                if company_id:
                    sellers = [x for x in sellers if x.company_id.id in [company_id, False]]
            if sellers:
                for s in sellers:
                    seller_variant = s.product_name and (
                        variant and "%s (%s)" % (s.product_name, variant) or s.product_name
                        ) or False
                    mydict = {
                              'id': product.id,
                              'name': seller_variant or name,
                              'default_code': s.product_code ,
                              }
                    temp = _name_get(mydict)
                    if temp not in result:
                        result.append(temp)
            else:
                mydict = {
                          'id': product.id,
                          'name': name,
                          'default_code': product.default_code,
                          }
                result.append(_name_get(mydict))
        return result
    def get_product_multiline_description_sale(self):
        """ Compute a multiline description of this product, in the context of sales
                (do not use for purchases or other display reasons that don't intend to use "description_sale").
            It will often be used as the default description of a sale order line referencing this product.
        """  
        name = self.display_name
        if self.description_sale:
            name += '\n' + self.description_sale
        return name
#         name = ""
#         if self.description_sale:
#             name += self.description_sale
#         if not self.description_sale:
#             name += str(self.name)

#         return name
               

class Shopifysaleorderline(models.Model):
     _inherit = "account.move.line"               
     
     
     
     
     def _get_computed_name(self):
        self.ensure_one()

        if not self.product_id:
            return ''


        if self.partner_id.lang:
            product = self.product_id.with_context(lang=self.partner_id.lang)
        else:
            product = self.product_id
               
        
     
     
        if self.partner_id.country_id.code == "FR":
          
          values2 = []
          if product.partner_ref:
            values2.append(product.partner_ref)
          if self.journal_id.type == 'sale':
            if product.description_sale:
                values2.append(product.description_sale)
          elif self.journal_id.type == 'purchase':
            if product.description_purchase:
                values2.append(product.description_purchase)
          return '\n'.join(values2)
          
          
          
          
          
        color = ""
        taille = ""
        if self.product_id.product_template_variant_value_ids:
          for m in self.product_id.product_template_variant_value_ids:
            phrase = m.attribute_id.name
            if m.attribute_id.id in [2,3,4]:
                color = ", Color: "+ m.name
            else:
                taille = m.name

        values = []
        if self.product_id.type_product:
            type_perso = str(self.product_id.type_product)
        else:
            type_perso = " "
        if self.product_id.product_template_variant_value_ids:
           lieu = self.product_id.name +" \n \n Taille :"+taille+" QTY: "+str(self.quantity)+" \n \n Type : "+type_perso + color +", made in France by Kiwami 9 rue ampere 64121 Montardon"
        else: 
          lieu = " \n \n  QTY: "+str(self.quantity)+" \n \n Type : "+type_perso + ", made in France by Kiwami 9 rue ampere 64121 Montardon"
          if product.partner_ref:
             values.append(product.partner_ref)
        values.append(lieu)    
        if self.journal_id.type == 'sale':
            if product.description_sale:
                
                values.append(product.description_sale)
                
        elif self.journal_id.type == 'purchase':
            if product.description_purchase:
                values.append(product.description_purchase)
        return '\n'.join(values)

     @api.onchange('partner_id')
     def _onchange_partner_fr(self):
        self.ensure_one()

        if not self.product_id:
            return ''

        if self.partner_id.lang:
            product = self.product_id.with_context(lang=self.partner_id.lang)
        else:
            product = self.product_id
               
        if self.partner_id.country_id.code == "FR":
          
          values2 = []
          if product.partner_ref:
            values2.append(product.partner_ref)
          if self.journal_id.type == 'sale':
            if product.description_sale:
                values2.append(product.description_sale)
          elif self.journal_id.type == 'purchase':
            if product.description_purchase:
                values2.append(product.description_purchase)
          return '\n'.join(values2)
        color = ""
        taille = ""
        if self.product_id.product_template_variant_value_ids:
         for m in self.product_id.product_template_variant_value_ids:
            phrase = m.attribute_id.name
            if m.attribute_id.id in [2,3,4]:
                color = m.name
            else:
                taille = m.name

        values = []
        if self.product_id.product_template_variant_value_ids:
           lieu = self.product_id.name +" \n \n Taille :"+taille+" QTY: "+str(self.quantity)+" \n \n  Type : "+str(self.product_id.type_product)+", Color : "+ color +", made in France by Kiwami 9 rue ampere 64121 Montardon"
        else: 
          lieu = " \n \n QTY: "+str(self.quantity)+" \n \n  Type : "+str(self.product_id.type_product) +", made in France by Kiwami 9 rue ampere 64121 Montardon"
          if product.partner_ref:
             values.append(product.partner_ref)
        values.append(lieu)    
        if self.journal_id.type == 'sale':
            if product.description_sale:
                
                values.append(product.description_sale)
                
        elif self.journal_id.type == 'purchase':
            if product.description_purchase:
                values.append(product.description_purchase)
        self.name =  '\n'.join(values)
     @api.onchange('quantity')
     def _onchange_quantity_desc(self):
       self.ensure_one()

       if not self.product_id:
            self.name =  ""

       if self.partner_id.lang:
            product = self.product_id.with_context(lang=self.partner_id.lang)
       else:
            product = self.product_id
               
       if self.partner_id.country_id.code == "FR":
          
          values2 = []
          if product.partner_ref:
            values2.append(product.partner_ref)
          if self.journal_id.type == 'sale':
            if product.description_sale:
                values2.append(product.description_sale)
          elif self.journal_id.type == 'purchase':
            if product.description_purchase:
                values2.append(product.description_purchase)
          
          self.name =  '\n'.join(values2)
       else: 
        color = ""
        taille = ""
        if self.product_id.product_template_variant_value_ids:
         for m in self.product_id.product_template_variant_value_ids:
            phrase = m.attribute_id.name
            if m.attribute_id.id in [2,3,4]:
                color = m.name
            else:
                taille = m.name

        values = []
        if self.product_id.product_template_variant_value_ids:
           lieu = self.product_id.name +" \n \n Taille :"+taille+" QTY: "+str(self.quantity)+" \n \n Type : "+str(self.product_id.type_product)+", Color : "+ color +", made in France by Kiwami 9 rue ampere 64121 Montardon"
        else: 
          lieu = " \n \n  QTY: "+str(self.quantity)+" \n \n Type : "+str(self.product_id.type_product)+", made in France by Kiwami 9 rue ampere 64121 Montardon"
          if product.partner_ref:
             values.append(product.partner_ref)
        values.append(lieu)    
        if self.journal_id.type == 'sale':
            if product.description_sale:
                
                values.append(product.description_sale)
                
        elif self.journal_id.type == 'purchase':
            if product.description_purchase:
                values.append(product.description_purchase)
        self.name =  '\n'.join(values)
               
               
               
               
               

class ShopifyProductProductEptt(models.Model):
     _inherit = "shopify.product.product.ept"
    
     hs_code = fields.Char()
     type_product = fields.Char()
