"""SINPE QR code generator for Costa Rica payments.

SINPE Móvil QR codes follow a specific format that banking apps can scan.
The QR contains payment information that pre-fills the transfer details.
"""
import base64
import io
import json
from decimal import Decimal
from typing import Optional
from uuid import UUID

try:
    import qrcode
    from qrcode.image.svg import SvgImage
    HAS_QRCODE = True
except ImportError:
    HAS_QRCODE = False

from pydantic import BaseModel, Field


class SinpeQRData(BaseModel):
    """Data structure for SINPE QR code."""

    # Recipient information
    phone_number: str = Field(..., description="SINPE Móvil phone number (8 digits)")
    recipient_name: str = Field(..., max_length=100, description="Recipient name")

    # Payment information
    amount: Optional[Decimal] = Field(None, ge=0, description="Payment amount in CRC")
    currency: str = Field(default="CRC", max_length=3)
    description: Optional[str] = Field(None, max_length=100, description="Payment description")

    # Reference information
    invoice_number: Optional[str] = Field(None, max_length=50)
    reference: Optional[str] = Field(None, max_length=50)


class SinpeQRResult(BaseModel):
    """Result of QR code generation."""

    qr_data: str = Field(..., description="Raw QR code data string")
    qr_base64: Optional[str] = Field(None, description="Base64 encoded PNG image")
    qr_svg: Optional[str] = Field(None, description="SVG image string")
    phone_number: str
    amount: Optional[Decimal]
    description: Optional[str]


class SinpeQRGenerator:
    """
    Generator for SINPE Móvil QR codes.

    SINPE QR codes encode payment information in a format that
    Costa Rican banking apps can read to pre-fill transfer details.
    """

    # SINPE QR format specification
    # Format: SINPE|{phone}|{name}|{amount}|{currency}|{description}|{reference}
    QR_PREFIX = "SINPE"
    FIELD_SEPARATOR = "|"

    def __init__(self):
        if not HAS_QRCODE:
            raise RuntimeError(
                "qrcode library not installed. Run: pip install qrcode[pil]"
            )

    def generate_qr_data(self, data: SinpeQRData) -> str:
        """
        Generate the raw data string for a SINPE QR code.

        Format: SINPE|phone|name|amount|currency|description|reference
        """
        # Clean phone number (remove +506, spaces, dashes)
        phone = self._clean_phone_number(data.phone_number)

        # Format amount (no decimals for CRC, 2 decimals for USD)
        amount_str = ""
        if data.amount is not None:
            if data.currency == "CRC":
                amount_str = str(int(data.amount))
            else:
                amount_str = f"{data.amount:.2f}"

        # Build QR data string
        parts = [
            self.QR_PREFIX,
            phone,
            data.recipient_name[:100],
            amount_str,
            data.currency,
            (data.description or "")[:100],
            (data.reference or data.invoice_number or "")[:50],
        ]

        return self.FIELD_SEPARATOR.join(parts)

    def generate_qr_image(
        self,
        data: SinpeQRData,
        size: int = 300,
        format: str = "png",
    ) -> SinpeQRResult:
        """
        Generate a QR code image for SINPE payment.

        Args:
            data: Payment data for QR code
            size: Image size in pixels (default 300)
            format: Output format ('png' or 'svg')

        Returns:
            SinpeQRResult with base64 encoded image
        """
        qr_data = self.generate_qr_data(data)

        # Create QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)

        result = SinpeQRResult(
            qr_data=qr_data,
            phone_number=self._clean_phone_number(data.phone_number),
            amount=data.amount,
            description=data.description,
        )

        if format.lower() == "svg":
            # Generate SVG
            img = qr.make_image(image_factory=SvgImage)
            buffer = io.BytesIO()
            img.save(buffer)
            result.qr_svg = buffer.getvalue().decode("utf-8")
        else:
            # Generate PNG
            img = qr.make_image(fill_color="black", back_color="white")
            img = img.resize((size, size))
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            result.qr_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

        return result

    def generate_payment_qr(
        self,
        phone_number: str,
        recipient_name: str,
        amount: Decimal,
        invoice_number: Optional[str] = None,
        description: Optional[str] = None,
    ) -> SinpeQRResult:
        """
        Convenience method to generate a payment QR code.

        Args:
            phone_number: SINPE Móvil number
            recipient_name: Name of recipient (business name)
            amount: Payment amount in CRC
            invoice_number: Optional invoice reference
            description: Optional payment description

        Returns:
            SinpeQRResult with QR code image
        """
        data = SinpeQRData(
            phone_number=phone_number,
            recipient_name=recipient_name,
            amount=amount,
            currency="CRC",
            description=description or f"Pago factura {invoice_number}" if invoice_number else None,
            invoice_number=invoice_number,
        )

        return self.generate_qr_image(data)

    def _clean_phone_number(self, phone: str) -> str:
        """Clean phone number to 8-digit format."""
        # Remove common prefixes and formatting
        cleaned = phone.replace("+506", "").replace("-", "").replace(" ", "").strip()

        # Keep only digits
        digits = "".join(c for c in cleaned if c.isdigit())

        # Return last 8 digits (Costa Rica mobile numbers)
        return digits[-8:] if len(digits) >= 8 else digits

    def parse_qr_data(self, qr_string: str) -> Optional[SinpeQRData]:
        """
        Parse a SINPE QR code data string.

        Args:
            qr_string: Raw QR code data

        Returns:
            SinpeQRData if valid, None otherwise
        """
        try:
            if not qr_string.startswith(self.QR_PREFIX):
                return None

            parts = qr_string.split(self.FIELD_SEPARATOR)
            if len(parts) < 3:
                return None

            return SinpeQRData(
                phone_number=parts[1] if len(parts) > 1 else "",
                recipient_name=parts[2] if len(parts) > 2 else "",
                amount=Decimal(parts[3]) if len(parts) > 3 and parts[3] else None,
                currency=parts[4] if len(parts) > 4 and parts[4] else "CRC",
                description=parts[5] if len(parts) > 5 else None,
                reference=parts[6] if len(parts) > 6 else None,
            )
        except (ValueError, IndexError):
            return None


# Simple implementation without qrcode library for basic functionality
class SimpleSinpeQRGenerator:
    """
    Simple QR generator that returns data URL for client-side rendering.

    Use this when the qrcode library is not available.
    The frontend can use a JavaScript QR library to render.
    """

    QR_PREFIX = "SINPE"
    FIELD_SEPARATOR = "|"

    def generate_qr_data(self, data: SinpeQRData) -> str:
        """Generate the raw data string for a SINPE QR code."""
        phone = data.phone_number.replace("+506", "").replace("-", "").replace(" ", "")
        phone = "".join(c for c in phone if c.isdigit())[-8:]

        amount_str = ""
        if data.amount is not None:
            amount_str = str(int(data.amount)) if data.currency == "CRC" else f"{data.amount:.2f}"

        parts = [
            self.QR_PREFIX,
            phone,
            data.recipient_name[:100],
            amount_str,
            data.currency,
            (data.description or "")[:100],
            (data.reference or data.invoice_number or "")[:50],
        ]

        return self.FIELD_SEPARATOR.join(parts)

    def generate_payment_qr(
        self,
        phone_number: str,
        recipient_name: str,
        amount: Decimal,
        invoice_number: Optional[str] = None,
        description: Optional[str] = None,
    ) -> dict:
        """Generate QR data for client-side rendering."""
        data = SinpeQRData(
            phone_number=phone_number,
            recipient_name=recipient_name,
            amount=amount,
            currency="CRC",
            description=description or f"Pago factura {invoice_number}" if invoice_number else None,
            invoice_number=invoice_number,
        )

        qr_data = self.generate_qr_data(data)

        return {
            "qr_data": qr_data,
            "phone_number": phone_number,
            "recipient_name": recipient_name,
            "amount": float(amount) if amount else None,
            "currency": "CRC",
            "description": data.description,
            "invoice_number": invoice_number,
        }


def get_sinpe_qr_generator():
    """Get the appropriate QR generator based on available libraries."""
    if HAS_QRCODE:
        return SinpeQRGenerator()
    return SimpleSinpeQRGenerator()
