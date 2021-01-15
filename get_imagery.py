from PIL import Image
import urllib.request
from io import BytesIO
import matplotlib.pyplot as plt

API_KEY = "AIzaSyB__zaEuZyD_B4Mg9g5oKB7hnsXMFeR26Q"

url = "https://maps.googleapis.com/maps/api/staticmap?"

if __name__ == "__main__":

    lat = 42.9470
    lng = -76.4291

    f = urllib.request.urlopen(
        url + \
        "center="+",".join([str(lat), str(lng)]) + \
        "&size=400x400" + \
        "&tilt=45" + \
        "&maptype=satellite" + \
        "&zoom=19" + \
        "&key=" + API_KEY
    )

    buffer = BytesIO(f.read())

    img = Image.open(buffer)

    plt.imshow(img)
    plt.show()

