from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from apiApp.models import (
    Categoria,
    MetodoPago,
    Pedido,
    PedidoItem,
    Producto,
    Proveedor,
    Tarifa,
)
from apiApp.serializers import PedidoSerializer


# ---------------------------------------------------------------------------
# 1. Pruebas de modelos
# ---------------------------------------------------------------------------
class ModelosTests(TestCase):
    def setUp(self):
        self.cat = Categoria.objects.create(nombre="Muebles")
        self.prov = Proveedor.objects.create(nombre="ProveedorTest")
        self.prod = Producto.objects.create(
            nombre="Mesa", descripcion="Mesa de madera", cantidad=50
        )
        self.prod.categorias.add(self.cat)
        self.prod.proveedores.add(self.prov)

        self.tarifa1 = Tarifa.objects.create(
            producto=self.prod, minimo=1, maximo=10, precio_unitario=15
        )
        self.tarifa2 = Tarifa.objects.create(
            producto=self.prod, minimo=11, maximo=None, precio_unitario=12
        )
        self.mp = MetodoPago.objects.create(nombre="BCP")
        self.pedido = Pedido.objects.create(
            nombre="Juan",
            apellido="Perez",
            dni="12345678",
            telefono="987654321",
            correo="juan@test.com",
            metodo_pago=self.mp,
            total=100,
        )

    # --- Categoria ---
    def test_categoria_str(self):
        self.assertEqual(str(self.cat), "Muebles")

    # --- Proveedor ---
    def test_proveedor_str(self):
        self.assertEqual(str(self.prov), "ProveedorTest")

    # --- Producto ---
    def test_producto_str(self):
        self.assertEqual(str(self.prod), "Mesa")

    def test_producto_activo_por_defecto(self):
        self.assertTrue(self.prod.activo)

    def test_producto_cantidad_por_defecto(self):
        p = Producto.objects.create(nombre="P2", descripcion="x")
        self.assertEqual(p.cantidad, 300)

    # --- Tarifa ---
    def test_tarifa_asociacion(self):
        self.assertIn(self.tarifa1, self.prod.tarifas.all())
        self.assertIn(self.tarifa2, self.prod.tarifas.all())

    # --- MetodoPago ---
    def test_metodopago_str(self):
        self.assertEqual(str(self.mp), "BCP")

    # --- Pedido ---
    def test_pedido_codigo_unico_5_digitos(self):
        self.assertEqual(len(self.pedido.codigo), 5)
        self.assertTrue(self.pedido.codigo.isdigit())

    def test_pedido_codigos_diferentes(self):
        p2 = Pedido.objects.create(
            nombre="Ana",
            apellido="Garcia",
            dni="11111111",
            telefono="999999999",
            correo="ana@test.com",
            metodo_pago=self.mp,
            total=0,
        )
        self.assertNotEqual(self.pedido.codigo, p2.codigo)

    # --- PedidoItem ---
    def test_pedidoitem_subtotal(self):
        pi = PedidoItem.objects.create(
            pedido=self.pedido, producto=self.prod, cantidad=5, precio_unitario=15
        )
        self.assertEqual(pi.subtotal(), 75)

    def test_pedido_subtotal_suma_items(self):
        PedidoItem.objects.create(
            pedido=self.pedido, producto=self.prod, cantidad=2, precio_unitario=10
        )
        PedidoItem.objects.create(
            pedido=self.pedido, producto=self.prod, cantidad=3, precio_unitario=5
        )
        self.assertEqual(self.pedido.subtotal, 35)  # 20 + 15

    def test_no_eliminar_producto_con_pedidos(self):
        from django.db.models import ProtectedError

        PedidoItem.objects.create(
            pedido=self.pedido, producto=self.prod, cantidad=1, precio_unitario=15
        )
        with self.assertRaises(ProtectedError):
            self.prod.delete()


# ---------------------------------------------------------------------------
# 2. Pruebas del serializer de pedido
# ---------------------------------------------------------------------------
class PedidoSerializerTests(TestCase):
    def setUp(self):
        self.mp = MetodoPago.objects.create(nombre="Yape")
        self.prod1 = Producto.objects.create(
            nombre="Kit Basico", descripcion="Basico", cantidad=20
        )
        self.tarifa1_1 = Tarifa.objects.create(
            producto=self.prod1, minimo=1, maximo=5, precio_unitario=10
        )
        self.tarifa1_2 = Tarifa.objects.create(
            producto=self.prod1, minimo=6, maximo=None, precio_unitario=8
        )
        self.prod2 = Producto.objects.create(
            nombre="Kit Premium", descripcion="Premium", cantidad=5
        )
        Tarifa.objects.create(
            producto=self.prod2, minimo=1, maximo=None, precio_unitario=25
        )

    def _build(self, items, envio_provincia=False):
        return {
            "nombre": "Test",
            "apellido": "User",
            "dni": "12345678",
            "telefono": "987654321",
            "correo": "test@test.com",
            "metodo_pago_id": self.mp.pk,
            "envio_provincia": envio_provincia,
            "items": items,
        }

    def test_creacion_pedido_tarifa_pequena(self):
        s = PedidoSerializer(data=self._build([{"producto_id": self.prod1.pk, "cantidad": 3}]))
        self.assertTrue(s.is_valid(), s.errors)
        pedido = s.save()
        self.prod1.refresh_from_db()
        self.assertEqual(pedido.total, 30)  # 3 x 10
        self.assertEqual(self.prod1.cantidad, 17)

    def test_creacion_pedido_tarifa_grande(self):
        s = PedidoSerializer(data=self._build([{"producto_id": self.prod1.pk, "cantidad": 7}]))
        self.assertTrue(s.is_valid(), s.errors)
        pedido = s.save()
        self.prod1.refresh_from_db()
        self.assertEqual(pedido.total, 56)  # 7 x 8
        self.assertEqual(self.prod1.cantidad, 13)

    def test_envio_provincia_agrega_8(self):
        s = PedidoSerializer(data=self._build(
            [{"producto_id": self.prod2.pk, "cantidad": 1}], envio_provincia=True
        ))
        self.assertTrue(s.is_valid(), s.errors)
        pedido = s.save()
        self.assertEqual(pedido.total, 33)  # 25 + 8

    def test_stock_insuficiente_rechazado(self):
        s = PedidoSerializer(data=self._build([{"producto_id": self.prod2.pk, "cantidad": 10}]))
        self.assertFalse(s.is_valid())
        self.assertIn("items", s.errors)

    def test_cantidad_invalida_cero(self):
        s = PedidoSerializer(data=self._build([{"producto_id": self.prod1.pk, "cantidad": 0}]))
        self.assertFalse(s.is_valid())

    def test_dni_invalido(self):
        data = self._build([{"producto_id": self.prod1.pk, "cantidad": 1}])
        data["dni"] = "1234"
        s = PedidoSerializer(data=data)
        self.assertFalse(s.is_valid())

    def test_telefono_invalido(self):
        data = self._build([{"producto_id": self.prod1.pk, "cantidad": 1}])
        data["telefono"] = "123"
        s = PedidoSerializer(data=data)
        self.assertFalse(s.is_valid())


# ---------------------------------------------------------------------------
# 3. Pruebas de permisos de la API REST
# ---------------------------------------------------------------------------
class APIPermissionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username="api-perm-test", is_staff=True
        )
        cls.token = Token.objects.create(user=cls.user)
        cls.cat = Categoria.objects.create(nombre="CatPerm")
        cls.prod = Producto.objects.create(
            nombre="ProdPerm", descripcion="x", cantidad=100
        )
        cls.prod.categorias.add(cls.cat)
        Tarifa.objects.create(
            producto=cls.prod, minimo=1, maximo=None, precio_unitario=5
        )
        cls.mp = MetodoPago.objects.create(nombre="PermMP")

    def setUp(self):
        self.api = APIClient()

    # --- Lectura pública (catálogo) ---
    def test_list_productos_publico(self):
        r = self.api.get("/api/productos/")
        self.assertEqual(r.status_code, 200)

    def test_list_categorias_publico(self):
        r = self.api.get("/api/categorias/")
        self.assertEqual(r.status_code, 200)

    def test_list_tarifas_publico(self):
        r = self.api.get("/api/tarifas/")
        self.assertEqual(r.status_code, 200)

    # --- Escritura restringida ---
    def test_post_productos_sin_auth_403(self):
        r = self.api.post(
            "/api/productos/",
            {"nombre": "X", "descripcion": "Y", "cantidad": 10},
            format="json",
        )
        self.assertEqual(r.status_code, 403)

    def test_post_productos_con_token_201(self):
        self.api.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        r = self.api.post(
            "/api/productos/",
            {"nombre": "PermProd", "descripcion": "ok", "cantidad": 50},
            format="json",
        )
        self.assertEqual(r.status_code, 201)

    def test_post_categorias_sin_auth_403(self):
        r = self.api.post("/api/categorias/", {"nombre": "X"}, format="json")
        self.assertEqual(r.status_code, 403)

    def test_put_producto_sin_auth_403(self):
        r = self.api.put(
            f"/api/productos/{self.prod.pk}/",
            {"nombre": "Mod", "descripcion": "x", "cantidad": 1},
            format="json",
        )
        self.assertEqual(r.status_code, 403)

    # --- Pedidos: lectura y escritura protegidas (datos personales) ---
    def test_list_pedidos_sin_auth_403(self):
        r = self.api.get("/api/pedidos/")
        self.assertEqual(r.status_code, 403)

    def test_list_pedidos_con_token_200(self):
        self.api.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        r = self.api.get("/api/pedidos/")
        self.assertEqual(r.status_code, 200)

    def test_list_pedido_items_sin_auth_403(self):
        r = self.api.get("/api/pedido-items/")
        self.assertEqual(r.status_code, 403)

    @patch("apiApp.views.pedido_views.enviar_correo_pedido")
    def test_post_pedidos_sin_auth_403(self, mock_email):
        r = self.api.post(
            "/api/pedidos/",
            {
                "nombre": "A",
                "apellido": "B",
                "dni": "11111111",
                "telefono": "999999999",
                "correo": "a@test.com",
                "metodo_pago_id": self.mp.pk,
                "envio_provincia": False,
                "items": [{"producto_id": self.prod.pk, "cantidad": 1}],
            },
            format="json",
        )
        self.assertEqual(r.status_code, 403)

    @patch("apiApp.views.pedido_views.enviar_correo_pedido")
    def test_post_pedidos_con_token_201(self, mock_email):
        self.api.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        # El correo se envía en transaction.on_commit: forzamos su ejecución.
        with self.captureOnCommitCallbacks(execute=True):
            r = self.api.post(
                "/api/pedidos/",
                {
                    "nombre": "C",
                    "apellido": "D",
                    "dni": "22222222",
                    "telefono": "988888888",
                    "correo": "c@test.com",
                    "metodo_pago_id": self.mp.pk,
                    "envio_provincia": False,
                    "items": [{"producto_id": self.prod.pk, "cantidad": 2}],
                },
                format="json",
            )
        self.assertEqual(r.status_code, 201)
        self.assertIn("codigo", r.data)
        mock_email.assert_called_once()


# ---------------------------------------------------------------------------
# 4. Pruebas de rate limiting en POST /api/token/
# ---------------------------------------------------------------------------
class TokenThrottleTests(TestCase):
    USERNAME = "throttle-user"
    PASSWORD = "ClaveSegura123!"

    def setUp(self):
        # El caché de throttle persiste entre tests: limpiarlo para aislar cada uno.
        cache.clear()
        self.api = APIClient()
        self.user = User.objects.create_user(
            username=self.USERNAME, password=self.PASSWORD
        )
        self.token = Token.objects.create(user=self.user)

    def tearDown(self):
        cache.clear()

    def _login(self, username, password):
        return self.api.post(
            "/api/token/",
            {"username": username, "password": password},
            format="json",
        )

    def test_login_valido_devuelve_token_200(self):
        r = self._login(self.USERNAME, self.PASSWORD)
        self.assertEqual(r.status_code, 200)
        self.assertIn("token", r.data)

    def test_cinco_intentos_fallidos_no_bloquean(self):
        for _ in range(5):
            r = self._login("nadie", "contrasena-mala")
            self.assertEqual(r.status_code, 400)

    def test_sexto_intento_fallido_recibe_429(self):
        for _ in range(5):
            self._login("nadie", "contrasena-mala")
        r = self._login("nadie", "contrasena-mala")
        self.assertEqual(r.status_code, 429)

    def test_limite_compartido_por_ip(self):
        # El contador es por IP, no por username intentado.
        for _ in range(5):
            self._login("atacante1", "mala1")
        r = self._login("atacante2", "mala2")
        self.assertEqual(r.status_code, 429)
