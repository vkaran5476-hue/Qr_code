import qrcode
import qrcode as qr

from PIL import Image

qr=qrcode.QRCode(version=1,box_size=10,border=5)

# img=qr.make("https://www.youtube.com/watch?v=FOGRHBp6lvM&list=PLjVLYmrlmjGfAUdLiF2bQ-0l8SwNZ1sBl")
# img.save("youtube.png")

qr.add_data("https://www.google.com")
qr.make(fit=True)
img = qr.make_image(fill="black", back_color="white")
img.save("qr.png")


