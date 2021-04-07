#!/usr/bin/env python3

import tkinter as tk
from belltower import *
from tower_chooser import choose_tower
import time

FONT_NAME = "TkDefaultFont"
FONT_SIZE = 12

FONT = (FONT_NAME, FONT_SIZE)
TITLE_FONT = (FONT_NAME, int(FONT_SIZE * 1.5), "bold")

MAX_ROWS = 100
MAX_COLS = 100

COL_ERROR = "#e3867d"
COL_FG = "#000000"
COL_BG = "#ffffff"
COL_FADE = "#777777"
COL_DONE = "#7de39c"

BELL_NAMES = "1234567890ETABCD"


ASSIGN_DELAY = 0.2


class WrappingLabel(tk.Label):
    """ A type of Label that automatically adjusts the wrap to the size """

    def __init__(self, master=None, **kwargs):
        tk.Label.__init__(self, master, **kwargs)
        self.bind('<Configure>', lambda e: self.config(wraplength=self.winfo_reqwidth()))


def bell_name_from_num(num):
    """ Gets the bell name from a given 0-indexed number. """
    return BELL_NAMES[num]


def bell_num_from_name(name):
    """ Gets the bell name from a given 0-indexed number. """
    assert len(name) == 1
    if name.upper() in BELL_NAMES:
        return BELL_NAMES.index(name.upper())
    else:
        return None


class VLabel:
    """ A utility class that creates a label where the text goes upwards. """

    def __init__(self, parent, text, enabledness=True):
        self._parent = parent
        self._text = text

        # Create a canvas and a text element for the label
        self._canvas = tk.Canvas(self._parent, width=FONT_SIZE * 1.1, height=100)
        self._text_elem = self._canvas.create_text(
            0, 0,
            font=FONT,
            text=self._text,
            angle=90,
        )

        # Find out the size of the text, and make sure that the canvas encompasses the entire text
        # (therefore, layouting will do what we expect)
        x1, y1, x2, y2 = self._canvas.bbox(self._text_elem)
        self._canvas.move(self._text_elem, -x1, -y1)
        self._canvas.config(width=x2 - x1, height=y2 - y1)

        # Forward layout methods to the canvas widget
        self.pack = self._canvas.pack
        self.grid = self._canvas.grid

        # Set the enabledness
        self.set_enabledness(enabledness)

    def set_enabledness(self, enabledness: bool):
        self._canvas.itemconfig(
            self._text_elem,
            fill=COL_FG if enabledness else COL_FADE
        )


class User:
    """ A single user in the practice. """

    """
    The number of rows used up by the user name.  Used to put the touch in the right places on the
    screen.
    """
    ROWS = 2

    def __init__(self, parent, user_id, name):
        self._parent = parent
        self._user_id = user_id
        self._name = name

        self._in_room = True

        self._vlabel = VLabel(self._parent, self._name)

        # Forward layout methods to the canvas widget
        self.pack = self._vlabel.pack
        self.grid = self._vlabel.grid

    @property
    def is_in_room(self):
        return self._in_room

    @property
    def name(self):
        """ The name of this user. """
        return self._name

    def set_in_room(self, is_in_room):
        self._in_room = is_in_room
        self._vlabel.set_enabledness(is_in_room)


class Touch:
    """ A single touch in the practice. """

    """
    The number of columns used up by the touch input.  Used to put the user columns in the right
    places on the screen.
    """
    COLS = 7
    # Leave one column free for the move-touch arrows
    LEFT_MARGIN = 1

    """
    The possible sizes that a RR tower can have.  We need these as strings so that they can be fed
    into a tkinter OptionMenu.
    """
    SIZES = [str(x) for x in [4, 5, 6, 8, 10, 12, 14, 16]]

    """ The possible modes that Ringing Room can be in (towerbells or handbells) """
    TOWER = "Tower"
    HAND = "Hand"
    BELL_MODES = [TOWER, HAND]

    def __init__(self, matrix, parent, index, _id, touch_to_clone):
        self._parent = parent
        self._matrix = matrix
        self._index = index
        self._id = _id

        # The cells of the document
        self._cells = {}
        self._cell_vars = {}

        # ===== LHS ELEMENTS =====

        # A label for the number of the touch
        self._number = tk.Label(self._parent, text=str(self._index + 1))
        # A dropdown for the size of the tower
        self._size_var = tk.StringVar(
            self._parent,
            name=f"SizeVar {self._index + 1}",
            value="8" if touch_to_clone is None else touch_to_clone._size_var.get()
        )
        self._size_var.trace("w", self.update)
        self._size_menu = tk.OptionMenu(self._parent, self._size_var, *self.SIZES)
        # A switch between towerbells and handbells
        self._bellmode_var = tk.StringVar(
            self._parent,
            value=self.TOWER if touch_to_clone is None else touch_to_clone._bellmode_var.get()
        )
        self._bellmode_var.trace("w", self.update)
        self._bellmode_menu = tk.OptionMenu(self._parent, self._bellmode_var, *self.BELL_MODES)
        # A toggle for touches which have been rung
        self._done_var = tk.IntVar(self._parent, value=0)
        self._done_var.trace("w", self._update_doneness)
        self._done_toggle = tk.Checkbutton(self._parent, variable=self._done_var)
        # A button to load this touch into the room
        self._load_button = tk.Button(self._parent, text="Load", command=self._on_load)
        # An otherwise-useless textbox for the user to put the touch names
        self._name_box = tk.Entry(self._parent)

        # ===== RHS ELEMENTS =====

        self._bells_left = tk.Label(self._parent, text="<bells left label>")

        # Layout all the LHS elements
        self._pack_elems()

        # Explicitly call an update to make sure that the display is initialised properly
        self.update()

    def _pack_elems(self):
        self._number.grid       (row=self._row, column=self.LEFT_MARGIN + 0, padx=4)
        self._size_menu.grid    (row=self._row, column=self.LEFT_MARGIN + 1)
        self._bellmode_menu.grid(row=self._row, column=self.LEFT_MARGIN + 2)
        self._load_button.grid  (row=self._row, column=self.LEFT_MARGIN + 3)
        self._done_toggle.grid  (row=self._row, column=self.LEFT_MARGIN + 4)
        self._name_box.grid     (row=self._row, column=self.LEFT_MARGIN + 5, padx=20)
        for _u_id, (i, c) in self._cells.items():
            c.grid(row=self._row, column=self.COLS + i)
        self._bells_left.grid(row=self._row, column=MAX_COLS, sticky="w", padx=(10, 4))

    def add_user(self, user_id, user):
        """ Adds a user to this touch as a new column. """
        cell_var = tk.StringVar(self._parent, value="")
        cell_var.trace_add("write", self.update)

        cell = tk.Entry(self._parent, width=2, textvariable=cell_var)
        cell.grid(row=self._row, column=self.COLS + len(self._cells))

        self._cell_vars[user_id] = cell_var
        self._cells[user_id] = (len(self._cells), cell)

    def _assignments_and_errors(self):
        """
        Returns a tuple of:
        - A mapping between bells and user IDs
        - A set of which user IDs have errors in their cells.
        """
        size = int(self._size_var.get())

        # The set of cells which contain errors.  These cells will be highlighted red
        cells_with_errors = set()

        # Figure out which bells are assigned to whom
        # assigned_users maps 0-indexed **bells** to **user_ids*
        assigned_users = {}
        for user_id, v in self._cell_vars.items():
            for c in v.get():
                bell = bell_num_from_name(c)
                # If the name was invalid or the bell is out of range, mark this cell as having
                # errors and continue
                if bell is None or bell < 0 or bell >= size:
                    cells_with_errors.add(user_id)
                    continue
                # If bells are assigned to a user who's left the tower, then that's also an error
                if not self._matrix.is_user_in_room(user_id):
                    cells_with_errors.add(user_id)
                    continue
                # Assign the bell to this user (but store existing assignments to show errors)
                if bell in assigned_users:
                    assigned_users[bell].append(user_id)
                else:
                    assigned_users[bell] = [user_id]

        return (assigned_users, cells_with_errors)

    def update(self, *args):
        size = int(self._size_var.get())

        assigned_users, cells_with_errors = self._assignments_and_errors()

        # Mark duplicate assignments as errors
        for b in assigned_users:
            users = assigned_users[b]
            if len(users) > 1:
                for u in users:
                    cells_with_errors.add(u)

        # Update the cell highlighting and the enabledness of the button
        for i, (_index, c) in self._cells.items():
            c['background'] = COL_ERROR if i in cells_with_errors else COL_BG
        self._load_button['state'] = tk.NORMAL if len(cells_with_errors) == 0 else tk.DISABLED

        # Find which bells are unassigned, and update the readout
        unassigned_bells = [b for b in range(size) if b not in assigned_users]
        if len(unassigned_bells) == 0:
            text = ''
        else:
            text = ','.join([bell_name_from_num(b) for b in unassigned_bells]) + " left"
        self._bells_left['text'] = text

    def _update_doneness(self, *args):
        self._name_box.config(bg=COL_DONE if self._done_var.get() == 1 else COL_BG)

    def set_index(self, new_index):
        self._index = new_index
        self._number.config(text=str(self._index + 1))
        self._pack_elems()

    @property
    def _row(self):
        """ Gets the row that this touch should occupy in the grid. """
        return User.ROWS + self._index

    @classmethod
    def create_headings(cls, parent):
        headers = [
            tk.Label(parent, text=i, font=(FONT_NAME, FONT_SIZE, "bold"))
            for i in ["Bells", "Mode", "", "Done", "Touch notes"]
        ]
        for i, h in enumerate(headers):
            h.grid(row=User.ROWS - 1, column=Touch.LEFT_MARGIN + 1 + i, sticky="S")
        return headers

    def _on_load(self):
        print(f"Loading #{self._index + 1}: '{self._name_box.get()}'")
        # If we load a touch, then automatically flag it as done
        self._done_var.set(1)
        # ===== READ ALL THE REQUIRED VALUES =====
        assigned_users, _cells_with_errors = self._assignments_and_errors()
        new_size = int(self._size_var.get())
        # Convert the bell type string into a BellType value
        bell_type_str = self._bellmode_var.get()
        if bell_type_str == "Tower":
            bell_type = TOWER_BELLS
        else:
            assert bell_type_str == "Hand"
            bell_type = HAND_BELLS

        # ===== UPDATE RINGING ROOM =====
        # Reassign all bells if we're changing the touch
        should_unassign_all = (self._id != self._matrix.last_assigned_touch_id)
        self._matrix.last_assigned_touch_id = self._id
        print(should_unassign_all)
        # Set tower size and setting
        tower = self._matrix.tower
        tower.set_at_hand()
        tower.set_size(new_size)
        tower.set_bell_type(bell_type)
        # Unassign all if needed
        if should_unassign_all:
            tower.unassign_all()
        # Assign users
        for i in range(new_size):
            bell = Bell.from_index(i)
            user_ids = assigned_users.get(i)
            if user_ids:
                # Only re-assign the bell if needed
                user_id = user_ids[0]
                # Only assign bells if change is required (in the case of unassigning all, we force
                # through this change, in case the Tower's internal state hasn't updated)
                if should_unassign_all or user_id != tower.get_assignment(bell):
                    time.sleep(ASSIGN_DELAY)
                    tower.assign(user_id, bell)
            else:
                # If the bell should be unassigned, then unassign it only if currently assigned
                if not should_unassign_all and tower.get_assignment(bell) is not None:
                    time.sleep(ASSIGN_DELAY)
                    tower.unassign(bell)


class Matrix:
    """ The matrix between touches (left) and ringers (top) """

    def __init__(self, parent, tower):
        # ===== INITIALISATION =====
        self._parent = parent
        self._panel = tk.Frame(self._parent)

        # Users is a mapping between user ids (`int`s) and the User objects
        self._users = {}
        self._touches = []
        self._next_touch_id = 0
        self.last_assigned_touch_id = None

        # Forward layout methods to the panel
        self.pack = self._panel.pack
        self.grid = self._panel.grid

        # ===== HANDLE RR CALLBACKS =====
        self.tower = tower
        self.tower.on_user_enter(self._on_user_enter)
        self.tower.on_user_leave(self._on_user_leave)

        # Make sure that all the existing users appear in the list
        for user_id, user_name in self.tower.all_users.items():
            self._on_user_enter(user_id, user_name)

        # ===== TOP-LEFT CORNER BOX =====
        self._help_box = tk.Frame(self._panel)
        self._help_box.grid(
            row=0,
            column=0,
            rowspan=User.ROWS - 1,
            columnspan=Touch.COLS,
            sticky="NESW"
        )

        self._title = tk.Label(
            self._help_box,
            text="Minor General",
            font=TITLE_FONT
        )
        self._title.pack(pady=(5, 0))

        self._desc = tk.Label(
            self._help_box,
            text="Run extremely efficient Ringing Room practices.",
            font=(FONT_NAME, FONT_SIZE, 'italic')
        )
        self._desc.pack()

        self._tower_label = tk.Label(
            self._help_box,
            text=f"Tower #{self.tower.tower_id}: {self.tower.tower_name}",
            font=(FONT_NAME, FONT_SIZE)
        )
        self._tower_label.pack()

        self._help_block = tk.Frame(self._help_box)
        self._help_block.pack(expand=True, fill=tk.X, pady=7, padx=5)

        # Generate the lines of the help box
        help_lines = [
            "'+' creates a new touch",
            "Give people bells by typing bell names into box",
            "The bell names for 1-16 are 1234567890ETABCD",
            "Write two bell names to assign to two bells",
            "If a bell is assigned to two ringers then the cells go red",
            "If an invalid bell name is entered the cell goes red",
            "Press 'Load' to load that touch to Ringing Room"
        ]
        self._help_labels = []
        for l in help_lines:
            label = WrappingLabel(
                self._help_block,
                text='- ' + l,
                font=(FONT_NAME, int(FONT_SIZE * .75)),
                anchor="w"
            )
            label.pack(expand=True, fill=tk.X)
            self._help_labels.append(label)

        # ===== INITIALISE THE TABLE =====

        # Always start with one touch, and generate the headings for the columns
        self._headers = Touch.create_headings(self._panel)
        self._add_touch()

        # An array to store the buttons to swap touches
        self._swap_buttons = []
        # Create the plus button
        self._plus_button = tk.Button(
            self._panel,
            text='+',
            font=FONT,
            command=self._add_touch
        )
        self._plus_button.grid(row=MAX_ROWS, column=0, columnspan=MAX_COLS + 1)

    def is_user_in_room(self, user_id):
        if user_id in self._users:
            return self._users[user_id].is_in_room

    def _on_user_enter(self, user_id, user_name):
        if user_id in self._users:
            self._users[user_id].set_in_room(True)
            # Update all the touches when a user returns to the tower
            for t in self._touches:
                t.update()
        else:
            self._add_user(user_id, user_name)

    def _on_user_leave(self, user_id, user_name):
        self._users[user_id].set_in_room(False)
        # Update all the touches when a user leaves the tower
        for t in self._touches:
            t.update()

    def _add_touch(self):
        """ Adds another row to the touch list. """
        # If this isn't the first touch, then create a new swap button
        num_touches = len(self._touches)
        if num_touches > 0:
            new_swap_button = tk.Button(
                self._panel,
                text="^",
                font=FONT,
                command=lambda: self._swap_touches(num_touches - 1)
            )
            new_swap_button.grid(row=User.ROWS + num_touches, column=0)
            self._swap_buttons.append(new_swap_button)

        # Generate a new ID for this touch
        new_id = self._next_touch_id
        self._next_touch_id += 1
        # Add a new touch
        touch_to_clone = self._touches[-1] if self._touches != [] else None
        new_touch = Touch(self, self._panel, num_touches, new_id, touch_to_clone)
        # Add all the existing users to the touch row
        for u_id, user in self._users.items():
            new_touch.add_user(u_id, user)
        # Add touch to list
        self._touches.append(new_touch)

    def _swap_touches(self, i):
        # Swap touches
        self._touches[i], self._touches[i + 1] = self._touches[i + 1], self._touches[i]
        # Update indices
        self._touches[i].set_index(i)
        self._touches[i + 1].set_index(i + 1)

    def _add_user(self, user_id, user_name):
        """
        Add a user to the practice.  This will be called as a callback for a user entering the
        practice.
        """
        user = User(self._panel, user_id, user_name)
        user.grid(
            row=0,
            column=Touch.COLS + len(self._users),
            rowspan=User.ROWS,
            sticky="S",
            padx=2,
            pady=(4, 2),
        )
        self._users[user_id] = user

        # Add this user to all the touches
        for t in self._touches:
            t.add_user(user_id, user)


def main():
    tower = choose_tower("Minor General", FONT, TITLE_FONT)
    if tower is None:
        return -1

    print("Connecting to tower...")
    with tower:
        tower.wait_loaded()

        print("Connected!")

        window = tk.Tk()
        window.title("Minor General")

        matrix = Matrix(window, tower)
        matrix.pack()

        window.mainloop()


if __name__ == "__main__":
    main()
