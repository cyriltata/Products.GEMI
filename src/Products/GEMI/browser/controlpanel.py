from plone.app.registry.browser import controlpanel
from Products.GEMI import _
from Products.GEMI.interfaces import IProductsGEMISettings

class ProductsGEMISettingsEditForm(controlpanel.RegistryEditForm):

    schema = IProductsGEMISettings
    label = _(u"Products.GEMI settings")
    description = _(u"Some global settings of the Products.GEMI extension")

    def updateFields(self):
        super(ProductsGEMISettingsEditForm, self).updateFields()

    def updateWidgets(self):
        super(ProductsGEMISettingsEditForm, self).updateWidgets()


class ProductsGEMISettingsControlPanel(controlpanel.ControlPanelFormWrapper):
    form = ProductsGEMISettingsEditForm