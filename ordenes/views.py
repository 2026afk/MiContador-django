from django.shortcuts import render

from datetime import date
from decimal import Decimal

from django.contrib import messages
from django.db.models import Case, DecimalField, F, Sum, When
from django.db.models.functions import TruncMonth
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from .forms import MovimientoForm
from .models import Movimiento, Usuario


def _usuario_actual(request):
    """Devuelve el Usuario de la sesión o None."""
    uid = request.session.get("usuario_id")
    if not uid:
        return None
    return Usuario.objects.filter(pk=uid).first()

MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun",
         "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
MESES_GRAFICA = 6  # cuántos meses muestra la gráfica


def _ultimos_meses(n):
    """Lista de (año, mes) de los últimos n meses, el actual al final."""
    hoy = date.today()
    anio, mes = hoy.year, hoy.month
    meses = []
    for _ in range(n):
        meses.append((anio, mes))
        mes -= 1
        if mes == 0:
            mes, anio = 12, anio - 1
    return list(reversed(meses))


def _datos_grafica(movimientos):
    """Totales mensuales de ingresos y egresos, ya convertidos a coordenadas SVG
    (viewBox 400x200) para la gráfica del menú."""
    meses = _ultimos_meses(MESES_GRAFICA)
    desde = date(meses[0][0], meses[0][1], 1)

    filas = (
        movimientos.filter(fecha__gte=desde)
        .annotate(mes=TruncMonth("fecha"))
        .values("mes", "tipo")
        .annotate(total=Sum("monto"))
    )
    totales = {}
    for f in filas:
        clave = (f["mes"].year, f["mes"].month, bool(f["tipo"]))
        totales[clave] = f["total"]

    ingresos = [totales.get((a, m, True), Decimal("0")) for a, m in meses]
    egresos = [totales.get((a, m, False), Decimal("0")) for a, m in meses]

    maximo = max(ingresos + egresos + [Decimal("0")])
    x_ini, x_fin = 20, 380
    y_base, y_alto = 180, 160  # y=180 es el valor 0; y=20 es el máximo
    paso = (x_fin - x_ini) / (len(meses) - 1)

    def puntos(valores):
        res = []
        for i, v in enumerate(valores):
            y = y_base if maximo == 0 else y_base - float(v / maximo) * y_alto
            res.append({
                "x": round(x_ini + i * paso, 1),
                "y": round(y, 1),
                "valor": v,
                "mes": MESES[meses[i][1] - 1],
            })
        return res

    p_ing, p_egr = puntos(ingresos), puntos(egresos)
    return {
        "ingresos": p_ing,
        "egresos": p_egr,
        "linea_ingresos": " ".join(f"{p['x']},{p['y']}" for p in p_ing),
        "linea_egresos": " ".join(f"{p['x']},{p['y']}" for p in p_egr),
        "etiquetas": [MESES[m - 1] for _, m in meses],
        "hay_datos": maximo > 0,
    }


@require_http_methods(["GET", "POST"])
def login_view(request):
    """Equivale a index.jsp + loginservlet."""
    if _usuario_actual(request):
        return redirect("menu_inicio")

    if request.method == "POST":
        nombre = request.POST.get("nombre", "").strip()
        contrasena = request.POST.get("contrasena", "")

        usuario = Usuario.objects.filter(nombre=nombre).first()
        if usuario and usuario.verificar_contrasena(contrasena):
            request.session["usuario_id"] = usuario.pk
            request.session["usuario_nombre"] = usuario.nombre
            return redirect("menu_inicio")

        messages.error(request, "Nombre o contraseña incorrectos.")

    return render(request, "index.html")


@require_http_methods(["GET", "POST"])
def registro_view(request):
    """Equivale a registro.jsp + usuarioservlet (accion=NuevaCuenta)."""
    if request.method == "POST":
        nombre = request.POST.get("nombre", "").strip()
        contrasena = request.POST.get("contrasena", "")

        if not nombre or not contrasena:
            messages.error(request, "Completa todos los campos.")
        elif len(nombre) > 30:
            messages.error(request, "El nombre puede tener máximo 30 caracteres.")
        elif len(contrasena) < 8:
            messages.error(request, "La contraseña debe tener mínimo 8 caracteres.")
        elif Usuario.objects.filter(nombre=nombre).exists():
            messages.error(request, "Ya existe un perfil con ese nombre.")
        else:
            usuario = Usuario(nombre=nombre)
            usuario.set_contrasena(contrasena)
            usuario.save()
            messages.success(request, "Perfil creado. Ya puedes iniciar sesión.")
            return redirect("login")

    return render(request, "registro.html")


def menu_inicio(request):
    """Equivale a MenuInicio.jsp (requiere sesión iniciada)."""
    usuario = _usuario_actual(request)
    if not usuario:
        return redirect("login")

    movimientos = Movimiento.objects.filter(usuario=usuario)
    cero = Decimal("0.00")
    totales = movimientos.aggregate(
        saldo=Sum(
            Case(
                When(tipo=True, then=F("monto")),
                default=-F("monto"),
                output_field=DecimalField(max_digits=14, decimal_places=2),
            )
        )
    )

    return render(
        request,
        "menu_inicio.html",
        {
            "nombre": usuario.nombre,
            "saldo": totales["saldo"] or cero,
            "recientes": movimientos[:5],
            "grafica": _datos_grafica(movimientos),
        },
    )


@require_http_methods(["GET", "POST"])
def agregar_movimiento(request):
    """Registra un ingreso o egreso en la tabla `movimientos`."""
    usuario = _usuario_actual(request)
    if not usuario:
        return redirect("login")

    if request.method == "POST":
        form = MovimientoForm(request.POST)
        if form.is_valid():
            movimiento = form.save(commit=False)
            movimiento.usuario = usuario
            movimiento.save()
            messages.success(request, "Movimiento registrado.")
            return redirect("menu_inicio")
    else:
        form = MovimientoForm()

    return render(
        request,
        "agregar_movimiento.html",
        {"form": form, "nombre": usuario.nombre},
    )

#-------Cerrar sesion------------
def logout_view(request):
    request.session.flush()
    return redirect("login")
