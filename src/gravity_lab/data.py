from datetime import datetime
import re
from time import sleep
from typing import Any, Mapping, Tuple, Union

import requests

class Data():
    def __init__(self, name: str):
        self.name: str = name

class TrajectoryData(Data):
    # object_trajectories maps an index or string id to a tuple (object_data, trajectory data)
    def __init__(self, name: str, object_trajectories: Mapping[Union[int, str], Tuple[Any, list]]):
        super().__init__(name)
        self.object_trajectories = object_trajectories

    @classmethod
    def load_solar_system_from_jpl_horizons_system(cls) -> 'TrajectoryData':
        object_trajectories = {}
        for body_name in ["Sun", "Mercury", "Venus", "Earth", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]:
            body_jpl_horizons_id = jpl_horizons_search_major_body_id(body_name)
            sleep(0.1)
            vector_data = jpl_horizons_ephemeris_vector(body_jpl_horizons_id)
            sleep(0.1)
            mass_kg = jpl_horizons_body_mass_kg(body_jpl_horizons_id)
            sleep(0.1)
            object_data = {"mass_kg": mass_kg}
            object_trajectories[body_name] = (object_data, vector_data)

        return TrajectoryData("JPL Horizons Solar System", object_trajectories)

JPL_HORIZONS_SYSTEM_API_URL = "https://ssd.jpl.nasa.gov/api/horizons.api"

# TODO: Rewrite code below to use regex. Currently very hacky

def jpl_horizons_request(request_params: dict):
    return requests.get(JPL_HORIZONS_SYSTEM_API_URL, params=request_params)

def jpl_horizons_search_major_body_id(body_name: str):
    jpl_mb_response = jpl_horizons_request({
        'format': 'text',
        'COMMAND': 'MB'
    })

    response_lines = jpl_mb_response.text.split('\n')

    def str_is_int(str_):
        try: 
            int(str_)
            return True
        except ValueError:
            return False

    for line in response_lines:
        words = line.split(' ')

        # remove empty words
        words = [word for word in words if word != '']

        # some major body names have spaces on them
        if len(words) > 2 and words[2] == 'Barycenter':
            words[1] += ' Barycenter'
            words[2] = ''

        if len(words) < 2:
            continue

        if str_is_int(words[0]) and body_name.lower() == words[1].lower():
            return int(words[0])

    raise RuntimeError(f'Could not find major body with name {body_name} in JPL Horizons System')

# @0 is the Solar System Barycenter
def jpl_horizons_ephemeris_vector(body_id: int, center: str = "@0"):
    jpl_horizons_response = jpl_horizons_request({
        'format': 'text',
        'COMMAND': body_id,
        'EPHEM_TYPE': "VECTORS",
        'CENTER': center
    })

    response_lines = jpl_horizons_response.text.split('\n')

    vector_data_lines = []
    after_start_str = False
    for line in response_lines:
        if line == '$$EOE':
            break

        if after_start_str:
            vector_data_lines.append(line)

        if line == '$$SOE':
            after_start_str = True

    # group vector data lines by 4. Each 4 lines is a ephemeris vector data calculation
    n = 4
    vector_data_lines = [vector_data_lines[i:i+n] for i in range(0, len(vector_data_lines), n)]

    # TODO: verify that all JPL Horizons Vector data always uses km units. Currently assuming
    # this is true and converting values to m
    vector_data = []
    for vector_data_strs in vector_data_lines:
        date_data = vector_data_strs[0].split(' ')
        ephemeris_datetime = datetime.strptime(f"{date_data[3]} {date_data[4]}", "%Y-%b-%d %H:%M:%S.%f")

        position_data = vector_data_strs[1].split(' ')
        position_vector = {}
        for i in range(len(position_data)):
            offset = 1
            if position_data[i] == 'X':
                if position_data[i+offset] == '=':
                    offset += 1

                value = float(position_data[i+offset][1:])
                position_vector['x'] = value * 1000.0
            elif position_data[i] == 'Y':
                if position_data[i+offset] == '=':
                    offset += 1

                value = float(position_data[i+offset][1:])
                position_vector['y'] = value * 1000.0
            elif position_data[i] == 'Z':
                if position_data[i+offset] == '=':
                    offset += 1

                value = float(position_data[i+offset][1:])
                position_vector['z'] = value * 1000.0

        velocity_data = vector_data_strs[2].split(' ')
        velocity_vector = {}
        for i in range(len(velocity_data)):
            if velocity_data[i] == 'VX' or velocity_data[i] == 'VX=':
                value = float(velocity_data[i+1])
                velocity_vector['x'] = value * 1000.0
                continue
            elif velocity_data[i] == 'VY' or velocity_data[i] == 'VY=':
                value = float(velocity_data[i+1])
                velocity_vector['y'] = value * 1000.0
                continue
            elif velocity_data[i] == 'VZ' or velocity_data[i] == 'VZ=':
                value = float(velocity_data[i+1])
                velocity_vector['z'] = value * 1000.0
                continue

            if velocity_data[i].startswith('VX='):
                _, value = velocity_data[i].split('=')
                velocity_vector['x'] = float(value) * 1000.0
            elif velocity_data[i].startswith('VY='):
                _, value = velocity_data[i].split('=')
                velocity_vector['y'] = float(value) * 1000.0
            elif velocity_data[i].startswith('VZ='):
                _, value = velocity_data[i].split('=')
                velocity_vector['z'] = float(value) * 1000.0

        vector_data.append({
            'datetime': ephemeris_datetime,
            'position': position_vector,
            'velocity': velocity_vector
        })

    return vector_data

def jpl_horizons_body_mass_kg(body_id: int, center: str = "@0"):
    jpl_horizons_response = jpl_horizons_request({
        'format': 'text',
        'COMMAND': body_id,
        'EPHEM_TYPE': "VECTORS",
        'CENTER': center
    })

    response_lines = jpl_horizons_response.text.split('\n')

    mass_kg_regex = r"Mass(?:\,)?(?:\s*)?(?:x)?(?:\s*)?10\^(\d\d)(?:\s*)?(?:\()?kg(?:\))?(?:\s*)?=(?:\s*)(?:\~)?(\d+(?:.\d+)?)"

    for line in response_lines:
        match = re.search(mass_kg_regex, line)
        if match:
            power_of_10_exponent = int(match.group(1))
            scientific_notation_coefficient = float(match.group(2))
            return scientific_notation_coefficient * (10 ** power_of_10_exponent)

    mass_g_regex = r"Mass(?:\,)?(?:\s*)?(?:x)?(?:\s*)?10\^(\d\d)(?:\s*)?(?:\()?g(?:\))?(?:\s*)?=(?:\s*)(?:\~)?(\d+(?:.\d+)?)"

    for line in response_lines:
        match = re.search(mass_g_regex, line)
        if match:
            power_of_10_exponent = int(match.group(1))
            scientific_notation_coefficient = float(match.group(2))
            return (scientific_notation_coefficient / 1000.0) * (10 ** power_of_10_exponent)