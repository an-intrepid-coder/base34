from constants import *

class Message:
    def __init__(self, msg, turn, tag=None):
        self.msg = msg
        self.tag = tag
        self.turn = turn

class Console: 
    def __init__(self, lines):
        self.messages = [
            Message("You have arrived at the outskirts of Base 34. Somewhere within is a terminal that", 0),
            Message("contains the information you need to find the base's entrance. You are unarmed, and must", 0),
            Message("rely on whatever gear you find. You can't take the weapons the guards carry, because they are", 0),
            Message("gene-locked to their holders. But there are sure to be weapons, ammo, and more available.", 0),
            Message("But first, you must gain access to the buildings in the area. The guards carry keycards.", 0),
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
                Message("* Use the mouse to move around. 4 TU to move (x2 diagonal cost).", 0),
                Message("* Use the WASD keys to move the camera, or middle-mouse-click, or click on the mini-map.", 0),
                Message("* Press 'c' to reset the camera to the player's position.", 0),
                Message("* Right-click change facing for 1 TU.", 0),
                Message("* Use the '[' or ']' keys, or mousewheel, to scroll the console.", 0),
                Message("* Press the HOME key to reset the console scroll.", 0),
                Message("* You can end turn by clicking the 'End Turn' button or by pressing 'e'.", 0),
                Message("___TIPS___", 0),
                Message("* '!' above a baddie's head indicates they can see the player, and may call for backup!", 0),
                Message("* '?' above a baddie's head indicates that they are investigating and suspicious.", 0),
                Message("* 'zzz' above a baddie's head indicates that they are KO'd.", 0),
                Message("* '$' overlayed on top of an object indicates that it can be interacted with.", 0),
                Message("* KO melee attacks cost {} TU and can be performed with shift-click.".format(TU_MELEE), 0),
                Message("* Lethal melee or ranged attacks cost {} TU and can be performed with ctrl-click".format(TU_LETHAL), 0),
                Message("* KO'd enemies can be killed with a coup de grace.", 0),
                Message("* Reloading costs {} TU and can be performed by ctrl+click on the item in the inventory.".format(TU_RELOAD), 0),
                Message("* Equip/Unequip costs {} TU. Do so by clicking on item in the inventory.".format(TU_EQUIP), 0),
                Message("* Throwing a throwable object costs {} TU, and is done by clicking the item in the inventory.".format(TU_THROW), 0),
                Message("* Stims cost no TU to use. Use them by clicking on them in the inventory.", 0),
                Message("* Keycards are dropped by baddies, sometimes. You need them to get through doors.", 0),
                Message("* If you KO/kill a baddie in a doorway, you can walk right through!.", 0),
                Message("* Alerts can be caused by lots of things: being spotted and your position called in;", 0),
                Message("  a KO'd baddie waking up; a dead baddie being discovered; the use of firearms or", 0),
                Message("  frag grenades.", 0),
                Message("* The baddies will slowly arm themselves with rifles every time there is an alert. ", 0),
                Message("  However, if gunshots/explosions are heard, or a dead body discovered, they will arm", 0),
                Message("  themselves much more quickly.", 0),
                Message("* If you die and choose to try again, the map layout will remain the same but all Baddies", 0),
                Message("  and loot will be re-generated.", 0),
                Message("* If you can see it, you can shoot it. But different weapons have different ammo capacities.", 0),
                Message("* Ammo is scarce. If you want to shoot your way out of a situation, then save up first.", 0),
                Message("* Terminals will give you a small map, and permanent tracking data on a number of baddies.", 0),
                Message("* 'Frag' Grenades can destroy walls. Use this to your advantage, if you find any!", 0),
                Message("* Body Armor will stop exactly one shot, and then needs to be replaced.", 0),
                Message("* It only takes one shot to kill you. Or one successful melee attack to KO you.", 0),
                Message("  But enemies sometimes miss, while you always hit what you see.", 0),
                Message("* The player has both a higher TU and a higher vision range than baddies.", 0),
                Message("  Use this to your advantage!", 0),
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

