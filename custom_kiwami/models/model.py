from odoo import api, fields, models, tools, _
from odoo.osv import expression
from odoo.exceptions import AccessError







class ShopifyProductProductEptt(models.Model):
     _inherit = "shopify.product.product.ept"
    
     hs_code = fields.Char()
     def search_odoo_product_and_set_sku_barcode(self, template_attribute_value_ids, variation, product_template):
        """ This method is used to search odoo product base on a prepared domain and set SKU and barcode on that
            product.
            :param template_attribute_value_ids: Record of product template attribute value ids.
            :param variation: Response of product variant which received from shopify store.
            :param product_template: Record of Odoo product template.
            @return: odoo_product
            @author: Haresh Mori @Emipro Technologies Pvt. Ltd on date 21 October 2020 .
            Task_id: 167537
        """
        odoo_product_obj = self.env["product.product"]
        sku = variation.get("sku")
        sh_code = variation.get("harmonizedSystemCode")
        barcode = variation.get("barcode") or False
        if barcode and barcode.__eq__("false"):
            barcode = False
        odoo_product = False

        domain = []
        for template_attribute_value in template_attribute_value_ids:
            tpl = ("product_template_attribute_value_ids", "=", template_attribute_value)
            domain.append(tpl)

        domain and domain.append(("product_tmpl_id", "=", product_template.id))
        if domain:
            odoo_product = odoo_product_obj.search(domain)
        if odoo_product and sku:
            odoo_product.write({"default_code": sku})
        if odoo_product and sh_code:
            odoo_product.write({"hs_code": "hghghg"})
        if barcode and odoo_product:
            odoo_product.write({"barcode": barcode})

        return odoo_product

class ShopifyProductTemplateEptt(models.Model):
    _inherit = "shopify.product.template.ept"
    def prepare_vals_for_product_basic_details(self, variant_vals, variant):
        """ This method is used to prepare a vals for the product basic details.
            @author: Haresh Mori @Emipro Technologies Pvt. Ltd on date 21 October 2020 .
            Task_id: 167537
        """
        variant_vals.update({"barcode": variant.product_id.barcode or "",
                             "grams": int(variant.product_id.weight * 1000),
                             "weight": variant.product_id.weight,
                             "hs_code": variant.inventory_item_id.harmonizedSystemCode,
                             "weight_unit": "kg",
                             "requires_shipping": "true", "sku": variant.default_code,
                             "taxable": variant.taxable and "true" or "false",
                             "title": variant.name,
                             })
        option_index = 0
        option_index_value = ["option1", "option2", "option3"]
        attribute_value_obj = self.env["product.template.attribute.value"]
        att_values = attribute_value_obj.search(
            [("id", "in", variant.product_id.product_template_attribute_value_ids.ids)],
            order="attribute_id")
        for att_value in att_values:
            if option_index > 3:
                continue
            variant_vals.update({option_index_value[option_index]: att_value.name})
            option_index = option_index + 1

        return variant_vals

    def prepare_variant_vals(self, instance, variant_data):
        """
        This method used to prepare a shopify variant dictionary.
        @param instance:
        @param variant_data: Data of Shopify variant.
        @author: Maulik Barad on Date 01-Sep-2020.
        """
        
#         mm = variant_data.get("inventoryItem",variant_data.get("inventory_item_id"))
#         test = variant_data.get("inventoryItem").get("harmonizedSystemCode")
        variant_vals = {"shopify_instance_id": instance.id,
                        "variant_id": variant_data.get("id"),
                        "sequence": variant_data.get("position"),
                        "default_code": variant_data.get("sku", ""),
#                         "hs_code": test,
                        "inventory_item_id": variant_data.get("inventory_item_id"),
                        "inventory_management": "shopify" if variant_data.get(
                            "inventory_management") == "shopify" else "Dont track Inventory",
                        "check_product_stock": variant_data.get("inventory_policy"),
                        "taxable": variant_data.get("taxable"),
                        "created_at": self.convert_shopify_date_into_odoo_format(variant_data.get("created_at")),
                        "updated_at": self.convert_shopify_date_into_odoo_format(variant_data.get("updated_at")),
                        "exported_in_shopify": True,
                        "active": True}

        return variant_vals
