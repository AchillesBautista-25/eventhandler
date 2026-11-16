import io, base64
import qrcode


def qr_data_url(data: str, box_size: int = 8) -> str:
    """Generate a PNG data-URL QR code for the given text."""
    img = qrcode.make(data, box_size=box_size)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()