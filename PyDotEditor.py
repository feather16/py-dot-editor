import os
import tkinter as tk
from tkinter import Button, filedialog, messagebox
from PIL import Image, ImageTk
import numpy as np
from enum import Enum

TITLE = 'PyDotEditor'
VERSION: str = '1.0'

def get_active_image(image: Image) -> Image:
    '''
    アイコン(pen, fill)の画像を選択状態にする
    '''
    new_image: Image = image.copy()
    size = new_image.size
    for x in range(size[0]):
        for y in range(size[1]):
            r ,g, b, a = image.getpixel((x, y))
            if a == 0:
                r, g, b, a = 160, 224, 255, 255
            new_image.putpixel((x, y),(r, g, b, a))
    return new_image

class GUI(tk.Frame):
    class Mode(Enum):
        PEN = 1
        FILL = 2
    NAME_TO_MODE: dict[str, Mode] = {
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

        self.PEN_ICON_PATH = os.path.dirname(__file__) + '/image/icon_pen.png'
        self.FILL_ICON_PATH = os.path.dirname(__file__) + '/image/icon_fill.png'

        COLORS: list[tuple[int, int, int]] = [
            (  0,   0,   0), # 黒
            (255, 255, 255), # 白
            (255,   0,   0), # 赤
            (255, 127,   0), # 橙
            (255, 255,   0), # 黄
            (  0, 255,   0), # 緑
            (  0, 255, 255), # 水
            (  0,   0, 255), # 青
            (255,   0, 255), # 桃
        ]

        # 変数
        self.width: int = 512
        self.height: int = 512 + self.UPPER_SPACE
        self.pixel: np.ndarray = np.full((32, 32, 4), 255, dtype=np.uint8)
        self.path: str = ''
        self.dragging: bool = False
        self.mode: GUI.Mode = GUI.Mode.PEN
        self.color: np.ndarray = np.zeros((3,), dtype=int)
        
        # 初期化
        super().__init__(tk_root)
        self.tk_root: tk.Tk = tk_root
        self.tk_root.geometry('{}x{}'.format(self.width, self.height))
        self.tk_root.minsize(256, 256 + self.UPPER_SPACE)
        self.update_title()

        # キャンバス
        self.main_canvas = tk.Canvas(self.tk_root, width=self.width, height=self.height)
        self.update_all_pixels()
        self.main_canvas.place(x=0, y=0)
        self.main_canvas.pack(fill=tk.BOTH, expand=True)
        self.set_color(np.zeros((3,), dtype=int))

        # ラベル
        self.current_color_label = tk.Label(
            self.tk_root, 
            text='Color',
            font=("Arial", 12)
        )
        self.current_color_label.pack()
        self.current_color_label.place(x=114, y=55)

        # ボタンのアイコン
        pen_icon_image = Image.open(self.PEN_ICON_PATH)
        pen_icon_image = pen_icon_image.resize((20, 20))
        self.pen_icon = ImageTk.PhotoImage(pen_icon_image)
        pen_icon_image_active = get_active_image(pen_icon_image)
        self.pen_icon_active = ImageTk.PhotoImage(pen_icon_image_active)
        fill_icon_image = Image.open(self.FILL_ICON_PATH)
        fill_icon_image = fill_icon_image.resize((20, 20))
        self.fill_icon = ImageTk.PhotoImage(fill_icon_image)
        fill_icon_image_active = get_active_image(fill_icon_image)
        self.fill_icon_active = ImageTk.PhotoImage(fill_icon_image_active)
        
        # ボタン
        self.pen_button = tk.Button(self.tk_root, text='Pen', command=lambda: self.on_switch_button('pen'), image=self.pen_icon_active)
        self.pen_button.pack()
        self.pen_button.place(x=20, y=20)
        self.fill_button = tk.Button(self.tk_root, text='Fill', command=lambda: self.on_switch_button('fill'), image=self.fill_icon)
        self.fill_button.pack()
        self.fill_button.place(x=60, y=20)

        # 色変更ボタン
        self.color_buttons: list[tk.Button] = []
        self.virtual_pixel = tk.PhotoImage(width=1, height=1)
        for i, color in enumerate(COLORS):
            button = tk.Button(
                self.tk_root, 
                bg='#{:02x}{:02x}{:02x}'.format(*color),
                width=20,
                height=20,
                image=self.virtual_pixel,
            )
            button.config(command=(lambda c: (lambda: self.set_color(c)))(color))
            button.pack()
            button.place(x=180+i*32, y=20)
            self.color_buttons.append(button)
        
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
        '''
        画面がクリック(押されたとき)
        '''
        if event.num == 1: # 左クリック
            self.dragging = True
            if self.mode == self.Mode.PEN:
                self.try_draw(event.x, event.y)
            elif self.mode == self.Mode.FILL:
                self.try_fill(event.x, event.y)
            else:
                raise NotImplementedError
            

    def on_button_release(self, event: tk.Event) -> None:
        '''
        画面がクリック(離されたとき)
        '''
        if event.num == 1: # 左クリック
            self.dragging = False

    def on_motion(self, event: tk.Event) -> None:
        if self.dragging:
            self.try_draw(event.x, event.y)

    def try_draw(self, x: float, y: float) -> bool:
        '''
        画面上の座標(`x`, `y`)に対して、可能であれば対応するピクセルを塗りつぶす
        '''
        if self.coord_inside_image(x, y):      
            i, j = self.coord_to_indices(x, y)
            self.pixel[i][j] = np.concatenate([self.color, [255]])
            self.update_pixel(i, j)
            return True
        else:
            return False

    def try_fill(self, x: float, y: float) -> bool:
        '''
        画面上の座標(`x`, `y`)に対して、可能であれば対応するピクセルをベースとしてfill操作を実行
        '''
        if self.coord_inside_image(x, y):      
            i, j = self.coord_to_indices(x, y)
            base_color: np.ndarray = np.copy(self.pixel[i][j]) # shape: (4,)
            drawn: np.ndarray = np.full(self.image_size, False)
            def _try_draw(m: int, n: int) -> None:
                if \
                    0 <= m < self.image_size[0] and \
                    0 <= n < self.image_size[1] and \
                    not drawn[m][n] and \
                    np.all(self.pixel[m][n] == base_color):

                    self.pixel[m][n] = np.concatenate([self.color, [255]])
                    self.update_pixel(m, n)
                    drawn[m][n] = True
                    _try_draw(m + 1, n)
                    _try_draw(m - 1, n)
                    _try_draw(m, n + 1)
                    _try_draw(m, n - 1)
            _try_draw(i, j)
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
        '''
        モード変更ボタンが押されたとき
        '''
        mode_prev = self.mode
        self.mode = self.NAME_TO_MODE[name]
        if mode_prev != self.Mode.PEN and self.mode == self.Mode.PEN:
            self.pen_button.config(image=self.pen_icon_active)
            self.fill_button.config(image=self.fill_icon)
        elif mode_prev != self.Mode.FILL and self.mode == self.Mode.FILL:
            self.pen_button.config(image=self.pen_icon)
            self.fill_button.config(image=self.fill_icon_active)

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
        '''
        画面上のピクセルを更新
        '''
        color_code: str = '#{:02x}{:02x}{:02x}'.format(*self.pixel[i][j][:3])
        coord: tuple = self.indices_to_coord(i, j)
        self.main_canvas.create_rectangle(
            coord[0],
            coord[1], 
            coord[0] + self.rect_size, 
            coord[1] + self.rect_size,
            fill=color_code, 
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
    def image_size(self) -> tuple[int, int]:
        return self.pixel.shape[:2]

    @property
    def rect_size(self) -> float:
        return min(self.width / self.image_size[0], (self.height - self.UPPER_SPACE) / self.image_size[1])

    def set_color(self, color: np.ndarray) -> None:
        self.color = color[:3]
        color_code: str = '#{:02x}{:02x}{:02x}'.format(*self.color)
        self.main_canvas.create_rectangle(
            120,
            20,
            150,
            50,
            fill=color_code,
            tags='current_color'
        )
        
if __name__ == '__main__':
    tk_root = tk.Tk()
    gui = GUI(tk_root)
    gui.mainloop()