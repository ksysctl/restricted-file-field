from django.db.models import FileField
from django.forms import forms
from django.template.defaultfilters import filesizeformat
from django.core.files.images import get_image_dimensions
from django.utils.translation import ugettext_lazy as _

class RestrictedFileField(FileField):
    """
    @summary: based on file field, added extra validation
    content_types: a list containing allowed content_types like ['application/pdf', 'image/jpeg']
    max_upload_size: a number indicating the maximum file size allowed for upload in bytes
    min_upload_size: a number indicating the minimal file size allowed for upload in bytes
    range_width: an list indicating the min./max. width allowed in image
    range_height: an list indicating the min./max. height allowed in image
    """
    VALID_IMAGE_PROC = (
        'image/gif',
        'image/jpeg',
        'image/png',
        'image/tiff',
    )
    VALID_IMAGE_TYPE = (
        VALID_IMAGE_PROC + (
        'image/pjpeg',
        'image/svg+xml',
        'image/vnd.microsoft.icon',
    ))

    def __init__(self, *args, **kwargs):
        self.content_types = kwargs.pop('content_types', None)
        self.max_upload_size = kwargs.pop('max_upload_size', None)
        self.min_upload_size = kwargs.pop('min_upload_size', None)
        self.range_width = kwargs.pop('range_width', None)
        self.range_height = kwargs.pop('range_height', None)

        if self.range_width is not None:
            if not isinstance(self.range_width, (list, tuple)):
                raise TypeError('range_width is not iterable')
            if len(self.range_width) != 2:
                raise ValueError('need 2 values to unpack from range_width')
            for width in self.range_width:
                if not isinstance(width, (float, int)):
                    raise TypeError('width is not a number')
                if width < 0:
                    raise ValueError('value not allowed in width')
            if self.range_width[0] > self.range_width[1]:
                self.range_width[0], self.range_width[1] = (
                    self.range_width[1],
                    self.range_width[0]
                )

        if self.range_height is not None:
            if not isinstance(self.range_height, (list, tuple)):
                raise TypeError('range_height is not iterable')
            if len(self.range_height) != 2:
                raise ValueError('need 2 values to unpack from range_height')
            for height in self.range_height:
                if not isinstance(height, (float, int)):
                    raise TypeError('height is not a number')
                if height < 0:
                    raise ValueError('value not allowed in height')
            if self.range_height[0] > self.range_height[1]:
                self.range_height[0], self.range_height[1] = (
                    self.range_height[1],
                    self.range_height[0]
                )

        if self.content_types:
            if not isinstance(self.content_types, (list, tuple)):
                raise TypeError('content_types is not iterable')
            for content_type in self.content_types:
                if not isinstance(content_type, basestring):
                    raise TypeError('content_type element is not a string')
                if self.range_width is not None or self.range_height is not None:
                    if content_type not in self.VALID_IMAGE_PROC:
                        raise ValueError('value not allowed in content_types')

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
                self.min_upload_size, self.max_upload_size = (
                    self.max_upload_size,
                    self.min_upload_size
                )

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

        if self.range_width is not None or self.range_height is not None:
            if content_type not in self.VALID_IMAGE_PROC:
                raise forms.ValidationError(
                    _('File type not supported, please only %r') %
                    (self.content_types,)
                )

            width, height = get_image_dimensions(file)

            if not(self.range_width[0] <= width <= self.range_width[1]):
                raise forms.ValidationError(
                    _('Invalid width %(width)spx, please only between %(min_width)s-%(max_width)s') %
                    {'width': width, 'min_width': self.range_width[0], 'max_width': self.range_width[1]}
                )

            if not(self.range_height[0] <= height <= self.range_height[1]):
                raise forms.ValidationError(
                    _('Invalid height %(height)spx, please only between %(min_height)s-%(max_height)s') %
                    {'height': height, 'min_height': self.range_height[0], 'max_height': self.range_height[1]}
                )

        if self.max_upload_size is not None and file._size > self.max_upload_size:
            raise forms.ValidationError(
                _('Please keep file size under %(max_upload_size)s. Current file size is %(size)s') %
                {'max_upload_size': filesizeformat(self.max_upload_size), 'size': filesizeformat(file._size)}
            )

        if self.min_upload_size is not None and file._size < self.min_upload_size:
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
                "range_width": ["range_width", {"default": None}],
                "range_height": ["range_height", {"default": None}],
            }
        ),
    ]
    # Modify this string, there should be the path to this class
    add_introspection_rules(rules, ["^app\.lib\.fields\.model\.RestrictedFileField"])
