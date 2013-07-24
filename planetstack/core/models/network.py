import os
from django.db import models
from core.models import PlCoreBase, Site, Slice, Sliver
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

# Create your models here.

class NetworkTemplate(PlCoreBase):
    VISIBILITY_CHOICES = (('public', 'public'), ('private', 'private'))

    name = models.CharField(max_length=32)
    guaranteedBandwidth = models.IntegerField(default=0)
    visibility = models.CharField(max_length=30, choices=VISIBILITY_CHOICES, default="private")

    def __unicode__(self):  return u'%s' % (self.name)

class Network(PlCoreBase):
    name = models.CharField(max_length=32)
    template = models.ForeignKey(NetworkTemplate)
    subnet = models.CharField(max_length=32)
    ports = models.CharField(max_length=1024)
    labels = models.CharField(max_length=1024)
    slice = models.ForeignKey(Slice, related_name="networks")

    guaranteedBandwidth = models.IntegerField(default=0)
    permittedSlices = models.ManyToManyField(Slice, blank=True, related_name="permittedNetworks")
    boundSlivers = models.ManyToManyField(Sliver, blank=True, related_name="boundNetworks", through="NetworkBoundSliver")

    def __unicode__(self):  return u'%s' % (self.name)

class NetworkBoundSliver(PlCoreBase):
    network = models.ForeignKey(Network)
    sliver = models.ForeignKey(Sliver)
    ip = models.GenericIPAddressField(help_text="Sliver ip address", blank=True, null=True)

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


