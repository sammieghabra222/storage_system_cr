"""Models for Hacienda electronic invoicing (Factura Electrónica v4.4)."""
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class TipoDocumento(str, Enum):
    """Document types for electronic invoicing."""
    FACTURA_ELECTRONICA = "01"  # Factura Electrónica
    NOTA_DEBITO = "02"  # Nota de Débito Electrónica
    NOTA_CREDITO = "03"  # Nota de Crédito Electrónica
    TIQUETE_ELECTRONICO = "04"  # Tiquete Electrónico
    CONFIRMACION_ACEPTACION = "05"  # Confirmación de Aceptación
    CONFIRMACION_RECHAZO = "06"  # Confirmación de Rechazo Parcial
    FACTURA_ELECTRONICA_COMPRA = "08"  # Factura Electrónica de Compra
    FACTURA_ELECTRONICA_EXPORTACION = "09"  # Factura Electrónica de Exportación


class TipoIdentificacion(str, Enum):
    """ID types for Costa Rica."""
    CEDULA_FISICA = "01"  # Cédula Física
    CEDULA_JURIDICA = "02"  # Cédula Jurídica
    DIMEX = "03"  # DIMEX (foreigners)
    NITE = "04"  # NITE


class CodigoMoneda(str, Enum):
    """Currency codes."""
    CRC = "CRC"  # Costa Rican Colón
    USD = "USD"  # US Dollar
    EUR = "EUR"  # Euro


class CondicionVenta(str, Enum):
    """Sale conditions."""
    CONTADO = "01"  # Cash
    CREDITO = "02"  # Credit
    CONSIGNACION = "03"  # Consignment
    APARTADO = "04"  # Layaway
    ARRENDAMIENTO_OPCION_COMPRA = "05"  # Lease with purchase option
    ARRENDAMIENTO_FUNCION_FINANCIERA = "06"  # Financial lease
    COBRO_FAVOR_TERCERO = "07"  # Collection on behalf of third party
    SERVICIOS_PRESTADOS_EXTERIOR = "08"  # Services rendered abroad
    SERVICIOS_PRESTADOS_PAIS = "09"  # Services rendered in country
    OTROS = "99"  # Other


class MedioPago(str, Enum):
    """Payment methods."""
    EFECTIVO = "01"  # Cash
    TARJETA = "02"  # Card
    CHEQUE = "03"  # Check
    TRANSFERENCIA = "04"  # Bank transfer / SINPE
    RECAUDADO_TERCEROS = "05"  # Collected by third parties
    OTROS = "99"  # Other


class UnidadMedida(str, Enum):
    """Units of measure (CABYS codes)."""
    UNIDAD = "Unid"  # Unit
    SERVICIO = "Sp"  # Service
    METRO_CUADRADO = "m2"  # Square meter
    MES = "Mes"  # Month
    OTROS = "Os"  # Other services


class CodigoImpuesto(str, Enum):
    """Tax codes."""
    IVA = "01"  # Value Added Tax
    SELECTIVO_CONSUMO = "02"  # Selective consumption tax
    UNICO_COMBUSTIBLES = "03"  # Unique fuel tax
    BEBIDAS_ALCOHOLICAS = "04"  # Alcoholic beverages tax
    BEBIDAS_ENVASADAS = "05"  # Bottled beverages tax
    TABACO = "06"  # Tobacco tax
    IVA_CALCULO_ESPECIAL = "07"  # IVA special calculation
    IVA_BIENES_USADOS = "08"  # IVA used goods
    OTROS = "99"  # Other


class TarifaIVA(str, Enum):
    """IVA rate codes."""
    EXENTO = "01"  # Exempt (0%)
    TARIFA_REDUCIDA_1 = "02"  # Reduced rate 1% (canasta básica)
    TARIFA_REDUCIDA_2 = "03"  # Reduced rate 2%
    TARIFA_REDUCIDA_4 = "04"  # Reduced rate 4% (health services)
    TRANSITORIO_0 = "05"  # Transitory 0%
    TRANSITORIO_4 = "06"  # Transitory 4%
    TRANSITORIO_8 = "07"  # Transitory 8%
    TARIFA_GENERAL = "08"  # General rate 13%


# Pydantic models for XML generation

class Telefono(BaseModel):
    """Phone number."""
    codigo_pais: str = Field(default="506", max_length=3)
    numero: str = Field(..., max_length=20)


class Ubicacion(BaseModel):
    """Location/address."""
    provincia: str = Field(..., min_length=1, max_length=1)  # 1-7 for CR provinces
    canton: str = Field(..., min_length=2, max_length=2)
    distrito: str = Field(..., min_length=2, max_length=2)
    barrio: Optional[str] = Field(None, max_length=2)
    otras_senas: str = Field(..., max_length=250)


class Identificacion(BaseModel):
    """Identification."""
    tipo: TipoIdentificacion
    numero: str = Field(..., max_length=20)


class Emisor(BaseModel):
    """Invoice issuer (business)."""
    nombre: str = Field(..., max_length=100)
    identificacion: Identificacion
    nombre_comercial: Optional[str] = Field(None, max_length=80)
    ubicacion: Optional[Ubicacion] = None
    telefono: Optional[Telefono] = None
    correo_electronico: str = Field(..., max_length=160)


class Receptor(BaseModel):
    """Invoice recipient (customer)."""
    nombre: str = Field(..., max_length=100)
    identificacion: Optional[Identificacion] = None
    identificacion_extranjero: Optional[str] = Field(None, max_length=20)
    nombre_comercial: Optional[str] = Field(None, max_length=80)
    ubicacion: Optional[Ubicacion] = None
    telefono: Optional[Telefono] = None
    correo_electronico: Optional[str] = Field(None, max_length=160)


class Impuesto(BaseModel):
    """Tax on a line item."""
    codigo: CodigoImpuesto = CodigoImpuesto.IVA
    codigo_tarifa: TarifaIVA = TarifaIVA.TARIFA_GENERAL
    tarifa: Decimal = Field(default=Decimal("13.00"))
    factor_iva: Optional[Decimal] = None
    monto: Decimal = Field(..., ge=0)
    monto_exportacion: Optional[Decimal] = None


class Descuento(BaseModel):
    """Discount on a line item."""
    monto_descuento: Decimal = Field(..., ge=0)
    naturaleza_descuento: str = Field(..., max_length=80)


class LineaDetalle(BaseModel):
    """Invoice line item."""
    numero_linea: int = Field(..., ge=1)
    codigo_tipo: str = Field(default="04")  # 04 = Código interno
    codigo: str = Field(..., max_length=20)
    codigo_cabys: Optional[str] = Field(None, max_length=13)  # CABYS code
    cantidad: Decimal = Field(..., ge=0)
    unidad_medida: UnidadMedida = UnidadMedida.SERVICIO
    unidad_medida_comercial: Optional[str] = Field(None, max_length=20)
    detalle: str = Field(..., max_length=200)
    precio_unitario: Decimal = Field(..., ge=0)
    monto_total: Decimal = Field(..., ge=0)
    descuentos: List[Descuento] = Field(default_factory=list)
    subtotal: Decimal = Field(..., ge=0)
    base_imponible: Optional[Decimal] = None
    impuestos: List[Impuesto] = Field(default_factory=list)
    impuesto_neto: Optional[Decimal] = None
    monto_total_linea: Decimal = Field(..., ge=0)


class ResumenFactura(BaseModel):
    """Invoice summary totals."""
    codigo_tipo_moneda: CodigoMoneda = CodigoMoneda.CRC
    tipo_cambio: Optional[Decimal] = None
    total_servicios_gravados: Decimal = Field(default=Decimal("0"), ge=0)
    total_servicios_exentos: Decimal = Field(default=Decimal("0"), ge=0)
    total_servicios_exonerados: Decimal = Field(default=Decimal("0"), ge=0)
    total_mercancias_gravadas: Decimal = Field(default=Decimal("0"), ge=0)
    total_mercancias_exentas: Decimal = Field(default=Decimal("0"), ge=0)
    total_mercancias_exoneradas: Decimal = Field(default=Decimal("0"), ge=0)
    total_gravado: Decimal = Field(default=Decimal("0"), ge=0)
    total_exento: Decimal = Field(default=Decimal("0"), ge=0)
    total_exonerado: Decimal = Field(default=Decimal("0"), ge=0)
    total_venta: Decimal = Field(..., ge=0)
    total_descuentos: Decimal = Field(default=Decimal("0"), ge=0)
    total_venta_neta: Decimal = Field(..., ge=0)
    total_impuesto: Decimal = Field(default=Decimal("0"), ge=0)
    total_iva_devuelto: Optional[Decimal] = None
    total_otros_cargos: Optional[Decimal] = None
    total_comprobante: Decimal = Field(..., ge=0)


class InformacionReferencia(BaseModel):
    """Reference information (for credit/debit notes)."""
    tipo_doc: TipoDocumento
    numero: str = Field(..., max_length=50)
    fecha_emision: datetime
    codigo: str = Field(..., max_length=2)  # 01=Anula, 02=Corrige, etc.
    razon: str = Field(..., max_length=180)


class FacturaElectronica(BaseModel):
    """Complete electronic invoice document."""
    clave: str = Field(..., min_length=50, max_length=50)  # 50-digit key
    codigo_actividad: str = Field(..., max_length=6)  # Economic activity code
    numero_consecutivo: str = Field(..., min_length=20, max_length=20)
    fecha_emision: datetime
    emisor: Emisor
    receptor: Optional[Receptor] = None
    condicion_venta: CondicionVenta = CondicionVenta.CONTADO
    plazo_credito: Optional[str] = Field(None, max_length=10)
    medio_pago: List[MedioPago] = Field(default_factory=lambda: [MedioPago.TRANSFERENCIA])
    detalle_servicio: List[LineaDetalle] = Field(default_factory=list)
    informacion_referencia: Optional[List[InformacionReferencia]] = None
    resumen_factura: ResumenFactura


class HaciendaResponse(BaseModel):
    """Response from Hacienda API."""
    clave: str
    fecha: datetime
    ind_estado: str  # 1=Aceptado, 2=Aceptado Parcialmente, 3=Rechazado
    respuesta_xml: Optional[str] = None
    mensaje: Optional[str] = None


class HaciendaCredentials(BaseModel):
    """Credentials for Hacienda API."""
    usuario: str
    password: str
    pin: str  # Certificate PIN


class HaciendaConfig(BaseModel):
    """Configuration for Hacienda integration."""
    ambiente: str = Field(default="sandbox")  # sandbox or production
    api_url: str = Field(default="https://api.comprobanteselectronicos.go.cr/recepcion-sandbox/v1")
    token_url: str = Field(default="https://idp.comprobanteselectronicos.go.cr/auth/realms/rut-stag/protocol/openid-connect/token")
    credentials: Optional[HaciendaCredentials] = None
    certificate_path: Optional[str] = None
    codigo_actividad: str = Field(default="681001")  # Storage services activity code
