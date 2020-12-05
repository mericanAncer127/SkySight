import argparse
import glob
import matplotlib.pyplot as plt
import os
from PIL import Image

def auto_crop(folder):
    """
    Crop all images in folder to min width/height of images
    """
    imgs = [Image.open(img) for img in glob.glob(folder+"/*.png")]
    imgs = {
        "North": Image.open(folder+"/north.png"),
        "East": Image.open(folder+"/east.png"),
        "South": Image.open(folder+"/south.png"),
        "West": Image.open(folder+"/west.png")
    }

    min_w, min_h = float("inf"), float("inf")
    # Find the min width/height
    for img in imgs.values():
        min_w, min_h = min(min_w, img.size[0]), min(min_h, img.size[1])

    # Crop and save images
    final_imgs = dict.fromkeys(imgs.keys())

    for key, img in imgs.items():
        w, h = img.size
        m_w, m_h = (w - min_w) / 2, (h - min_h) / 2
        new = img.crop((
            m_w,
            m_h,
            w - m_w,
            h - m_h
        ))

        final_imgs[key] = new

        # new.save(os.path.join(folder, str(i) + ".png"))
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(nrows=2, ncols=2)
    ax1.imshow(final_imgs["North"])
    ax1.set_title("North Side")
    ax1.axis("off")

    ax2.imshow(final_imgs["South"])
    ax2.set_title("South Side")
    ax2.axis("off")

    ax3.imshow(final_imgs["East"])
    ax3.set_title("East Side")
    ax3.axis("off")

    ax4.imshow(final_imgs["West"])
    ax4.set_title("West Side")
    ax4.axis("off")

    plt.tight_layout()
    plt.savefig(folder+"/views", dpi=1500)
    # plt.show()

    return

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--f", dest="folder")
    args = parser.parse_args()

    auto_crop(args.folder)
