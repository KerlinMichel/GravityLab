from threading import Event, Thread
from time import sleep
import tkinter as tk

from gravity_lab.gravity_model import Object


class Display2DCanvas(tk.Canvas):
    def __init__(self, master):
        super().__init__(master)

        self.model_object_to_canvas_object = {}

        suspend_thread_event = Event()
        self.update_canvas_thread = Thread(target=self.update_canvas, args=(suspend_thread_event,), daemon=True)
        self.update_canvas_thread.suspend_event = suspend_thread_event
        self.update_canvas_thread.start()

        self.zoom = 1.0

        #TODO make the 2 values below editable
        self.display_translation = [50.0, 50.0]
        self.display_2d_coord_index = [0, 1]


    def add_object(self, model_object: Object):
        canvas_object = self.create_oval(0, 0, 3, 3, fill='#000000')
        self.model_object_to_canvas_object[model_object] = canvas_object

    def update_canvas(self, suspend_event: Event):
        while not suspend_event.is_set():
            sleep(1.0/60.0)
            try:
                for model_object in self.model_object_to_canvas_object:
                    canvas_object = self.model_object_to_canvas_object[model_object]
                    if hasattr(model_object, 'coordinate'):
                        self.moveto(canvas_object, (model_object.coordinate[self.display_2d_coord_index[0]] * self.zoom) + self.display_translation[0],
                                            (model_object.coordinate[self.display_2d_coord_index[1]] * self.zoom) + self.display_translation[1])
            except:
                pass # TODO react to errors