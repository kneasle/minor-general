import tkinter as tk
from belltower import RingingRoomTower
from belltower.page_parsing import parse_page

def choose_tower(
    title = "Choose a RR tower!",
    normal_font = ("TkDefaultFont", 12),
    title_font = ("TkDefaultFont", 12, "bold")
):
    """
    This function creates a window where the user can input the tower ID, returning a
    RingingRoomTower or None when the user has made their choice.
    """
    # Incredible hack: arrays are always passed by reference, so we can set the first item in an
    # array from inside a local function.  Isn't Python wonderful?
    window_intentionally_closed = [False]

    def on_id_change(*args):
        """ Callback called whenever the user changes the tower ID. """
        tower_id = tower_id_var.get()

        # Try to load the tower name from RR.  If this fails, then the tower does not exist
        try:
            _url, tower_name, _bell_type = parse_page(tower_id, "ringingroom.com")
        except Exception:
            tower_name = None

        # Decide on what text to display, according to what the user wrote
        if tower_name is None:
            if tower_id == "":
                text = "Tower names can't be blank"
            else:
                text = f"No tower found for {tower_id}"
        else:
            text = f"Join '{tower_name}'?"
        
        # Update the UI
        join_button['state'] = tk.DISABLED if tower_name is None else tk.NORMAL  
        tower_name_box['text'] = text
        tower_name_box['fg'] = "red" if tower_name is None else "black"

    def on_join_click():
        """ Mark the closing as intentional, and close the window. """
        window_intentionally_closed[0] = True
        window.destroy()

    window = tk.Tk()
    window.title(title)
    # A title with the program name
    title = tk.Label(window, text = title, font = title_font)
    # Row for the tower ID box
    input_frame = tk.Frame(window)
    enter_tower_id = tk.Label(input_frame, text = "Enter tower ID:", font = normal_font)
    tower_id_var = tk.StringVar(window, value = "")
    tower_id_var.trace_add("write", on_id_change)
    entry = tk.Entry(input_frame, textvariable=tower_id_var)
    # Box for either an error or the tower name
    tower_name_box = tk.Label(window, text = "...", font = normal_font)
    # Row for the buttons
    cancel_join_label = tk.Frame(window)
    cancel_button = tk.Button(cancel_join_label, text="Cancel", font=normal_font,
                              command=window.destroy)
    join_button = tk.Button(cancel_join_label, text="Join", font=normal_font, command=on_join_click)

    title.pack()
    input_frame.pack()
    enter_tower_id.grid(row = 0, column = 0)
    entry.grid(row = 0, column = 1)
    tower_name_box.pack()
    cancel_join_label.pack()
    cancel_button.grid(row = 0, column = 0)
    join_button.grid(row = 0, column = 1)

    # Cause an update so that everything gets initialised
    on_id_change()

    # Go into the mainloop, until either the window is closed, or the user hits 'Join'
    window.mainloop()

    return RingingRoomTower(int(tower_id_var.get())) if window_intentionally_closed[0] else None
