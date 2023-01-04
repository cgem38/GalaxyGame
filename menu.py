from kivy.uix.relativelayout import RelativeLayout



class MenuWidget(RelativeLayout):
    def on_touch_down(self, touch):
        if self.opacity == 0:
            return False
        return super().on_touch_down(touch)
    #This function disables the Start Game button while the game is running. When the game
    #is started, the menu disappears by turning its opacity to 0, but it is still on the 
    #screen and could be interacted with while playing. This function disallows that. 
    

