"""Client for Hacienda electronic invoicing API (Factura Electrónica v4.4)."""
import hashlib
import logging
import random
import string
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, Tuple
from uuid import UUID
import xml.etree.ElementTree as ET

from app.domain.models.invoice import Invoice, InvoiceLineItem
from app.domain.models.customer import Customer
from app.domain.models.tenant import Tenant
from app.infrastructure.integrations.hacienda.models import (
    FacturaElectronica,
    Emisor,
    Receptor,
    Identificacion,
    TipoIdentificacion,
    TipoDocumento,
    LineaDetalle,
    Impuesto,
    CodigoImpuesto,
    TarifaIVA,
    ResumenFactura,
    CodigoMoneda,
    CondicionVenta,
    MedioPago,
    UnidadMedida,
    HaciendaConfig,
    HaciendaResponse,
)

logger = logging.getLogger(__name__)

# Costa Rica IVA rate (13%)
IVA_RATE = Decimal("13.00")

# Province codes for clave generation
PROVINCE_CODES = {
    "San Jose": "1",
    "Alajuela": "2",
    "Cartago": "3",
    "Heredia": "4",
    "Guanacaste": "5",
    "Puntarenas": "6",
    "Limon": "7",
}


class HaciendaClient:
    """Client for interacting with Hacienda's electronic invoicing system."""

    def __init__(self, config: Optional[HaciendaConfig] = None):
        self.config = config or HaciendaConfig()
        self._access_token: Optional[str] = None
        self._token_expires: Optional[datetime] = None

    def generate_clave(
        self,
        tenant: Tenant,
        tipo_documento: TipoDocumento,
        consecutivo: int,
        situacion: str = "1",  # 1=Normal, 2=Contingencia, 3=Sin Internet
    ) -> str:
        """
        Generate the 50-digit clave (key) for an electronic document.

        Format: PDDMMAACC-CCCCCCCC-TTSS-CCCCCCCCCC-S-SSSSSSSS
        - P: País (506 for Costa Rica)
        - DD: Día
        - MM: Mes
        - AA: Año (last 2 digits)
        - CC-CCCCCCCC: Cédula emisor (12 digits)
        - TT: Tipo de documento
        - SS: Situación
        - CCCCCCCCCC: Consecutivo (10 digits)
        - S: Situación del comprobante
        - SSSSSSSS: Código de seguridad (8 random digits)
        """
        now = datetime.now(timezone.utc)

        # Country code
        pais = "506"

        # Date components
        dia = now.strftime("%d")
        mes = now.strftime("%m")
        anio = now.strftime("%y")

        # Sender ID (padded to 12 digits)
        cedula = (tenant.cedula_juridica or "").replace("-", "").zfill(12)

        # Document type
        tipo_doc = tipo_documento.value

        # Situation
        situacion_code = situacion.zfill(2)

        # Consecutive number (padded to 10 digits)
        consecutivo_str = str(consecutivo).zfill(10)

        # Security code (8 random digits)
        codigo_seguridad = "".join(random.choices(string.digits, k=8))

        # Assemble the key
        clave = (
            f"{pais}{dia}{mes}{anio}"
            f"{cedula}"
            f"{consecutivo_str}"
            f"{situacion_code}"
            f"{codigo_seguridad}"
        )

        # Ensure exactly 50 characters
        return clave[:50].zfill(50)

    def generate_consecutivo(
        self,
        sucursal: int,
        terminal: int,
        tipo_documento: TipoDocumento,
        consecutivo: int,
    ) -> str:
        """
        Generate the 20-digit consecutive number.

        Format: SSS-TTTTT-TT-CCCCCCCCCC
        - SSS: Sucursal (branch)
        - TTTTT: Terminal
        - TT: Tipo de documento
        - CCCCCCCCCC: Consecutivo
        """
        sucursal_str = str(sucursal).zfill(3)
        terminal_str = str(terminal).zfill(5)
        tipo_doc = tipo_documento.value
        consecutivo_str = str(consecutivo).zfill(10)

        return f"{sucursal_str}{terminal_str}{tipo_doc}{consecutivo_str}"

    def build_factura_electronica(
        self,
        invoice: Invoice,
        tenant: Tenant,
        customer: Customer,
        consecutivo: int,
    ) -> FacturaElectronica:
        """
        Build a FacturaElectronica from an Invoice.

        Args:
            invoice: The invoice to convert
            tenant: The tenant (issuer)
            customer: The customer (recipient)
            consecutivo: The sequential invoice number

        Returns:
            FacturaElectronica ready for XML generation
        """
        tipo_documento = TipoDocumento.FACTURA_ELECTRONICA

        # Generate clave and consecutivo
        clave = self.generate_clave(tenant, tipo_documento, consecutivo)
        numero_consecutivo = self.generate_consecutivo(1, 1, tipo_documento, consecutivo)

        # Build emisor (issuer)
        emisor = Emisor(
            nombre=tenant.legal_name or tenant.name,
            identificacion=Identificacion(
                tipo=TipoIdentificacion.CEDULA_JURIDICA,
                numero=(tenant.cedula_juridica or "").replace("-", ""),
            ),
            nombre_comercial=tenant.name,
            correo_electronico=tenant.email,
        )

        # Build receptor (recipient)
        receptor = None
        if customer:
            tipo_id = TipoIdentificacion.CEDULA_FISICA
            numero_id = customer.cedula

            if customer.customer_type.value == "business":
                tipo_id = TipoIdentificacion.CEDULA_JURIDICA
                numero_id = customer.cedula_juridica

            if numero_id:
                receptor = Receptor(
                    nombre=customer.display_name,
                    identificacion=Identificacion(
                        tipo=tipo_id,
                        numero=numero_id.replace("-", ""),
                    ),
                    correo_electronico=customer.email,
                )
            else:
                # Foreign customer without CR ID
                receptor = Receptor(
                    nombre=customer.display_name,
                    correo_electronico=customer.email,
                )

        # Build line items
        lineas_detalle = []
        total_gravado = Decimal("0")
        total_impuesto = Decimal("0")

        for idx, item in enumerate(invoice.line_items, start=1):
            # Calculate amounts
            subtotal = item.quantity * item.unit_price
            discount_amount = subtotal * (item.discount_percent / 100) if item.discount_percent else Decimal("0")
            subtotal_after_discount = subtotal - discount_amount
            tax_amount = subtotal_after_discount * (item.tax_rate / 100) if item.tax_rate else Decimal("0")
            total_line = subtotal_after_discount + tax_amount

            total_gravado += subtotal_after_discount
            total_impuesto += tax_amount

            # Build impuesto if tax rate > 0
            impuestos = []
            if item.tax_rate and item.tax_rate > 0:
                impuestos.append(Impuesto(
                    codigo=CodigoImpuesto.IVA,
                    codigo_tarifa=TarifaIVA.TARIFA_GENERAL,
                    tarifa=item.tax_rate,
                    monto=tax_amount,
                ))

            linea = LineaDetalle(
                numero_linea=idx,
                codigo_tipo="04",  # Internal code
                codigo=f"SERV-{idx:03d}",
                codigo_cabys="8531100000100",  # Storage services CABYS code
                cantidad=item.quantity,
                unidad_medida=UnidadMedida.SERVICIO,
                detalle=item.description[:200],
                precio_unitario=item.unit_price,
                monto_total=subtotal,
                subtotal=subtotal_after_discount,
                impuestos=impuestos,
                monto_total_linea=total_line,
            )
            lineas_detalle.append(linea)

        # Build resumen
        resumen = ResumenFactura(
            codigo_tipo_moneda=CodigoMoneda.CRC if invoice.currency == "CRC" else CodigoMoneda.USD,
            total_servicios_gravados=total_gravado,
            total_gravado=total_gravado,
            total_venta=total_gravado,
            total_venta_neta=total_gravado,
            total_impuesto=total_impuesto,
            total_comprobante=total_gravado + total_impuesto,
        )

        # Determine payment method
        medio_pago = [MedioPago.TRANSFERENCIA]  # Default to SINPE/transfer

        # Build the factura
        factura = FacturaElectronica(
            clave=clave,
            codigo_actividad=self.config.codigo_actividad,
            numero_consecutivo=numero_consecutivo,
            fecha_emision=datetime.now(timezone.utc),
            emisor=emisor,
            receptor=receptor,
            condicion_venta=CondicionVenta.CONTADO,
            medio_pago=medio_pago,
            detalle_servicio=lineas_detalle,
            resumen_factura=resumen,
        )

        return factura

    def generate_xml(self, factura: FacturaElectronica) -> str:
        """
        Generate the XML document for an electronic invoice.

        Returns:
            XML string for the factura electrónica
        """
        # XML namespaces
        nsmap = {
            None: "https://cdn.comprobanteselectronicos.go.cr/xml-schemas/v4.4/facturaElectronica",
            "xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "xsd": "http://www.w3.org/2001/XMLSchema",
        }

        # Build XML
        root = ET.Element("FacturaElectronica")
        root.set("xmlns", nsmap[None])
        root.set("xmlns:xsi", nsmap["xsi"])
        root.set("xmlns:xsd", nsmap["xsd"])

        # Clave
        ET.SubElement(root, "Clave").text = factura.clave

        # CodigoActividad
        ET.SubElement(root, "CodigoActividad").text = factura.codigo_actividad

        # NumeroConsecutivo
        ET.SubElement(root, "NumeroConsecutivo").text = factura.numero_consecutivo

        # FechaEmision
        ET.SubElement(root, "FechaEmision").text = factura.fecha_emision.strftime("%Y-%m-%dT%H:%M:%S-06:00")

        # Emisor
        emisor_elem = ET.SubElement(root, "Emisor")
        ET.SubElement(emisor_elem, "Nombre").text = factura.emisor.nombre
        id_elem = ET.SubElement(emisor_elem, "Identificacion")
        ET.SubElement(id_elem, "Tipo").text = factura.emisor.identificacion.tipo.value
        ET.SubElement(id_elem, "Numero").text = factura.emisor.identificacion.numero
        if factura.emisor.nombre_comercial:
            ET.SubElement(emisor_elem, "NombreComercial").text = factura.emisor.nombre_comercial
        ET.SubElement(emisor_elem, "CorreoElectronico").text = factura.emisor.correo_electronico

        # Receptor
        if factura.receptor:
            receptor_elem = ET.SubElement(root, "Receptor")
            ET.SubElement(receptor_elem, "Nombre").text = factura.receptor.nombre
            if factura.receptor.identificacion:
                id_elem = ET.SubElement(receptor_elem, "Identificacion")
                ET.SubElement(id_elem, "Tipo").text = factura.receptor.identificacion.tipo.value
                ET.SubElement(id_elem, "Numero").text = factura.receptor.identificacion.numero
            if factura.receptor.correo_electronico:
                ET.SubElement(receptor_elem, "CorreoElectronico").text = factura.receptor.correo_electronico

        # CondicionVenta
        ET.SubElement(root, "CondicionVenta").text = factura.condicion_venta.value

        # MedioPago
        for medio in factura.medio_pago:
            ET.SubElement(root, "MedioPago").text = medio.value

        # DetalleServicio
        detalle_elem = ET.SubElement(root, "DetalleServicio")
        for linea in factura.detalle_servicio:
            linea_elem = ET.SubElement(detalle_elem, "LineaDetalle")
            ET.SubElement(linea_elem, "NumeroLinea").text = str(linea.numero_linea)

            codigo_elem = ET.SubElement(linea_elem, "Codigo")
            ET.SubElement(codigo_elem, "Tipo").text = linea.codigo_tipo
            ET.SubElement(codigo_elem, "Codigo").text = linea.codigo

            if linea.codigo_cabys:
                ET.SubElement(linea_elem, "CodigoComercial").text = linea.codigo_cabys

            ET.SubElement(linea_elem, "Cantidad").text = f"{linea.cantidad:.3f}"
            ET.SubElement(linea_elem, "UnidadMedida").text = linea.unidad_medida.value
            ET.SubElement(linea_elem, "Detalle").text = linea.detalle
            ET.SubElement(linea_elem, "PrecioUnitario").text = f"{linea.precio_unitario:.5f}"
            ET.SubElement(linea_elem, "MontoTotal").text = f"{linea.monto_total:.5f}"
            ET.SubElement(linea_elem, "SubTotal").text = f"{linea.subtotal:.5f}"

            # Impuestos
            if linea.impuestos:
                for impuesto in linea.impuestos:
                    imp_elem = ET.SubElement(linea_elem, "Impuesto")
                    ET.SubElement(imp_elem, "Codigo").text = impuesto.codigo.value
                    ET.SubElement(imp_elem, "CodigoTarifa").text = impuesto.codigo_tarifa.value
                    ET.SubElement(imp_elem, "Tarifa").text = f"{impuesto.tarifa:.2f}"
                    ET.SubElement(imp_elem, "Monto").text = f"{impuesto.monto:.5f}"

            ET.SubElement(linea_elem, "MontoTotalLinea").text = f"{linea.monto_total_linea:.5f}"

        # ResumenFactura
        resumen_elem = ET.SubElement(root, "ResumenFactura")
        moneda_elem = ET.SubElement(resumen_elem, "CodigoTipoMoneda")
        ET.SubElement(moneda_elem, "CodigoMoneda").text = factura.resumen_factura.codigo_tipo_moneda.value
        if factura.resumen_factura.tipo_cambio:
            ET.SubElement(moneda_elem, "TipoCambio").text = f"{factura.resumen_factura.tipo_cambio:.5f}"

        ET.SubElement(resumen_elem, "TotalServGravados").text = f"{factura.resumen_factura.total_servicios_gravados:.5f}"
        ET.SubElement(resumen_elem, "TotalServExentos").text = f"{factura.resumen_factura.total_servicios_exentos:.5f}"
        ET.SubElement(resumen_elem, "TotalGravado").text = f"{factura.resumen_factura.total_gravado:.5f}"
        ET.SubElement(resumen_elem, "TotalExento").text = f"{factura.resumen_factura.total_exento:.5f}"
        ET.SubElement(resumen_elem, "TotalVenta").text = f"{factura.resumen_factura.total_venta:.5f}"
        ET.SubElement(resumen_elem, "TotalDescuentos").text = f"{factura.resumen_factura.total_descuentos:.5f}"
        ET.SubElement(resumen_elem, "TotalVentaNeta").text = f"{factura.resumen_factura.total_venta_neta:.5f}"
        ET.SubElement(resumen_elem, "TotalImpuesto").text = f"{factura.resumen_factura.total_impuesto:.5f}"
        ET.SubElement(resumen_elem, "TotalComprobante").text = f"{factura.resumen_factura.total_comprobante:.5f}"

        # Generate XML string
        xml_string = ET.tostring(root, encoding="unicode", method="xml")

        # Add XML declaration
        xml_declaration = '<?xml version="1.0" encoding="UTF-8"?>'
        return f"{xml_declaration}\n{xml_string}"

    async def submit_invoice(
        self,
        factura: FacturaElectronica,
    ) -> HaciendaResponse:
        """
        Submit an electronic invoice to Hacienda.

        In production, this would:
        1. Sign the XML with the business's digital certificate
        2. Authenticate with Hacienda's OAuth2 endpoint
        3. POST the signed XML to the reception endpoint
        4. Return the response

        For now, this is a stub that simulates the submission.
        """
        logger.info(f"Submitting invoice {factura.clave} to Hacienda")

        # Generate the XML
        xml_content = self.generate_xml(factura)

        # In production:
        # 1. Sign XML with certificate
        # 2. Get OAuth token
        # 3. POST to Hacienda API
        # 4. Handle response

        # Simulate successful response
        response = HaciendaResponse(
            clave=factura.clave,
            fecha=datetime.now(timezone.utc),
            ind_estado="1",  # Accepted
            mensaje="Documento procesado correctamente (simulado)",
        )

        logger.info(f"Invoice {factura.clave} submitted successfully (simulated)")

        return response

    async def check_status(self, clave: str) -> HaciendaResponse:
        """
        Check the status of a submitted document.

        Args:
            clave: The 50-digit document key

        Returns:
            HaciendaResponse with the current status
        """
        logger.info(f"Checking status for document {clave}")

        # In production, this would query Hacienda's API

        # Simulate response
        return HaciendaResponse(
            clave=clave,
            fecha=datetime.now(timezone.utc),
            ind_estado="1",
            mensaje="Documento aceptado",
        )
