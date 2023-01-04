from kivy.config import Config
Config.set('graphics', 'width', '900')
Config.set('graphics', 'height', '400')
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, StringProperty, Clock, ObjectProperty
from kivy.graphics.context_instructions import Color
from kivy.graphics.vertex_instructions import Line, Rectangle, Quad, Triangle 
from kivy.core.window import Window
from kivy import platform
import random
from kivy.lang import Builder
from kivy.uix.relativelayout import RelativeLayout
from kivy.core.audio import SoundLoader

Builder.load_file("menu.kv")

class MainWidget(RelativeLayout):
    from transforms import transform, transform_2D, transform_perspective
    from user_actions import keyboard_closed, on_keyboard_down, on_keyboard_up, on_touch_down, on_touch_up
    perspective_point_x = NumericProperty(0)
    perspective_point_y = NumericProperty(0)
    vertical_lines = []
    V_NB_LINES = 8 
    V_LINES_SPACING = .4 #percentage of screen width

    horizontal_lines = []
    H_NB_LINES = 15
    H_LINES_SPACING = .1 #percentage of screen height

    speed = 0   
    speed_x = 3
    current_speed_x = 0
    current_offset_x = 0
    current_offset_y = 0
    current_y_loop = 0

    NB_TILES = 16
    tiles = []
    tiles_coordinates = []
    
    ship_width = .1
    ship_height = 0.035
    ship_base_y = 0.04
    ship = None
    ship_coordinates = [(0,0), (0,0), (0,0)]

    state_game_over= False
    state_game_started = False
    menu_widget = ObjectProperty()

    menu_title = StringProperty("G   A   L   A   X   Y")
    menu_button_title = StringProperty("START")

    score = "Score: 0"
    score_label = StringProperty("Score: " + score)
    difficulty_selected = StringProperty("Difficulty Selected: None")

    begin_sound = None
    galaxy_sound = None
    impact_sound = None
    gameover_voice_sound = None
    music1_sound = None
    restart_sound = None

    def __init__(self, **kwargs):
        super(MainWidget, self).__init__(**kwargs)
        self.init_vertical_lines()
        self.init_horizontal_lines()
        self.init_tiles()
        self.reset_game()
        self.init_ship()
        self.init_audio()
        
        if self.is_desktop():
            self._keyboard = Window.request_keyboard(self.keyboard_closed, self)
            self._keyboard.bind(on_key_down=self.on_keyboard_down)
            self._keyboard.bind(on_key_up=self.on_keyboard_up)
        
        Clock.schedule_interval(self.update, 1/60)
        self.galaxy_sound.play()

    def init_audio(self):
        self.begin_sound = SoundLoader.load("audio/begin.wav")
        self.galaxy_sound = SoundLoader.load("audio/galaxy.wav")
        self.impact_sound = SoundLoader.load("audio/gameover_impact.wav")
        self.gameover_voice_sound = SoundLoader.load("audio/gameover_voice.wav")
        self.music1_sound = SoundLoader.load("audio/music1.wav")
        self.restart_sound = SoundLoader.load("audio/restart.wav")

        self.begin_sound.volume = .25
        self.galaxy_sound.volume = .25
        self.impact_sound.volume = .25
        self.gameover_voice_sound.volume = .25 
        self.music1_sound.volume = 1
        self.restart_sound.volume = .25
        

    def reset_game(self):
        self.current_offset_y = 0
        self.current_y_loop = 0
        self.current_speed_x = 0
        self.current_offset_x = 0

        self.tiles_coordinates = []
        self.pre_fill_tiles_coordinates()
        self.generate_tile_coordinates()
        
        self.state_game_over = False

    def is_desktop(self):
        if platform in ('linux', 'win', 'macosx'):
            return True
        return False

    def init_tiles(self):
        with self.canvas:
            Color(1, 1, 1)
            for i in range(0, self.NB_TILES):
                self.tiles.append(Quad())
    
    def init_ship(self):
        with self.canvas:
            Color(0, 0, 0)
            self.ship = Triangle()
    
    def update_ship(self):
        center_x = self.width/2
        base_y = self.ship_base_y * self.height
        ship_width = self.ship_width * self.width
        ship_height = self.ship_height * self.height
        self.ship_coordinates[0] = (center_x-ship_width/2, base_y)
        self.ship_coordinates[1] = (center_x, base_y + ship_height)
        self.ship_coordinates[2] = (center_x+ship_width/2, base_y)
        # print("0= ", self.ship_coordinates[0])
        # print("1= ", self.ship_coordinates[1])
        # print("2= ", self.ship_coordinates[2])
        #    2
        # 1     3
        x1, y1 = self.transform(*self.ship_coordinates[0])
        x2, y2 = self.transform(*self.ship_coordinates[1])
        x3, y3 = self.transform(*self.ship_coordinates[2])
        #self.ship_coordinates is a tuple, but self.transform takes two arguments. Putting
        # the asterisk before the touple in the function call "expands" the tuple, allowing
        # all of the inner arguments to be used in the function. 

        self.ship.points = [x1, y1, x2, y2, x3, y3]

    def check_ship_collision(self):
        for i in range(0, len(self.tiles_coordinates)):
            ti_x, ti_y = self.tiles_coordinates[i]
            if ti_y > self.current_y_loop + 1:
                return False
            if self.check_ship_collision_with_tile(ti_x, ti_y):
                return True
        return False

    def check_ship_collision_with_tile(self, ti_x, ti_y):
        xmin, ymin = self.get_tile_coordinates(ti_x, ti_y)
        xmax, ymax = self.get_tile_coordinates(ti_x+1, ti_y+1)
        for i in range(0, 3):
            px, py = self.ship_coordinates[i]
            if xmin <= px <= xmax and ymin <= py <= ymax:
                return True
        return False

    def pre_fill_tiles_coordinates(self):
        for i in range(0,10):
            self.tiles_coordinates.append((0,i))
            
    def generate_tile_coordinates(self):
        last_y = 0
        last_x = 0

        start_index = -int(self.V_NB_LINES / 2) + 1
        end_index = start_index + self.V_NB_LINES - 1
        x_min = self.get_line_x_from_index(start_index)
        x_max = self.get_line_x_from_index(end_index)
        #print("xmax= ", str(x_max))
        #clearing the coordinates of the tiles that have left the screen:
        for i in range(len(self.tiles_coordinates)-1, -1, -1):
            if self.tiles_coordinates[i][1] < self.current_y_loop:
                del self.tiles_coordinates[i]

        if len(self.tiles_coordinates) > 0:
            last_coordinates = self.tiles_coordinates[-1]
            last_y = last_coordinates[1] + 1
            last_x = last_coordinates[0]
            # print("last coor = ", str(last_coordinates))
        
        for i in range(len(self.tiles_coordinates), self.NB_TILES):
            r = random.randint(0,2)
            self.tiles_coordinates.append((last_x, last_y))
            # For r: 
            # 0 -> straight
            # 1 -> right
            # 2 -> left
            # if r == 0:
            #     self.tiles_coordinates.append((last_x, last_y))
            # print("last x = ", str(last_x))
            # print("xmax= ", str(x_max), "xmin= ", str(x_min))
            right_bound = self.get_line_x_from_index(last_x+1)
            left_bound = self.get_line_x_from_index(last_x)
            if right_bound >= x_max:
                r = 2
            if left_bound <= x_min:
                r = 1

            if r == 1:
                last_x+=1
                self.tiles_coordinates.append((last_x, last_y))
                last_y+=1
                self.tiles_coordinates.append((last_x, last_y))
            elif r == 2:
                last_x-=1
                self.tiles_coordinates.append((last_x, last_y))
                last_y+=1
                self.tiles_coordinates.append((last_x, last_y))

            last_y += 1

    def init_vertical_lines(self):
        with self.canvas:
            Color(1, 1, 1)
            v_line_height = int(self.height * .75)
            for i in range(0, self.V_NB_LINES):
                self.vertical_lines.append(Line())

    def init_horizontal_lines(self):
        with self.canvas:
            Color(1, 1, 1)
            for i in range(0, self.H_NB_LINES):
                self.horizontal_lines.append(Line())
        

    def get_line_x_from_index(self, index):
        central_line_x = self.perspective_point_x
        spacing = self.V_LINES_SPACING * self.width
        offset = index - 0.5
        line_x = central_line_x + offset*spacing + self.current_offset_x
        #print("line_x= ", str(line_x))
        return line_x

    def get_line_y_from_index(self, index):
        spacing = self.H_LINES_SPACING * self.height
        line_y = index * spacing - self.current_offset_y
        return line_y
    
    def get_tile_coordinates(self, ti_x, ti_y):
        ti_y = ti_y - self.current_y_loop #
        x = self.get_line_x_from_index(ti_x)
        y = self.get_line_y_from_index(ti_y)
        return x, y

    def update_vertical_lines(self):
        #coordinates for vertical lines:
        #-1 0 1 2
        start_index = -int(self.V_NB_LINES/2) + 1
        for i in range(start_index, start_index + self.V_NB_LINES):
            x_coor = self.get_line_x_from_index(i)
            x1, y1 = self.transform(x_coor, 0)
            x2, y2 = self.transform(x_coor, self.height)
            self.vertical_lines[i].points = (x1, y1, x2, y2)

    def update_horizontal_lines(self):
        start_index = -int(self.V_NB_LINES / 2) + 1
        end_index = start_index + self.V_NB_LINES - 1

        x_min = self.get_line_x_from_index(start_index)
        x_max = self.get_line_x_from_index(end_index)

        for i in range(0, self.H_NB_LINES):
            line_y = self.get_line_y_from_index(i)
            x1, y1 = self.transform(x_min, line_y)
            x2, y2 = self.transform(x_max, line_y)
            self.horizontal_lines[i].points = (x1, y1, x2, y2)

        # center_x = int(self.width/2)
        # spacing_x = self.V_LINES_SPACING * self.width

        # if self.V_NB_LINES % 2 == 0:
        #     offset_min = int(self.V_NB_LINES/2) - 0.5
        #     offset_max = int(self.V_NB_LINES/2) - 0.5
        # else:
        #     offset_min = int(self.V_NB_LINES/2) - 0.5
        #     offset_max = int(self.V_NB_LINES/2) + 0.5
      
        # x_min = center_x - offset_min * spacing_x + self.current_offset_x
        # x_max = center_x + offset_max * spacing_x + self.current_offset_x
        # spacing_y = self.H_LINES_SPACING*self.height

        # for i in range(0, self.H_NB_LINES):
        #     line_y = i * spacing_y - self.current_offset_y
        #     x1, y1 = self.transform(x_min, line_y)
        #     x2, y2 = self.transform(x_max, line_y)
        #     self.horizontal_lines[i].points = (x1, y1, x2, y2)
    
    def update_tiles(self):
        for i in range(0, self.NB_TILES):
            tile = self.tiles[i]
            tile_coordinates = self.tiles_coordinates[i]
            xmin, ymin = self.get_tile_coordinates(tile_coordinates[0], tile_coordinates[1])
            xmax, ymax = self.get_tile_coordinates(tile_coordinates[0]+1, tile_coordinates[1]+1)

            # 2     3
            #
            # 1     4
            x1, y1 = self.transform(xmin, ymin)
            x2, y2 = self.transform(xmin, ymax)
            x3, y3 = self.transform(xmax, ymax)
            x4, y4 = self.transform(xmax, ymin)

            tile.points = [x1, y1, x2, y2, x3, y3, x4, y4]

    def update_score(self):
        self.score = str(self.current_y_loop)
        self.score_label = "Score: " + self.score

    def update(self, dt):
        self.update_horizontal_lines()
        self.update_vertical_lines()
        self.update_tiles()
        self.update_ship()
        self.update_score()
        #self.current_offset_x += self.speed_x
        time_factor = dt * 60

        if not self.state_game_over and self.state_game_started:
            game_speed = (self.speed * self.height) / 100
            self.current_offset_y += game_speed * time_factor
            spacing_y = self.H_LINES_SPACING*self.height

            while self.current_offset_y >= spacing_y:
                self.current_offset_y -= spacing_y
                self.current_y_loop += 1
                self.generate_tile_coordinates()

            self.current_offset_x += self.current_speed_x * time_factor

        if not self.check_ship_collision() and not self.state_game_over:
            self.state_game_over = True
            self.speed = 0
            self.difficulty_selected = "Difficulty Selected: None"
            self.menu_widget.opacity = 1 
            self.music1_sound.stop()
            self.impact_sound.play()
            self.gameover_voice_sound.play()
            print("GAME OVER")
    
    def easy_difficulty_selected(self):
        self.speed = 0.5
        self.difficulty_selected = "Difficulty Selected: Easy"

    def medium_difficulty_selected(self):
        self.speed = .8
        self.difficulty_selected = "Difficulty Selected: Medium"

    def hard_difficulty_selected(self):
        self.speed = 1.1
        self.difficulty_selected = "Difficulty Selected: Hard"
    
    def insane_difficulty_selected(self):
        self.speed = 1.5
        self.speed_x = 4
        self.difficulty_selected = "Difficulty Selected: Insane"

    def on_menu_button_pressed(self):
        if self.speed != 0:
            if self.state_game_over:
                self.restart_sound.play()
            else:
                self.begin_sound.play()
            self.music1_sound.play()
            self.reset_game()
            self.state_game_started = True
            self.menu_title = "GAME OVER"
            self.menu_button_title = "RESTART" 
            self.menu_widget.opacity = 0
        else:
            self.difficulty_selected = "Please Select a Difficulty Setting"
        
        

class GalaxyApp(App):
    pass

GalaxyApp().run()
    