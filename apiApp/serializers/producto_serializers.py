from rest_framework import serializers
from ..models import ImagenProducto, VideoProducto, Producto
from .categoria_serializers import CategoriaSerializer, TarifaSerializer


class ImagenProductoSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    public_id = serializers.SerializerMethodField()
    existing_url = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = ImagenProducto
        fields = ["id", "url", "public_id", "existing_url", "producto"]

    def get_url(self, obj):
        return obj.imagen.url if obj.imagen else None

    def get_public_id(self, obj):
        return obj.imagen.public_id if obj.imagen else None

    def create(self, validated_data):
        existing_url = validated_data.pop("existing_url", None)
        if existing_url:
            return ImagenProducto.objects.create(
                producto=validated_data["producto"],
                imagen=existing_url
            )
        return super().create(validated_data)


class VideoProductoSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    public_id = serializers.SerializerMethodField()
    existing_url = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = VideoProducto
        fields = ["id", "url", "public_id", "existing_url", "producto"]

    def get_url(self, obj):
        return obj.video.url if obj.video else None

    def get_public_id(self, obj):
        return obj.video.public_id if obj.video else None

    def create(self, validated_data):
        existing_url = validated_data.pop("existing_url", None)
        if existing_url:
            return VideoProducto.objects.create(
                producto=validated_data["producto"],
                video=existing_url
            )
        return super().create(validated_data)


class ProductoSerializer(serializers.ModelSerializer):
    categorias = CategoriaSerializer(many=True, read_only=True)
    tarifas = TarifaSerializer(many=True, read_only=True)
    imagenes = ImagenProductoSerializer(many=True, read_only=True)
    videos = VideoProductoSerializer(many=True, read_only=True)

    class Meta:
        model = Producto
        fields = '__all__'
