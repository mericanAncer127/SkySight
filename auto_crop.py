import argparse
from PIL import Image
import glob
import os

def auto_crop(folder):
    """
    Crop all images in folder to min width/height of images
    """
    imgs = [Image.open(img) for img in glob.glob(folder+"/*.png")]
    min_w, min_h = float("inf"), float("inf")
    # Find the min width/height
    for img in imgs:
        min_w, min_h = min(min_w, img.size[0]), min(min_h, img.size[1])

    # Crop and save images
    for i, img in enumerate(imgs):
        w, h = img.size
        m_w, m_h = (w - min_w) / 2, (h - min_h) / 2
        new = img.crop((
            m_w,
            m_h,
            w - m_w,
            h - m_h
        ))

        new.save(os.path.join(folder, str(i) + ".png"))

    return

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--f", dest="folder")
    args = parser.parse_args()

    auto_crop(args.folder)
