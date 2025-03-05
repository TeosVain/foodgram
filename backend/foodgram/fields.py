import base64
import imghdr
import uuid

from django.core.files.base import ContentFile
from rest_framework import serializers


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        """Декодирует base64-строку и сохраняет как файл."""
        if isinstance(data, str) and data.startswith('data:image'):
            try:
                format, imgstr = data.split(';base64,')
                ext = format.split('/')[-1]
                img_data = base64.b64decode(imgstr)
                if not ext or ext not in ['jpeg', 'jpg', 'png']:
                    ext = imghdr.what(None, h=img_data) or 'png'
                filename = f'{uuid.uuid4()}.{ext}'
                return ContentFile(img_data, name=filename)
            except Exception as e:
                raise serializers.ValidationError(
                    f'Ошибка декодирования изображения: {e}'
                )
        return super().to_internal_value(data)
