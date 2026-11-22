from django import forms
from django.utils import timezone

from .models import Movimiento


class MovimientoForm(forms.ModelForm):
    tipo = forms.TypedChoiceField(
        choices=[(1, "Ingreso"), (0, "Egreso")],
        coerce=lambda v: bool(int(v)),
        widget=forms.RadioSelect,
        initial=0,
    )
    fecha = forms.DateTimeField(
        input_formats=["%Y-%m-%dT%H:%M", "%Y-%m-%dT%H:%M:%S"],
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"
        ),
    )

    class Meta:
        model = Movimiento
        fields = ["tipo", "monto", "descripcion", "fecha"]
        widgets = {
            "monto": forms.NumberInput(attrs={"step": "0.01", "min": "0.01", "placeholder": "0.00"}),
            "descripcion": forms.TextInput(attrs={"placeholder": "Ej: Mercado, salario, arriendo"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_bound:
            self.initial["fecha"] = timezone.localtime().replace(second=0, microsecond=0) \
                if timezone.is_aware(timezone.now()) else timezone.now().replace(second=0, microsecond=0)

    def clean_monto(self):
        monto = self.cleaned_data["monto"]
        if monto <= 0:
            raise forms.ValidationError("El monto debe ser mayor que cero.")
        return monto