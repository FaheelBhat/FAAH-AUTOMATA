"""Utility functions for Phone Keyboard to PC"""
import socket
import qrcode
from PIL import Image, ImageTk


def get_local_ip():
    """Get the local IP address of this machine"""
    try:
        # Connect to a remote address to determine local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def generate_qr_code(url):
    """Generate a QR code image from a URL"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=3,  # Smaller QR code
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    return img


def qr_code_to_photoimage(url):
    """Convert QR code URL to PhotoImage for tkinter"""
    try:
        qr_img = generate_qr_code(url)
        photo = ImageTk.PhotoImage(qr_img)
        return photo
    except Exception as e:
        print(f"QR code error: {e}")
        return None

