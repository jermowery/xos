import os
from django.db import models
from core.models import PlCoreBase
from core.models import Project
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic

# Create your models here.

class TagType(PlCoreBase):
    name = models.SlugField(help_text="The name of this tag", max_length=128)
    project = models.ForeignKey(Project, related_name='tags', help_text="The Project this Tag is associated with")

    def __unicode__(self):  return u'%s' % (self.name)

class Tag(PlCoreBase):
    tagType = models.ForeignKey(TagType, related_name="tags", help_text="The name of the tag")
    value = models.CharField(help_text="The value of this tag", max_length=1024)

    # The required fields to do a ObjectType lookup, and object_id assignment
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    def __unicode__(self):
        return self.tagType.name

