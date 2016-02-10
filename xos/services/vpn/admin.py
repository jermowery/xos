import time

from core.admin import ReadOnlyAwareAdmin, SliceInline
from core.middleware import get_request
from core.models import User
from django import forms
from django.contrib import admin
from services.vpn.models import VPN_KIND, VPNService, VPNTenant


class VPNServiceAdmin(ReadOnlyAwareAdmin):
    """Defines the admin for the VPNService."""
    model = VPNService
    verbose_name = "VPN Service"

    list_display = ("backend_status_icon", "name", "enabled")

    list_display_links = ('backend_status_icon', 'name', )

    fieldsets = [(None, {'fields': ['backend_status_text', 'name', 'enabled',
                                    'versionNumber', 'description', "view_url"],
                         'classes':['suit-tab suit-tab-general']})]

    readonly_fields = ('backend_status_text', )

    inlines = [SliceInline]

    extracontext_registered_admins = True

    user_readonly_fields = ["name", "enabled", "versionNumber", "description"]

    suit_form_tabs = (('general', 'VPN Service Details'),
                      ('administration', 'Tenants'),
                      ('slices', 'Slices'),)

    suit_form_includes = (('vpnserviceadmin.html',
                           'top',
                           'administration'),)

    def queryset(self, request):
        return VPNService.get_service_objects_by_user(request.user)


class VPNTenantForm(forms.ModelForm):
    """The form used to create and edit a VPNTenant.

    Attributes:
        creator (forms.ModelChoiceField): The XOS user that created this tenant.
        client_conf (forms.CharField): The readonly configuration used on the client to connect to this Tenant.
        server_address (forms.GenericIPAddressField): The ip address on the VPN of this Tenant.
        client_address (forms.GenericIPAddressField): The ip address on the VPN of the client.
        is_persistent (forms.BooleanField): Determines if this Tenant keeps this connection alive through failures.
        can_view_subnet (forms.BooleanField): Determins if this Tenant makes it's subnet available to the client.

    """
    creator = forms.ModelChoiceField(queryset=User.objects.all())
    server_network = forms.GenericIPAddressField(
        protocol="IPv4", required=True)
    vpn_subnet = forms.GenericIPAddressField(protocol="IPv4", required=True)
    is_persistent = forms.BooleanField(required=False)
    clients_can_see_each_other = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        super(VPNTenantForm, self).__init__(*args, **kwargs)
        self.fields['kind'].widget.attrs['readonly'] = True
        # self.fields['script_name'].widget.attrs['readonly'] = True
        self.fields[
            'provider_service'].queryset = VPNService.get_service_objects().all()

        self.fields['kind'].initial = VPN_KIND

        if self.instance:
            self.fields['creator'].initial = self.instance.creator
            self.fields['vpn_subnet'].initial = self.instance.vpn_subnet
            self.fields[
                'server_network'].initial = self.instance.server_network
            self.fields[
                'clients_can_see_each_other'].initial = self.instance.clients_can_see_each_other
            self.fields['is_persistent'].initial = self.instance.is_persistent

        if (not self.instance) or (not self.instance.pk):
            self.fields['creator'].initial = get_request().user
            self.fields['vpn_subnet'].initial = "255.255.255.0"
            self.fields['server_network'].initial = "10.66.77.0"
            self.fields['clients_can_see_each_other'].initial = True
            self.fields['is_persistent'].initial = True
            if VPNService.get_service_objects().exists():
                self.fields["provider_service"].initial = VPNService.get_service_objects().all()[
                    0]

    def save(self, commit=True):
        self.instance.creator = self.cleaned_data.get("creator")
        self.instance.is_persistent = self.cleaned_data.get('is_persistent')
        self.instance.vpn_subnet = self.cleaned_data.get("vpn_subnet")
        self.instance.server_network = self.cleaned_data.get('server_network')
        self.instance.clients_can_see_each_other = self.cleaned_data.get(
            'clients_can_see_each_other')

        if (not self.instance.script):
            self.instance.script = str(time.time()) + ".vpn"

        if (not self.instance.ca_cert):
            self.generate_ca_crt()

        if ((not self.instance.server_cert) or (not self.instance.server_key)):
            self.generate_server_credentials()

        return super(VPNTenantForm, self).save(commit=commit)

    def generate_ca_crt(self):
        """str: Generates the ca cert by reading from the ca file"""
        with open("/opt/openvpn/easyrsa3/pki/ca.crt") as crt:
            return crt.readlines()

    def generate_server_credentials(self):
        with open("/opt/openvpn/easyrsa3/pki/issued/server.crt") as crt:
            self.instance.server_crt = crt.readlines()

        with open("/opt/openvpn/easyrsa3/pki/private/server.key") as key:
            self.instance.server_key = key.readlines()

        with open("/opt/openvpn/easyrsa3/pki/dh.pem") as dh:
            self.instance.dh = dh.readlines()

    class Meta:
        model = VPNTenant


class VPNTenantAdmin(ReadOnlyAwareAdmin):
    verbose_name = "VPN Tenant Admin"
    list_display = ('id', 'backend_status_icon', 'instance',
                    'server_network', 'vpn_subnet')
    list_display_links = ('id', 'backend_status_icon',
                          'instance', 'server_network', 'vpn_subnet')
    fieldsets = [(None, {'fields': ['backend_status_text', 'kind',
                                    'provider_service', 'instance', 'creator',
                                    'server_network', 'vpn_subnet', 'is_persistent',
                                    'clients_can_see_each_other', 'script_link'],
                         'classes': ['suit-tab suit-tab-general']})]
    readonly_fields = ('backend_status_text', 'instance', 'script_link')
    form = VPNTenantForm

    suit_form_tabs = (('general', 'Details'),)

    def queryset(self, request):
        return VPNTenant.get_tenant_objects_by_user(request.user)

# Associate the admin forms with the models.
admin.site.register(VPNService, VPNServiceAdmin)
admin.site.register(VPNTenant, VPNTenantAdmin)