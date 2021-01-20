#!/usr/bin/env python3

import tkinter as tk

FONT_NAME = "TkDefaultFont"
FONT_SIZE = 12
FONT = (FONT_NAME, FONT_SIZE)


MAX_ROWS = 100
MAX_COLS = 100


BELL_NAMES = "1234567890ETABCD"


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
    if name in BELL_NAMES:
        return BELL_NAMES.index(name.upper())
    else:
        return None


class VLabel:
    """ A utility class that creates a label where the text goes upwards. """

    def __init__(self, parent, text):
        self._parent = parent
        self._text = text

        # Create a canvas and a text element for the label
        self._canvas = tk.Canvas(self._parent, width=FONT_SIZE * 1.1, height=100)
        self._text_elem = self._canvas.create_text(0, 0, font=FONT, text=self._text, angle=90)

        # Find out the size of the text, and make sure that the canvas encompasses the entire text
        # (therefore, layouting will do what we expect)
        x1, y1, x2, y2 = self._canvas.bbox(self._text_elem)
        self._canvas.move(self._text_elem, -x1, -y1)
        self._canvas.config(width=x2 - x1, height=y2 - y1)
        
        # Forward layout methods to the canvas widget
        self.pack = self._canvas.pack
        self.grid = self._canvas.grid


class User:
    """ A single user in the practice. """

    """
    The number of rows used up by the user name.  Used to put the touch in the right places on the
    screen.
    """
    ROWS = 2


    def __init__(self, parent, name):
        self._parent = parent
        self._name = name

        self._vlabel = VLabel(self._parent, self._name)
        
        # Forward layout methods to the canvas widget
        self.pack = self._vlabel.pack
        self.grid = self._vlabel.grid

    @property
    def name(self):
        """ The name of this user. """
        return self._name

class Touch:
    """ A single touch in the practice. """

    """
    The number of columns used up by the touch input.  Used to put the user columns in the right
    places on the screen.
    """
    COLS = 5

    """
    The possible sizes that a RR tower can have.  We need these as strings so that they can be fed
    into a tkinter OptionMenu.
    """
    SIZES = [str(x) for x in [4, 5, 6, 8, 10, 12, 14, 16]]

    """ The possible modes that Ringing Room can be in (towerbells or handbells) """
    TOWER = "Tower"
    HAND = "Hand"
    BELL_MODES = [TOWER, HAND]

    def __init__(self, parent, index):
        self._parent = parent
        self._index = index

        # The cells of the document
        self._cells = []
        self._cell_vars = []

        # ===== LHS ELEMENTS =====

        # A label for the number of the touch
        self._number = tk.Label(self._parent, text=str(self._index + 1))
        # A dropdown for the size of the tower
        self._size_var = tk.StringVar(self._parent, name=f"SizeVar {self._index + 1}", value="8")
        self._size_var.trace("w", self._update)
        self._size_menu = tk.OptionMenu(self._parent, self._size_var, *self.SIZES)
        # A switch between towerbells and handbells
        self._bellmode_var = tk.StringVar(self._parent, value=self.TOWER)
        self._bellmode_var.trace("w", self._update)
        self._bellmode_menu = tk.OptionMenu(self._parent, self._bellmode_var, *self.BELL_MODES)
        # A button to load this touch into the room
        self._load_button = tk.Button(self._parent, text="Load", command=self._on_load)
        # An otherwise-useless textbox for the user to put the touch names
        self._name_box = tk.Entry(self._parent)

        # Layout all the LHS elements
        self._number.grid(row = self._row, column = 0, padx = 4)
        self._size_menu.grid(row = self._row, column = 1)
        self._bellmode_menu.grid(row = self._row, column = 2)
        self._load_button.grid(row = self._row, column = 3)
        self._name_box.grid(row = self._row, column = 4, padx = 20)

        # ===== RHS ELEMENTS =====

        self._bells_left = tk.Label(self._parent, text="<bells left label>")
        self._bells_left.grid(row = self._row, column = MAX_COLS, sticky = "w", padx = (10, 4))

        # Explicitly call an update to make sure that the display is initialised properly
        self._update()

    def add_user(self, user):
        """ Adds a user to this touch as a new column. """
        cell_var = tk.StringVar(self._parent, value="")
        cell_var.trace_add("write", self._update)

        cell = tk.Entry(self._parent, width = 2, textvariable=cell_var)
        cell.grid(row = self._row, column = self.COLS + len(self._cells))

        self._cell_vars.append(cell_var)
        self._cells.append(cell)

    def _update(self, *args):
        # Read the size
        size = int(self._size_var.get())

        # The set of cells which contain errors.  These cells will be highlighted red
        cells_with_errors = set()

        # Figure out which bells are assigned to whom
        # assigned_users maps **bells** to **users** (both of which are 0-indexed integers)
        assigned_users = {}
        for i, v in enumerate(self._cell_vars):
            for c in v.get():
                bell = bell_num_from_name(c)
                # If the name was invalid or the bell is out of range, mark this cell as having
                # errors and continue
                if bell is None or bell < 0 or bell >= size:
                    cells_with_errors.add(i)
                    continue
                # Assign the bell to this user (but store existing assignments to show errors)
                if bell in assigned_users:
                    assigned_users[bell].append(i)
                else:
                    assigned_users[bell] = [i]

        # Mark duplicate assignments as errors
        for b in assigned_users:
            users = assigned_users[b]
            if len(users) > 1:
                for u in users:
                    cells_with_errors.add(u)

        # Update the cell highlighting and the enabledness of the button
        for i, c in enumerate(self._cells):
            c['background'] = 'red' if i in cells_with_errors else 'white'
        self._load_button['state'] = tk.NORMAL if len(cells_with_errors) == 0 else tk.DISABLED
        
        # Find which bells are unassigned, and update the readout
        unassigned_bells = [b for b in range(size) if b not in assigned_users]
        if len(unassigned_bells) == 0:
            text = ''
        else:
            text = ','.join([bell_name_from_num(b) for b in unassigned_bells])  + " left"
        self._bells_left['text'] = text

    @property
    def _row(self):
        """ Gets the row that this touch should occupy in the grid. """
        return User.ROWS + self._index

    @classmethod
    def create_headings(cls, parent):
        headers = [
            tk.Label(parent, text=i, font=(FONT_NAME, FONT_SIZE, "bold"))
            for i in ["Bells", "Mode", "", "Touch notes"]
        ]
        for i, h in enumerate(headers):
            h.grid(row = User.ROWS - 1, column = 1 + i, sticky = "S")
        return headers

    def _on_load(self):
        print(f"Loading #{self._index + 1}: '{self._name_box.get()}'")


class Matrix:
    """ The matrix between touches (left) and ringers (top) """

    def __init__(self, parent):
        # ===== INITIALISATION =====
        self._parent = parent
        self._panel = tk.Frame(self._parent)

        self._users = []
        self._touches = []

        # Forward layout methods to the panel
        self.pack = self._panel.pack
        self.grid = self._panel.grid

        # ===== TOP-LEFT CORNER BOX =====
        self._help_box = tk.Frame(self._panel)
        self._help_box.grid(
            row = 0,
            column = 0,
            rowspan = User.ROWS - 1,
            columnspan = Touch.COLS,
            sticky = "NESW"
        )

        self._title = tk.Label(
            self._help_box,
            text="Minor General",
            font = (FONT_NAME, int(FONT_SIZE * 1.5), 'bold')
        )
        self._title.pack(pady = (5, 0))

        self._desc = tk.Label(
            self._help_box,
            text="Run extremely efficient Ringing Room practices.",
            font = (FONT_NAME, FONT_SIZE, 'italic')
        )
        self._desc.pack()

        self._tower_label = tk.Label(
            self._help_box,
            text="Tower #963758214: OUSCR",
            font = (FONT_NAME, FONT_SIZE)
        )
        self._tower_label.pack()

        self._help_block = tk.Frame(self._help_box)
        self._help_block.pack(expand = True, fill = tk.X, pady = 7, padx = 5)

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
                text = '- ' + l,
                font = (FONT_NAME, int(FONT_SIZE * .75)),
                anchor = "w"
            )
            label.pack(expand = True, fill = tk.X)
            self._help_labels.append(label)

        # ===== INITIALISE THE TABLE =====

        # Always start with one touch, and generate the headings for the columns
        self._headers = Touch.create_headings(self._panel)
        self._add_touch()

        # Initially create some people.  TODO: Link this to RR
        for n in ["Me", "The Ringing Rabbit", "Ringing Mummy", "Heather", "Katie", "Julia", "Jess",
                  "Ali", "Josie", "Jon", "David"]:
            self._add_user(n)

        # Create the plus button
        self._plus_button = tk.Button(
            self._panel,
            text = '+',
            font = FONT,
            command = self._add_touch
        )
        self._plus_button.grid(row = MAX_ROWS, column = 0, columnspan = MAX_COLS + 1)

    def _add_touch(self):
        """ Adds another row to the touch list. """
        new_touch = Touch(self._panel, len(self._touches))
        # Add all the existing users to the touch row
        for u in self._users:
            new_touch.add_user(u)
        # Add touch to list
        self._touches.append(new_touch)

    def _add_user(self, user_name):
        """
        Add a user to the practice.  This will be called as a callback for a user entering the
        practice.
        """
        user = User(self._panel, user_name)
        user.grid(
            row = 0,
            column = Touch.COLS + len(self._users),
            rowspan = User.ROWS,
            sticky = "S",
            padx = 2,
            pady = (4, 2),
        )
        self._users.append(user)

        # Add this user to all the touches
        for t in self._touches:
            t.add_user(user)


def main():
    window = tk.Tk()

    window.title("Minor General")

    matrix = Matrix(window)
    matrix.pack()

    window.mainloop()

if __name__ == "__main__":
    main()
