from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token


class Command(BaseCommand):
    help = (
        "Crea (si no existe) el usuario de servicio api-servicio y muestra su "
        "token de API. Úsalo para obtener el valor de BACKEND_TOKEN del frontend."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--username",
            type=str,
            default="api-servicio",
            help="Nombre de usuario de servicio (default: api-servicio).",
        )
        parser.add_argument(
            "--email",
            type=str,
            default="jhoelegus357@gmail.com",
            help="Correo del usuario de servicio (default: corporativo).",
        )

    def handle(self, *args, **kwargs):
        username = kwargs["username"]
        email = kwargs["email"]

        user, created = User.objects.get_or_create(
            username=username,
            defaults={"email": email, "is_staff": True},
        )
        if created or not user.has_usable_password():
            user.is_staff = True
            user.set_unusable_password()
            user.save()
            self.stdout.write(self.style.WARNING(
                f"Usuario '{username}' creado/ajustado (sin contraseña)."
            ))

        token, _ = Token.objects.get_or_create(user=user)
        self.stdout.write(self.style.SUCCESS(
            f"Token de API para '{username}':\n{token.key}"
        ))