from threading import Event, Thread
from time import sleep
import tkinter as tk

from gravity_lab.data import TrajectoryData
from gravity_lab.gravity_model import Object
from gravity_lab.math import Vector


class Display2DCanvas(tk.Canvas):
    def __init__(self, master):
        super().__init__(master)

        self.model_object_to_canvas_object = {}
        self.canvas_object_to_model_object = {}

        self.trajectory_data_objects = {}

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
        self.canvas_object_to_model_object[canvas_object] = model_object

    def add_trajectory(self, trajectory_data: TrajectoryData):
        def rgb_to_hex(r, g, b):
            r, g, b = int(r), int(g), int(b)
            return f'#{r:02x}{g:02x}{b:02x}'
        for object_name in trajectory_data.object_trajectories:
            object_data, object_trajectory_data = trajectory_data.object_trajectories[object_name]
            canvas_objects = []

            def parse_vector(vector):
                return Vector([vector['x'], vector['y'], vector['z']])
            num_trajectory_points = len(object_trajectory_data)
            for point_idx, trajectory_point in enumerate(object_trajectory_data):
                trajectory_trace_ratio = point_idx/num_trajectory_points
                position = parse_vector(trajectory_point['position'])
                canvas_object = self.create_oval(0, 0, 3, 3,
                    fill=f'{rgb_to_hex(trajectory_trace_ratio*255, 255 - trajectory_trace_ratio*255, 0)}')

                self.moveto(canvas_object,
                    (position[self.display_2d_coord_index[0]] * self.zoom) + self.display_translation[0],
                    (position[self.display_2d_coord_index[1]] * self.zoom) + self.display_translation[1])

                canvas_objects.append(canvas_object)
            self.trajectory_data_objects[object_name] = {
                "data": object_trajectory_data,
                "canvas_objects": canvas_objects
            }

    def update_canvas(self, suspend_event: Event):
        while not suspend_event.is_set():
            sleep(1.0/60.0)
            try:
                for model_object in self.model_object_to_canvas_object:
                    canvas_object = self.model_object_to_canvas_object[model_object]
                    if hasattr(model_object, 'coordinate'):
                        self.moveto(canvas_object, (model_object.coordinate[self.display_2d_coord_index[0]] * self.zoom) + self.display_translation[0],
                                            (model_object.coordinate[self.display_2d_coord_index[1]] * self.zoom) + self.display_translation[1])

                for object_name in self.trajectory_data_objects:
                    for i, trajectory_point in enumerate(self.trajectory_data_objects[object_name]["data"]):
                        canvas_object = self.trajectory_data_objects[object_name]["canvas_objects"][i]
                        def parse_vector(vector):
                            return Vector([vector['x'], vector['y'], vector['z']])
                        position = parse_vector(trajectory_point['position'])
                        self.moveto(canvas_object,
                            (position[self.display_2d_coord_index[0]] * self.zoom) + self.display_translation[0],
                            (position[self.display_2d_coord_index[1]] * self.zoom) + self.display_translation[1])
            except Exception as e:
                print(e) # TODO react to errors