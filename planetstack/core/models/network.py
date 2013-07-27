import os
import socket
from django.db import models
from core.models import PlCoreBase, Site, Slice, Sliver
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

# Create your models here.

SUBNET_BASE = "10.0.0.0"
SUBNET_NODE_BITS = 12     # enough for 4096 bits per subnet
SUBNET_SUBNET_BITS = 12   # enough for 4096 private networks

def ip_to_int(ip):
    return int(socket.inet_aton(ip).encode('hex'),16)

def int_to_ip(i):
    return socket.inet_ntoa(hex(i)[2:].zfill(8).decode('hex'))

def find_unused_subnet(base, subnet_bits, node_bits, existing_subnets):
    # enumerate possible subnets until we find one that isn't used
    i=1
    while True:
        subnet_i = ip_to_int(base) | (i<<node_bits)
        subnet = int_to_ip(subnet_i) + "/" + str(32-node_bits)
        if (subnet not in existing_subnets):
            return subnet
        i=i+1
        # TODO: we could run out...

def find_unused_address(subnet, existingAddresses):
    # enumerate possible addresses until we find one that isn't used
    (network, bits) = subnet.split("/")
    network_i = ip_to_int(network)
    max_addr = 1<<(32-int(bits))
    i = 1
    while True:
        if i>=max_addr:
            raise ValueError("No more ips available")
        ip = int_to_ip(network_i | i)
        if not (ip in existingAddresses):
            return ip
        i=i+1

class NetworkTemplate(PlCoreBase):
    VISIBILITY_CHOICES = (('public', 'public'), ('private', 'private'))

    name = models.CharField(max_length=32)
    guaranteedBandwidth = models.IntegerField(default=0)
    visibility = models.CharField(max_length=30, choices=VISIBILITY_CHOICES, default="private")

    def __unicode__(self):  return u'%s' % (self.name)

class Network(PlCoreBase):
    name = models.CharField(max_length=32)
    template = models.ForeignKey(NetworkTemplate)
    subnet = models.CharField(max_length=32, blank=True)
    ports = models.CharField(max_length=1024, blank=True, null=True)
    labels = models.CharField(max_length=1024, blank=True, null=True)
    slice = models.ForeignKey(Slice, related_name="networks")

    guaranteedBandwidth = models.IntegerField(default=0)
    permittedSlices = models.ManyToManyField(Slice, blank=True, related_name="permittedNetworks")
    slivers = models.ManyToManyField(Sliver, blank=True, related_name="boundNetworks", through="NetworkSliver")

    def __unicode__(self):  return u'%s' % (self.name)

    def allocateSubnet(self):
        existingSubnets = [x.subnet for x in Network.objects.all()]
        return find_unused_subnet(SUBNET_BASE, SUBNET_SUBNET_BITS, SUBNET_NODE_BITS, existingSubnets)

    def allocateAddress(self):
        existingAddresses = [x.ip for x in self.networksliver_set.all()]
        return find_unused_address(self.subnet, existingAddresses)

    def save(self, *args, **kwds):
        if not self.subnet:
            self.subnet = self.allocateSubnet()
        super(Network, self).save(*args, **kwds)

class NetworkSliver(PlCoreBase):
    network = models.ForeignKey(Network)
    sliver = models.ForeignKey(Sliver)
    ip = models.GenericIPAddressField(help_text="Sliver ip address", blank=True)

    def save(self, *args, **kwds):
        if not self.ip:
            self.ip = self.network.allocateAddress()
        super(NetworkSliver, self).save(*args, **kwds)

    def __unicode__(self):  return u'foo!'

class Router(PlCoreBase):
    name = models.CharField(max_length=32)
    owner = models.ForeignKey(Slice, related_name="routers")
    networks = models.ManyToManyField(Network, blank=True, related_name="routers")

    def __unicode__(self):  return u'%s' % (self.name)

class NetworkParameterType(PlCoreBase):
    name = models.SlugField(help_text="The name of this tag", max_length=128)

    def __unicode__(self):  return u'%s' % (self.name)

class NetworkParameter(PlCoreBase):
    networkParameterType = models.ForeignKey(NetworkParameterType, related_name="parameters", help_text="The name of the parameter")
    value = models.CharField(help_text="The value of this parameter", max_length=1024)

    # The required fields to do a ObjectType lookup, and object_id assignment
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    def __unicode__(self):
        return self.networkParameterType.name


