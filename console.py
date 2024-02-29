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
            Message("Each of the buildings in this lightly wooded area contain computer terminals.", 0),
            Message("On one of those terminals is your objective!", 0),
            Message("The rest contain maps and intel on the patrol routes of the base's guards.", 0),
            Message("Good luck!", 0),
            Message("(press '?' for help info)", 0),
        ]
        self.scrolled_up_by = 0
        self.lines = lines
        self.pushed_controls_last = False

    def push_controls(self):
        if not self.pushed_controls_last:
            self.messages.extend([
                Message("___Controls___", 0),
                Message("Use the mouse to move around. 4 TU to move (x2 diagonal cost).", 0),
                Message("Use the WASD keys to move the camera, or middle-mouse-click, or click on the mini-map.", 0),
                Message("Also, press 'c' to reset the camera to the player's position.", 0),
                Message("right-click on tile adjacent to player to change facing for 1 TU.", 0),
                Message("Use the '[' or ']' keys, or mousewheel, to scroll the console.", 0),
                Message("Press the HOME key to reset the console scroll.", 0),
                Message("You can end turn by clicking the 'End Turn' button or by pressing 'e'.", 0),
                Message("___TIPS___", 0),
                Message("'!' above a baddie's head indicates they can see the player, and may call for backup!", 0),
                Message("'?' above a baddie's head indicates that they are investigating and suspicious.", 0),
                Message("'$' overlayed on top of an object indicates that it can be interacted with.", 0),
                Message("* For now, the player has both a higher TU and a higher vision range than baddies.", 0),
                Message("  Use this to your advantage! Combat for the player will be implemented in the next", 0),
                Message("  version.", 0),
            ])
            self.pushed_controls_last = True

    def push(self, msg):
        self.messages.append(msg) 
        self.pushed_controls_last = False

    def scroll(self, updown):
        if self.scrolled_up_by > 0 and updown == "down":
            self.scrolled_up_by -= 1
        elif len(self.messages) - (self.scrolled_up_by + 1) <= len(self.messages) and updown == "up":
            self.scrolled_up_by += 1

    def reset(self):
        self.scrolled_up_by = 0

