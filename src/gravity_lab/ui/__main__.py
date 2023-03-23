from threading import Event, Thread
from time import sleep
import tkinter as tk
from tkinter import ttk
from typing import get_type_hints

from gravity_lab.cartesian_coordinate_system import CartesianCoordinateSystem
from gravity_lab.data import Data, TrajectoryData, jpl_horizons_body_mass_kg, jpl_horizons_search_major_body_id, jpl_horizons_ephemeris_vector
from gravity_lab.gravity_model import GravityModel, ModelRunner
from gravity_lab.math import Vector
from gravity_lab.newtonian_mechanics_model import NewtonianMechanicsModel
from gravity_lab.ui import Display2DCanvas


class SimulationManager():
    gravity_lab_models = [
        NewtonianMechanicsModel(CartesianCoordinateSystem(2)),
        NewtonianMechanicsModel(CartesianCoordinateSystem(3))
    ]

    def __init__(self, models: list[ModelRunner] = []):
        self.models = SimulationManager.gravity_lab_models + models

        self.model_name_to_model_map = {}
        for model in SimulationManager.gravity_lab_models:
            self.model_name_to_model_map[f"{model.__class__.__name__}:{model.coordinate_system.dimension}D"] = model

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

        # [data_name: str] -> Data()
        self.loaded_data = {}

        self.simulation_manager = SimulationManager()
        self.build_ui()

    def interact_on_canvas(self, event):
        closest_objects = self.canvas.find_closest(event.x, event.y)
        if len(closest_objects) == 0:
            self.add_object(event)
        else:
            closest_object = closest_objects[0]
            closest_object_position = self.canvas.coords(closest_object)
            x1, y1, _, _ = closest_object_position
            if (Vector([event.x, event.y]) - Vector([x1, y1])).magnitude() < 10.0:
                pass # TODO: open menu to see object details and interact with object
            else:
                self.add_object(event)

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
                    if self.simulation_manager.current_model.coordinate_system.dimension == 2:
                        entry_str_var.set(f"{float(click_event.x)/self.canvas.zoom - self.canvas.display_translation[0]/self.canvas.zoom},{float(click_event.y)/self.canvas.zoom - self.canvas.display_translation[1]/self.canvas.zoom}")
                    elif self.simulation_manager.current_model.coordinate_system.dimension == 3:
                        entry_str_var.set(f"{float(click_event.x)/self.canvas.zoom - self.canvas.display_translation[0]/self.canvas.zoom},0.0,{float(click_event.y)/self.canvas.zoom - self.canvas.display_translation[1]/self.canvas.zoom}")
                else:
                    if self.simulation_manager.current_model.coordinate_system.dimension == 2:
                        entry_str_var.set("0.0,0.0")
                    elif self.simulation_manager.current_model.coordinate_system.dimension == 3:
                        entry_str_var.set("0.0,0.0,0.0")
                vector_entry.pack()

        add_button = tk.Button(top)
        add_button.config(text='Add Object')
        add_button.pack()

        add_button.bind("<Button-1>", lambda _: self.create_object_from_tkinter_strinvars(parameter_name_to_variable_map, parameter_name_to_type_map, model_object_type, top))

    def create_object_from_tkinter_strinvars(self, parameter_name_to_variable_map, parameter_name_to_type_map, model_object_type: type, to_destory: tk.Tk = None):
        arguments = {}
        for parameter_name in parameter_name_to_variable_map:
            parameter_variable = parameter_name_to_variable_map[parameter_name]
            parameter_value = parameter_variable.get()
            arguments[parameter_name] = parameter_name_to_type_map[parameter_name](parameter_value)

        model_object = model_object_type(**arguments)
        self.simulation_manager.current_model.objects.append(model_object)

        self.canvas.add_object(model_object)

        if to_destory != None:
            to_destory.destroy()

    def create_object(self, model_object_init_params):
        # get the type of objects used by the model
        model_object_type: type = get_type_hints(self.simulation_manager.current_model.__init__)["objects"].__args__[0]

        model_object = model_object_type(**model_object_init_params)
        self.simulation_manager.current_model.objects.append(model_object)

        self.canvas.add_object(model_object)

    def select_model(self, *args):
        self.simulation_manager.current_model = self.simulation_manager.model_name_to_model_map[self.model_var.get()]

        if self.simulation_manager.current_model.coordinate_system.dimension == 2:
            self.display_2d_coord_index = [0, 1]
        # Assuming 3D coordinates are (x, y, z) where y is the height. Height is not displayed.
        # For our solar system this would give a flat view of solar system but our solar system 
        # is relatively flat so that's ok
        elif self.simulation_manager.current_model.coordinate_system.dimension == 3:
            self.display_2d_coord_index = [0, 2]

    def load_jpl_horizons_solar_system_objects(self):
        self.model_var.set("NewtonianMechanicsModel:3D")

        for body_name in ["Sun", "Mercury", "Venus", "Earth", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]:
            body_jpl_horizons_id = jpl_horizons_search_major_body_id(body_name)
            sleep(0.1)
            vector_data = jpl_horizons_ephemeris_vector(body_jpl_horizons_id)
            sleep(0.1)
            mass_kg = jpl_horizons_body_mass_kg(body_jpl_horizons_id)
            sleep(0.1)

            self.create_object({
                "mass": mass_kg,
                "coordinate": Vector([vector_data[0]["position"]["x"], vector_data[0]["position"]["y"], vector_data[0]["position"]["z"]]),
                "velocity": Vector([vector_data[0]["velocity"]["x"], vector_data[0]["position"]["y"], vector_data[0]["velocity"]["z"]])
            })

        self.zoom_string_var.set('5e-10')
        self.canvas.display_translation = [100.0, 100.0]

    def open_data_popup(self, data: Data):
        top = tk.Toplevel(self.window)
        top.title(data.name)

        model_validation_label = tk.Label(top, text="Model Validation")
        model_validation_label.pack()

        model_validation_step_size_label = tk.Label(top, text="Model Validation Step Size:")
        model_validation_step_size_label.pack()

        self.model_validation_step_size_val = 86400.0

        def update_model_validation_step_size(model_validation_step_size):
            try:
                self.model_validation_step_size_val = float(model_validation_step_size)
            except:
                pass

        self.model_validation_step_size = tk.StringVar()
        self.model_validation_step_size.trace_add("write", lambda name, index, mode : update_model_validation_step_size(self.model_validation_step_size.get()))
        self.model_validation_step_size.set("86400")
        model_validation_step_size = tk.Entry(top, textvariable=self.model_validation_step_size)
        model_validation_step_size.pack()

        model_validation_button = tk.Button(top)
        model_validation_button.config(text='Run Model Validation')
        model_validation_button.pack()

        model_validation_button.bind("<Button-1>", lambda _ : data.validate_model(self.simulation_manager.current_model, self.model_validation_step_size_val))

        separator = ttk.Separator(top, orient='horizontal')
        separator.pack(fill='x')

    def load_jpl_horizons_solar_system_trajectory_data(self):
        trajectory_data: TrajectoryData = TrajectoryData.load_solar_system_from_jpl_horizons_system()
        self.loaded_data[trajectory_data.name] = trajectory_data
        self.data_list.insert(tk.END, trajectory_data.name)

    def build_ui(self):
        menu_bar = tk.Menu(self.window)
        self.window.config(menu=menu_bar)

        initial_objects_menu = tk.Menu(menu_bar)
        initial_objects_menu.add_command(label="Solar System (Data from JPL Horizons System)", command=self.load_jpl_horizons_solar_system_objects)
        menu_bar.add_cascade(label="Load Initial Object Values", menu=initial_objects_menu)

        data_menu = tk.Menu(menu_bar)
        data_menu.add_command(label="Solar System (Data from JPL Horizons System) Trajectory Data", command=self.load_jpl_horizons_solar_system_trajectory_data)
        menu_bar.add_cascade(label="Load Data", menu=data_menu)

        left_frame = tk.Frame(self.window)
        left_frame.pack(side='left',  fill='both', padx=1, expand=True)

        right_frame = tk.Frame(self.window)
        right_frame.pack(side='right',  fill='both', expand=True)

        canvas = Display2DCanvas(left_frame)
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

        separator = ttk.Separator(right_frame, orient='horizontal')
        separator.pack(fill='x')

        data_label = tk.Label(right_frame, text='Data:')
        data_label.pack()

        data_list = tk.Listbox(right_frame)
        self.data_list = data_list
        data_list.pack()

        def select_data(self, event: tk.Event):
            list_index = int(event.widget.curselection()[0])
            data_name = event.widget.get(list_index)
            data = self.loaded_data[data_name]
            self.open_data_popup(data)

        self.data_list.bind('<<ListboxSelect>>', lambda event: select_data(self, event))

        separator = ttk.Separator(right_frame, orient='horizontal')
        separator.pack(fill='x')

        view_configs_label = tk.Label(right_frame, text='View Configs:')
        view_configs_label.pack()

        zoom_lablel = tk.Label(right_frame, text='Zoom')
        zoom_lablel.pack()

        def update_zoom(zoom_str):
            try:
                self.canvas.zoom = float(zoom_str)
            except:
                pass

        self.zoom_string_var = tk.StringVar()
        self.zoom_string_var.trace_add("write", lambda name, index, mode : update_zoom(self.zoom_string_var.get()))
        self.zoom_string_var.set("1")
        zoom_entry = tk.Entry(right_frame, textvariable=self.zoom_string_var)
        zoom_entry.pack()

        self.canvas.bind("<Button-1>", self.interact_on_canvas)

        self.window.protocol("WM_DELETE_WINDOW", self.window_close)

    def window_close(self):
        self.canvas.update_canvas_thread.suspend_event.set()
        self.simulation_manager.stop_simulation()
        self.window.destroy()

    def open_window(self):
        self.window.mainloop()

    def run_simulation(self, _):
        self.simulation_manager.simulate()

if __name__ == '__main__':
    lab = GravityLab()
    lab.open_window()