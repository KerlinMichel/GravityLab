from threading import Event, Thread
from time import sleep
import tkinter as tk
from typing import get_type_hints

from gravity_lab.cartesian_coordinate_system import CartesianCoordinateSystem
from gravity_lab.gravity_model import GravityModel, ModelRunner
from gravity_lab.math import Vector
from gravity_lab.newtonian_mechanics_model import NewtonianMechanicsModel

class SimulationManager():
    gravity_lab_models = [
        NewtonianMechanicsModel(CartesianCoordinateSystem(2))
    ]

    def __init__(self, models: list[ModelRunner] = []):
        self.models = SimulationManager.gravity_lab_models + models

        self.model_name_to_model_map = {}
        for model in SimulationManager.gravity_lab_models:
            self.model_name_to_model_map[model.__class__.__name__] = model

        self.current_model: GravityModel = None
        self.simulation_thread: Thread = Thread(target=self.run_model, daemon=True)
        suspect_thread_event: Event = Event()
        self.simulation_thread.suspend_event = suspect_thread_event

    def run_model(self):
        while not self.simulation_thread.suspend_event.is_set():
            sleep(1.0/120.0)
            self.current_model.step(1.0/120.0)

    def simulate(self):
        self.simulation_thread.start()

    def stop_simulation(self):
        self.simulation_thread.suspend_event.set()
    
    def model_names(self):
        return list(self.model_name_to_model_map.keys())

class GravityLab():
    def __init__(self):
        self.window = tk.Tk()
        self.window.title('Gravity Lab (2D Only)')
        self.window.config(bg="black")
        self.window.minsize(200, 100)

        self.simulation_manager = SimulationManager()
        self.build_ui()

        suspend_thread_event = Event()
        self.update_canvas_thread = Thread(target=self.update_canvas, args=(suspend_thread_event,), daemon=True)
        self.update_canvas_thread.suspend_event = suspend_thread_event
        self.update_canvas_thread.start()

    def add_object(self, event):
        # get the type of objects used by the model
        model_object_type: type = get_type_hints(self.simulation_manager.current_model.__init__)["objects"].__args__[0]

        self.open_add_object_popup(get_type_hints(model_object_type.__init__), model_object_type, event)

    def open_add_object_popup(self, parameter_name_to_type_map, model_object_type: type, click_event: tk.Event):
        top = tk.Toplevel(self.window)
        top.title("Add Object")
        parameter_name_to_variable_map = {}
        for param_name in parameter_name_to_type_map:
            param_type = parameter_name_to_type_map[param_name]
            param_name_label = tk.Label(top, text= f"{param_name}:")
            param_name_label.pack()

            entry_str_var = tk.StringVar(top)
            parameter_name_to_variable_map[param_name] = entry_str_var
            if param_type == float:
                float_entry = tk.Entry(top, textvariable=entry_str_var)
                float_entry.pack()
            elif param_type == Vector:
                vector_entry = tk.Entry(top, textvariable=entry_str_var)
                if param_name == 'coordinate':
                    entry_str_var.set(f"{click_event.x},{click_event.y}")
                else:
                    entry_str_var.set("0.0,0.0")
                vector_entry.pack()

        add_button = tk.Button(top)
        add_button.config(text='Add Object')
        add_button.pack()

        add_button.bind("<Button-1>", lambda _: self.create_object(parameter_name_to_variable_map, parameter_name_to_type_map, model_object_type, top))

    def create_object(self, parameter_name_to_variable_map, parameter_name_to_type_map, model_object_type: type, to_destory: tk.Tk = None):
        arguments = {}
        for parameter_name in parameter_name_to_variable_map:
            parameter_variable = parameter_name_to_variable_map[parameter_name]
            parameter_value = parameter_variable.get()
            arguments[parameter_name] = parameter_name_to_type_map[parameter_name](parameter_value)

        model_object = model_object_type(**arguments)
        self.simulation_manager.current_model.objects.append(model_object)

        canvas_object = self.canvas.create_oval(model_object.coordinate[0], model_object.coordinate[1], model_object.coordinate[0] + 8, model_object.coordinate[1] + 8)
        self.canvas_objects.append((canvas_object, model_object))

        if to_destory != None:
            to_destory.destroy()

    def select_model(self, *args):
        self.simulation_manager.current_model = self.simulation_manager.model_name_to_model_map[self.model_var.get()]

    def build_ui(self):
        left_frame = tk.Frame(self.window)
        left_frame.pack(side='left',  fill='both', padx=1, expand=True)

        right_frame = tk.Frame(self.window)
        right_frame.pack(side='right',  fill='both', expand=True)

        canvas = tk.Canvas(left_frame)
        canvas.pack()
        self.canvas = canvas
        self.canvas_objects = []

        model_selection_label = tk.Label(right_frame, text="Model:")
        model_selection_label.pack()

        self.model_var = tk.StringVar(right_frame)
        self.model_var.trace_add("write", self.select_model)
        self.model_var.set(self.simulation_manager.model_names()[0])

        model_option_menu = tk.OptionMenu(right_frame, self.model_var, *self.simulation_manager.model_names())
        model_option_menu.pack()

        simulate_button = tk.Button(right_frame)
        simulate_button.config(text='Simulate')
        simulate_button.pack()

        simulate_button.bind("<Button-1>", self.run_simulation)

        canvas.bind("<Button-1>", self.add_object)

        self.window.protocol("WM_DELETE_WINDOW", self.window_close)

    def update_canvas(self, suspend_event: Event):
        while not suspend_event.is_set():
            sleep(1.0/60.0)
            for canvas_object, model_object in self.canvas_objects:
                if hasattr(model_object, 'coordinate'):
                    self.canvas.moveto(canvas_object, model_object.coordinate[0], model_object.coordinate[1])

    def window_close(self):
        self.update_canvas_thread.suspend_event.set()
        self.simulation_manager.stop_simulation()
        self.window.destroy()

    def open_window(self):
        self.window.mainloop()

    def run_simulation(self, _):
        self.simulation_manager.simulate()

if __name__ == '__main__':
    lab = GravityLab()
    lab.open_window()