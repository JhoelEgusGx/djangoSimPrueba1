from rest_framework import serializers
from ..models import MetodoPago


class MetodoPagoSerializer(serializers.ModelSerializer):
    qr_imagen_url = serializers.SerializerMethodField()
    qr_imagen_id = serializers.SerializerMethodField()
    existing_url = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = MetodoPago
        fields = [
            "id", "nombre", "descripcion",
            "qr_imagen", "existing_url",
            "qr_imagen_url", "qr_imagen_id",
            "numero_cuenta"
        ]
        extra_kwargs = {
            "qr_imagen": {"write_only": True}
        }

    def get_qr_imagen_url(self, obj):
        return obj.qr_imagen.url if hasattr(obj.qr_imagen, "url") else obj.qr_imagen

    def get_qr_imagen_id(self, obj):
        return obj.qr_imagen.public_id if hasattr(obj.qr_imagen, "public_id") else None

    def create(self, validated_data):
        existing_url = validated_data.pop("existing_url", None)
        if existing_url:
            return MetodoPago.objects.create(
                qr_imagen=existing_url,
                **validated_data
            )
        return super().create(validated_data)

    def update(self, instance, validated_data):
        existing_url = validated_data.pop("existing_url", None)
        if existing_url:
            instance.qr_imagen = existing_url
        return super().update(instance, validated_data)
