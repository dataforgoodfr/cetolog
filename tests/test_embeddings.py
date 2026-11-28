import numpy as np
from PIL import Image

from pipeline.embeddings import crop_keep_sea, sea_box


def test_sea_box_adds_margin_and_squares():
    # dauphin de 100 x 40 au centre d'une photo 1000 x 1000, marge 10 % -> carré de 120
    dolphin, photo = (450, 480, 550, 520), (1000, 1000)
    assert sea_box(dolphin, photo, 0.1, True) == (440, 440, 560, 560)
    # sans carré : 120 x 60
    assert sea_box(dolphin, photo, 0.1, False) == (440, 470, 560, 530)


def test_sea_box_stays_inside_photo():
    # dauphin collé au coin : le carré glisse dans la photo au lieu de déborder
    assert sea_box((0, 0, 100, 40), (1000, 1000), 0.1, True) == (0, 0, 120, 120)
    # photo trop basse pour un carré : coupé à la hauteur de la photo
    assert sea_box((400, 10, 600, 40), (1000, 50), 0.1, True) == (380, 0, 620, 50)


def test_crop_keep_sea_keeps_pixels():
    class FakeSegmenter:
        def __init__(self, box):
            self.box = box

        def mask(self, image):
            mask = Image.new("L", image.size, 0)
            mask.paste(255, self.box)
            return mask

    rng = np.random.default_rng(0)
    image = Image.fromarray(rng.integers(0, 255, (200, 300, 3), dtype=np.uint8))
    cropped = crop_keep_sea(FakeSegmenter((100, 80, 150, 100)), image, margin=0.1)
    assert cropped.size == (60, 60)
    # mêmes pixels que la photo : rien n'est peint
    expected = image.crop((95, 60, 155, 120))
    assert np.array_equal(np.asarray(cropped), np.asarray(expected))
    # masque vide : la photo telle quelle
    assert crop_keep_sea(FakeSegmenter((0, 0, 0, 0)), image).size == image.size
