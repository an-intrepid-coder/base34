class Message:
    def __init__(self, msg, turn, tag=None):
        self.msg = msg
        self.tag = tag
        self.turn = turn

class Console: 
    def __init__(self, lines):
        self.messages = [
            Message("Welcome to Base 34. A Tactical Espionage Roguelike in the making.", 0),
            Message("Eventually this will be a game! For now it's a testing ground. Enjoy!", 0),
            Message("Use the mouse to move around. 4 TU to move (x2 diagonal cost).", 0),
            Message("Use the WASD keys to move the camera, or middle-mouse-click.", 0),
            Message("shift + left-click on tile adjacent to player to change facing for 1 TU.", 0),
            Message("Use the '[' or ']' keys, or mousewheel, to scroll the console.", 0),
            Message("Press the HOME key to reset the console scroll.", 0),
        ]
        self.scrolled_up_by = 0
        self.lines = lines

    def push(self, msg):
        self.messages.append(msg) 

    def scroll(self, updown):
        if self.scrolled_up_by > 0 and updown == "down":
            self.scrolled_up_by -= 1
        elif len(self.messages) - (self.scrolled_up_by + 1) <= len(self.messages) and updown == "up":
            self.scrolled_up_by += 1

    def reset(self):
        self.scrolled_up_by = 0

