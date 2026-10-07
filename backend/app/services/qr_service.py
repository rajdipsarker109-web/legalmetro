import os
import qrcode


def generate_qr(unique_instrument_id, frontend_url, upload_folder):
    url = f"{frontend_url}/verify.html?id={unique_instrument_id}"
    qr = qrcode.make(url)
    os.makedirs(os.path.join(upload_folder, 'qr'), exist_ok=True)
    filename = f"qr_{unique_instrument_id}.png"
    path = os.path.join(upload_folder, 'qr', filename)
    qr.save(path)
    return f"/uploads/qr/{filename}"
