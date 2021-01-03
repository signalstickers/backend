# pylint: disable=invalid-name
class TestSticker:
    def __init__(self, sticker_id, img_data):
        self.id = sticker_id
        self.image_data = img_data


class TestPack:
    def __init__(self, title, author, *args):
        self.title = title
        self.author = author
        self.cover = TestSticker(42, b"\x00")
        self.stickers = [TestSticker(id + 1, arg) for id, arg in enumerate(args)]
