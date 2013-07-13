import os
from django.db import models
from core.models import PlCoreBase, Site, Slice
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

# Create your models here.

class Network(PlCoreBase):
    name = models.CharField(max_length=32)
    subnet = models.CharField(max_length=32)
    ports = models.CharField(max_length=1024)
    labels = models.CharField(max_length=1024)
    slice = models.ForeignKey(Slice, related_name="networks")
    guaranteedBandwidth = models.IntegerField()
    permittedSlices = models.ManyToManyField(Slice, blank=True, related_name="permittedNetworks")
    boundSlices = models.ManyToManyField(Slice, blank=True, related_name="boundNetworks")

    def __unicode__(self):  return u'%s' % (self.name)

class Router(PlCoreBase):
    name = models.CharField(max_length=32)
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
        return self.tagType.name


