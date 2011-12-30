from django.db.models import FileField
from django.forms import forms
from django.template.defaultfilters import filesizeformat
from django.utils.translation import ugettext_lazy as _

class RestrictedFileField(FileField):
    """
    @summary: based on file field, added extra validation
    content_types: a list containing allowed content_types like ['application/pdf', 'image/jpeg']
    max_upload_size: a number indicating the maximum file size allowed for upload in bytes
    min_upload_size: a number indicating the minimal file size allowed for upload in bytes
    """
    description = "same as FileField but you can validate by content type, size."

    def __init__(self, *args, **kwargs):
        self.content_types = kwargs.pop('content_types', None)
        self.max_upload_size = kwargs.pop('max_upload_size', None)
        self.min_upload_size = kwargs.pop('min_upload_size', None)

        if self.content_types:
            if not isinstance(self.content_types, (list, tuple)):
                raise TypeError('content_types is not iterable')
            for content_type in self.content_types:
                if not isinstance(content_type, basestring):
                    raise TypeError('content_type element is not a string')

        if self.max_upload_size is not None:
            if not isinstance(self.max_upload_size, (float, int)):
                raise TypeError('max_upload_size is not a number')
            if self.max_upload_size < 0:
                raise ValueError('value not allowed in max_upload_size')

        if self.min_upload_size is not None:
            if not isinstance(self.min_upload_size, (float, int)):
                raise TypeError('min_upload_size is not a number')
            if self.min_upload_size < 0:
                raise ValueError('value not allowed in min_upload_size')

        if self.max_upload_size is not None and self.min_upload_size is not None:
            if self.max_upload_size < self.min_upload_size:
                self._upload_size = self.max_upload_size
                self.max_upload_size = self.min_upload_size
                self.min_upload_size = self._upload_size

        super(RestrictedFileField, self).__init__(*args, **kwargs)

    def clean(self, *args, **kwargs):
        data = super(RestrictedFileField, self).clean(*args, **kwargs)

        file = data.file
        if not hasattr(file, 'content_type'):
            return data
        content_type = file.content_type

        if self.content_types and content_type not in self.content_types:
            raise forms.ValidationError(
                _('File type not supported, please only %r') %
                (self.content_types,)
            )

        elif self.max_upload_size is not None and file._size > self.max_upload_size:
            raise forms.ValidationError(
                _('Please keep file size under %(max_upload_size)s. Current file size is %(size)s') %
                {'max_upload_size': filesizeformat(self.max_upload_size), 'size': filesizeformat(file._size)}
            )

        elif self.min_upload_size is not None and file._size < self.min_upload_size:
            raise forms.ValidationError(
                _('Please keep file size above %(min_upload_size)s. Current file size is %(size)s') %
                {'min_upload_size': filesizeformat(self.min_upload_size), 'size': filesizeformat(file._size)}
            )

        return data

# South migration support
try:
    from south.modelsinspector import add_introspection_rules
except:
    pass
else:
    rules = [
        (
            (RestrictedFileField,), [],
            {
                "content_types": ["content_types", {"default": None}],
                "max_upload_size": ["max_upload_size", {"default": None}],
                "min_upload_size": ["min_upload_size", {"default": None}],
            }
        ),
    ]
    # Modify this string, there should be the path to this class 
    add_introspection_rules(rules, ["^app\.lib\.fields\.model\.RestrictedFileField"])
