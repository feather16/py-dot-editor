import os
import tkinter as tk
from tkinter import Button, filedialog
from tkinter import messagebox
from PIL import Image
import numpy as np
from enum import Enum

TITLE = 'PyDotEditor'
VERSION: str = '1.0'

class GUI(tk.Frame):
    class Mode(Enum):
        PEN = 1
        FILL = 2
    NAME_TO_MODE: dict = {
        'pen': Mode.PEN,
        'fill': Mode.FILL
    }

    def __init__(self, tk_root: tk.Tk):
        # 定数
        self.UPPER_SPACE: int = 96
        self.FILE_TYPES: list = [
            ('Image file', '.bmp .png .jpg .tif'),
            ('Bitmap', '.bmp'),
            ('PNG', '.png'),
            ('JPEG', '.jpg'),
            ('Tiff', '.tif')
        ]
        self.EXTS = ['.bmp', '.png', '.jpg', '.tif']
        self.DEFAULT_EXT = '.png'

        # 変数
        self.width: int = 512
        self.height: int = 512 + self.UPPER_SPACE
        self.pixel: np.ndarray = np.full((32, 32, 4), 255, dtype=np.uint8)
        self.path: str = ''
        self.dragging: bool = False
        self.mode: GUI.Mode = GUI.Mode.PEN

        # 初期化
        super().__init__(tk_root)
        self.tk_root: tk.Tk = tk_root
        self.tk_root.geometry('{}x{}'.format(self.width, self.height))
        self.tk_root.minsize(256, 256 + self.UPPER_SPACE)
        self.update_title()

        # キャンバス
        self.main_canvas = tk.Canvas(self.tk_root, width=self.width, height=self.height)
        self.update_all_pixels()
        self.main_canvas.place(x=0, y=self.UPPER_SPACE)
        self.main_canvas.pack(fill=tk.BOTH, expand=True)
        
        # ボタン
        #button1 = tk.Button(self.tk_root, text='Pen', command=lambda: self.on_switch_button('pen'))
        #button1.pack()
        #button1.place(x=20, y=20)
        #button2 = tk.Button(self.tk_root, text='Fill', command=lambda: self.on_switch_button('fill'))
        #button2.pack()
        #button2.place(x=60, y=20)

        # メニュー
        menubar = tk.Menu(self.tk_root)
        self.tk_root.config(menu=menubar)
        file_menu = tk.Menu(self.tk_root, tearoff=0)
        menubar.add_cascade(label='File', menu=file_menu)
        file_menu.add_command(label='Open', command=self.open_file)
        file_menu.add_command(label='Save', command=self.save_file)
        file_menu.add_command(label='Save As...', command=self.save_file_as)

        # イベント追加
        self.tk_root.bind('<Configure>', self.on_configure)
        self.tk_root.bind('<Button>', self.on_button)
        self.tk_root.bind('<ButtonRelease>', self.on_button_release)
        self.tk_root.bind('<Motion>', self.on_motion)

        # ショートカットキー
        self.tk_root.bind('<Control-o>', self.open_file)
        self.tk_root.bind('<Control-s>', self.save_file)

    def open_image(self, path: str) -> None:
        image: np.ndarray = np.array(Image.open(path))
        if 16 <= image.shape[0] <= 64 and 16 <= image.shape[1] <= 64:
            self.pixel = image
            self.path = path
            self.update_all_pixels()
            self.update_title()
        else:
            messagebox.showerror('Error', \
                'Can\'t open \'{}\'. Image size must be between 16x16 and 64x64.'.format(path))

    def on_configure(self, event: tk.Event) -> None:
        # ウィンドウサイズが変更されたとき
        if (event.width, event.height) != (self.width, self.height):
            self.width, self.height = event.width, event.height
            self.update_all_pixels()

    def on_button(self, event: tk.Event) -> None:
        if event.num == 1:
            self.dragging = True
            self.try_draw(event.x, event.y)

    def on_button_release(self, event: tk.Event) -> None:
        if event.num == 1:
            self.dragging = False

    def on_motion(self, event: tk.Event) -> None:
        if self.dragging:
            self.try_draw(event.x, event.y)

    def try_draw(self, x: float, y: float) -> bool:
        if self.coord_inside_image(x, y):      
            i, j = self.coord_to_indices(x, y)
            self.pixel[i][j] = 0, 0, 0, 255
            self.update_pixel(i, j)
            return True
        else:
            return False

    def open_file(self, e = None) -> None:
        filepath = filedialog.askopenfilename(filetypes=self.FILE_TYPES)
        # ファイルが選択されたなら
        if len(filepath) > 0:
            self.open_image(filepath)

    def save_file(self, e = None) -> None:
        if self.path != '':
            Image.fromarray(self.pixel).save(self.path)
        else:
            self.save_file_as()

    def save_file_as(self) -> None:
        filepath = filedialog.asksaveasfilename(filetypes=self.FILE_TYPES)
        if filepath == '':
            return
        _, ext = os.path.splitext(filepath)
        if ext == '':
            filepath += self.DEFAULT_EXT
        elif ext not in self.EXTS:
            messagebox.showerror('Error', 'Unsupported format \'{}\'.'.format(ext))
            return
        self.path = filepath
        self.update_title()
        self.save_file()

    def on_switch_button(self, name: str) -> None:
        self.mode = self.NAME_TO_MODE[name]

    def update_title(self) -> None:
        appname = '{} ver.{}'.format(TITLE, VERSION)
        if len(self.path) > 0:
            self.tk_root.title(os.path.basename(self.path) + ' - ' + appname)
        else:
            self.tk_root.title(appname)

    def update_all_pixels(self) -> None:
        self.main_canvas.delete('pixel')
        for i in range(self.image_size[0]):
            for j in range(self.image_size[1]):
                self.update_pixel(i, j)
    
    def update_pixel(self, i: int, j: int) -> None:
        fill: str = '#{:02x}{:02x}{:02x}'.format(*self.pixel[i][j][:3])
        coord: tuple = self.indices_to_coord(i, j)
        self.main_canvas.create_rectangle(
            coord[0],
            coord[1], 
            coord[0] + self.rect_size, 
            coord[1] + self.rect_size,
            fill=fill, 
            outline='white', tags='pixel')

    def indices_to_coord(self, i: int, j: int) -> tuple:
        return \
            self.rect_size * j, \
            self.rect_size * i + self.UPPER_SPACE

    def coord_inside_image(self, x: float, y: float) -> bool:
        i, j = self.coord_to_indices(x, y)
        return 0 <= i < self.image_size[0] and 0 <= j < self.image_size[1]

    def coord_to_indices(self, x: float, y: float) -> tuple:
        return \
            int((y - self.UPPER_SPACE) / self.rect_size), \
            int(x / self.rect_size)

    # 編集対象の画像のサイズ
    @property
    def image_size(self) -> tuple:
        return self.pixel.shape[:2]

    @property
    def rect_size(self) -> float:
        return min(self.width / self.image_size[0], (self.height - self.UPPER_SPACE) / self.image_size[1])
        
if __name__ == '__main__':
    tk_root = tk.Tk()
    gui = GUI(tk_root)
    gui.mainloop()