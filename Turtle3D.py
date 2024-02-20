"""Module that renders and manages 3D objects in Turtle, with lighting, cameras, and more."""

import turtle, math, copy, numpy

def load_obj_file(filename):
    """
    Load vertices and faces from an .obj file.

    Returns:
    - verts (list): 2D list containing [x,y,z] coordinates of every vertex as floats or integers.
    - faces (list): 2D list containing the indexes of vertices to join to make faces.
    """
    verts = []
    faces = []
    file = open(filename, 'r')
    lines = file.readlines()
    for line in lines:
        if line.startswith("v "):
            raw = line.replace("\n", "").replace("v ","").split(" ")
            for x in range(len(raw)): raw[x] = float(raw[x])
            verts.append(raw)
        elif line.startswith("f "):
            raw = line.replace("\n", "").replace("f ","").split(" ")
            for x in range(len(raw)): raw[x] = int(raw[x])
            faces.append(raw)
    file.close()
    return verts, faces

class Turtle3DError(Exception):
    """
    A custom exception class for Turtle3D specific errors.
    
    Parameters:
    - message (str): Description of the error (has default message).
    """
    def __init__(self, message: str = "Unknown Turtle3D error"):
        self.message = message
        super().__init__(self.message)
    
class DuplicateNameError(Turtle3DError):
    """
    Exception raised when attempting to add an object/camera/light to the renderer with a duplicate name.
    
    Parameters:
    - name (str): Name of object/camera.
    - message (str): Description of the error (has default message).
    """
    def __init__(self, name : str, message: str = "Object/camera/light with name '{}' already exists in global memory!"):
        super().__init__(message.format(name))
        
class AlreadyInSceneError(Turtle3DError):
    """
    Exception raised when attempting to add an object/light to a scene it is already in.
    
    Parameters:
    - message (str): Description of the error (has default message).
    """
    def __init__(self, object_name : str, message: str = "Object/light '{}' already exists in renderer scene memory!"):
        super().__init__(message.format(object_name))

class IDNotFoundError(Turtle3DError):
    """
    Exception raised when an object with a specified id cannot be found in global or scene memory.
    
    Parameters:
    - object_id (int): The identifier of the object which could not be found.
    - message (str): Description of the error (has default message).
    """
    def __init__(self, object_id: int, message: str = "Object/camera/light with ID: {} cannot be found in global or scene memory!"):
        super().__init__(message.format(object_id))
        
class NoActiveCamera(Turtle3DError):
    """
    Exception raised when attempting to render a scene without a set active camera.
    
    Parameters:
    - scene_name (str): Name of the scene
    - message (str): Description of the error (has default message).
    """
    def __init__(self, scene_name, message: str = "Scene '{}' does not have an active camera!"):
        super().__init__(message.format(scene_name))

class NoScenePermission(Turtle3DError):
    """
    Exception raised when attempting to change a scene value without permission
    
    Parameters:
    - scene_name (str): Name of the scene
    - scene_value (str): Name of the value attempted to change.
    - message (str): Description of the error (has default message).
    """
    def __init__(self, scene_name, scene_value, message: str = "Scene '{}' doesn't permit modfication of value '{}'!"):
        super().__init__(message.format(scene_name, scene_value))
        
class Window:
    """
    Instance of turtle window. Turtle3D initialises an instance during runtime, and always uses the instance attached to global_window.

    Parameters:
    - width (int): Width of the Turtle window. Defaults to 800.
    - height (int): Height of the Turtle window. Defaults to 600.
    - title (str): Title for the Turtle window. Defaults to "Turtle GL".
    - fullscreen (bool): Whether to launch the Turtle in fullscreen borderless. Defaults to false.
    """
    def __init__(self, width: int = None, height: int = None, title: str = None, fullscreen: bool = None):
        if width is None: width = 800
        if height is None: height = 600
        if title is None: title = "Turtle3D"
        self.screen = turtle.Screen()
        self.screen.colormode(255)
        self.screen.tracer(0,0)
        self.screen.setup(width=width, height=height)
        self.canvas = self.screen.getcanvas()
        self._is_full_screen = False
        if fullscreen: self.toggle_full_screen()
        self.pointer = turtle.Turtle()
        self.pointer.hideturtle()
        self._mouse_x = 0
        self._mouse_y = 0
        self.screen.title(title)
        self.canvas.bind('<Motion>', self._track_mouse_motion)
        self.screen.listen()

    def toggle_full_screen(self):
        """
        Switch between borderless fullscreen and windowed.
        """
        self._is_full_screen = not self._is_full_screen
        self.canvas.winfo_toplevel().attributes("-fullscreen", self._is_full_screen)
        
    def destroy(self):
        """
        Destroy the Turtle window.
        """
        self.canvas.destroy()
        turtle.bye()
            
    def _track_mouse_motion(self, event):
        """
        Internal function to track mouse motion. Bound to the canvas with a motion sequence.

        Parameters:
        - event (tkinter.Event): Tkinter event to recieve motion information from.
        """
        half_width = self.screen.window_width() // 2
        half_height = self.screen.window_height() // 2
        self._mouse_x = event.x - half_width
        self._mouse_y = half_height - event.y

global_window = Window()
"""Window instance used by all render functions."""

class Material:
    def __init__(self, name: str, ambient_color: tuple = None, diffuse_color: tuple = None,  specular_color: tuple = None, specular_coefficient: float =None):
        """
        Material for Turtle3D objects to use to calculate lighting.

        Parameters:
        - name (str): The name of the material.
        - ambient_color (tuple): The ambient RGB color as a tuple (R, G, B) - Defaults to white. 
        - diffuse_color (tuple): The diffuse RGB color as a tuple (R, G, B) - Defaults to white.
        - specular_color (tuple): The specular RGB color as a tuple (R, G, B) - Defaults to white.
        - specular_coefficient (float): The shininess coefficient of the material - Defaults to 10.0.
        """
        self.name = name
        self.ambient_color = ambient_color if ambient_color is not None else (255, 255, 255)
        self.diffuse_color = diffuse_color if diffuse_color is not None else (255, 255, 255)
        self.specular_color = specular_color if specular_color is not None else (255, 255, 255)
        self.specular_coefficient = specular_coefficient if specular_coefficient else 10.0
    
    def get_rgb_tuple(self):
        """
        Utility function to get the diffuse color as an RGB tuple (0-255).

        Returns:
        diffuse_color (tuple) - The diffuse colour of the material.
        """
        return self.diffuse_color
    
class Light:
    """
    Point/omni light used to add lighting to scenes and objects.

    Parameters:
    - name (str): Name of the light, must be unique in the global memory.    
    - position (list): A list of three floats or integers representing the light's position on the x, y, and z axis.
    - color (tuple): A tuple representing RGB color values that the light emits - Defaults to (255,255,255).
    - intesity (float): A float from 0.0 to 1.0 representing the intensity of the light - Defaults to 1.0.
    """
    _global_light_memory = []
    _next_memory_id = 1

    def __init__(self, name: str, position: list, color : tuple = None, intensity: float = None):
        
        if any(light._name == name for light in self._global_light_memory):
            raise DuplicateNameError()
        
        self._name = name
        self.position = position
        self.color = color if color else (255,255,255)
        self.intensity = intensity if intensity else 1.0

        self._scenes = []
        self._id = self._next_memory_id
        self._global_light_memory.append(self)
        self._next_memory_id += 1

    def add_to_scene(self, scene: 'Scene'):
        """
        Adds the light to a specified scene's memory.
        
        Parameters:
        - scene (Scene): The Scene object for the scene the light is to be added to.
        """
        scene.add_light(self)

    def remove_from_scene(self, scene: 'Scene'):
        """
        Removes the light from a specified scene's memory.
        
        Parameters:
        - scene (Scene): The Scene object for the scene the light is to be removed from.
        """
        try:
            scene.remove_light(self)
        except ValueError:
            raise IDNotFoundError(self._id)
        
    def change_name(self, new_name: str):
        """
        Changes the name of the light, ensuring it remains unique in the global memory.
        
        Parameters:
        - new_name (str): New name assigned to the light, must be unique among all scenes.
        """
        if any(obj._name == new_name for obj in self._global_light_memory):
            raise DuplicateNameError()
        self._name = new_name
    

class Scene:
    """
    Represents a scene which can contain multiple objects, cameras, and lights.
    
    Parameters:
    - name (str): Name assigned to the scene, must be unique among all scenes.
    - ambient_light (tuple): Ambient light/background for scene (R,G,B) - Defaults to (25,25,25).
    """
    _global_scene_memory = []
    _next_memory_id = 1

    def __init__(self, name: str, ambient_light: tuple = None):
        if any(scene._name == name for scene in self._global_scene_memory):
            raise DuplicateNameError()
        
        if ambient_light is None:
            ambient_light = (25,25,25)

        self.ambient_light = ambient_light
        self._name = name
        self._object_memory = []
        self._light_memory = []
        self._active_camera = None
        
        self._id = self._next_memory_id
        self._next_memory_id += 1
        self._global_scene_memory.append(self)

    def add_object(self, object: 'Object'):
        """
        Adds an object to the scene's memory by object reference.
        
        Parameters:
        - object (Object): Reference to the object to be added.
        """
        if any(obj._name == object._name for obj in self._object_memory):
            raise AlreadyInSceneError()
        self._object_memory.append(object)
        object._scenes.append(self)

    def remove_object(self, object: 'Object'):
        """
        Removes an object from the scene's memory by object reference.
        
        Parameters:
        - object (Object): Reference to the object to be removed.
        """
        try:
            self._object_memory.remove(object)
            object._scenes.remove(self)
        except ValueError:
            raise IDNotFoundError(object._id)

    def get_object_from_memory(self, object_id: int):
        """
        Retrieves an object from the scene's memory by its id.
        
        Parameters:
        - object_id (int): The identifier of the object which is to be retrieved.
        """
        for obj in self._object_memory:
            if obj._id == object_id:
                return obj
        raise IDNotFoundError(object_id)
    
    def add_light(self, light: 'Light'):
        """
        Adds a light to the scene's memory by reference.
        
        Parameters:
        - object (Light): Reference to the light to be added.
        """
        if any(obj._name == light._name for obj in self._light_memory):
            raise AlreadyInSceneError()
        self._light_memory.append(light)
        light._scenes.append(self)

    def remove_light(self, light: 'Light'):
        """
        Removes a light from the scene's memory by reference.
        
        Parameters:
        - light (Light): Reference to the light to be removed.
        """
        try:
            self._light_memory.remove(light)
            light._scenes.remove(self)
        except ValueError:
            raise IDNotFoundError(light._id)

    def get_light_from_memory(self, light_id: int):
        """
        Retrieves a light from the scene's memory by its id.
        
        Parameters:
        - light_id (int): The identifier of the light which is to be retrieved.
        """
        for obj in self._light_memory:
            if obj._id == light_id:
                return obj
        raise IDNotFoundError(light_id)
    
    def set_active_camera(self, camera: 'Camera'):
        """
        Sets the camera used to render the scene.
        
        Parameters:
        - camera (Camera): Reference to the camera instance.
        """
        self._active_camera = camera

    def remove_active_camera(self):
        """
        Removes an active camera from the scene.
        """
        self._active_camera = None
    
    def change_name(self, new_name: str):
        """
        Changes the name of the scene, ensuring it remains unique in the global scene memory.
        
        Parameters:
        - new_name (str): New name assigned to the scene, must be unique among all scenes.
        """
        if any(obj._name == new_name for obj in self._global_scene_memory):
            raise DuplicateNameError()
        self._name = new_name
        
    def render_scene(self, mode: str = 'face'):
        """
        Renders all objects in scene.
        
        Parameters:
        - mode (str): Rendering mode, can be 'wire' or 'face'.
        """
        if self._active_camera is None: raise NoActiveCamera(self._name)
        distances = [(obj, obj.get_distance_to_camera(self._active_camera)) for obj in self._object_memory]
        distances.sort(key=lambda x: x[1], reverse=True)
        global_window.pointer.clear()
        if global_window.screen.bgcolor() != self.ambient_light: global_window.screen.bgcolor(self.ambient_light)
        for obj, distance in distances:
            obj._render(global_window.pointer, self._active_camera, self.ambient_light, self._light_memory, mode)
        global_window.screen.update()
        
class Camera:
    """
    Represents a camera used by the renderer to render scenes.
    
    Parameters:
    - name (str): Name of the renderer camera, must be unique in the global memory.
    - fov (int): An integer representing the camera's field of view - Defaults to 60.
    - position (list): A list of three floats or integers representing the camera's position on the x, y, and z axis - Defaults to [0,0,0].
    - rotation (list): A list of three floats or integers representing the rotation transformation around the x, y, and z axis - Defaults to [0,0,0].
    - near_plane (float): An integer representing the minimum distance an object can be from the camera before it is no longer rendered - Defaults to 0.1.
    - far_plane (float): An integer representing the maximum distance an object can be from the camera before it is no longer rendered - Defaults to 1000.
    - rotation_order (list): The order in which rotations are applied to objects. Used to prevent/minimise gimbal lock - Defaults to ['y','x','z'].
    - x_clamp (list): A list containing the minimum and maximum value for the rotation on the X axis (i.e. [-90, 90]) - Defaults to None
    - y_clamp (list): A list containing the minimum and maximum value for the rotation on the Y axis (i.e. [-90, 90]) - Defaults to None
    - z_clamp (list): A list containing the minimum and maximum value for the rotation on the Z axis (i.e. [-90, 90]) - Defaults to None
    """
    _global_memory = []
    _next_memory_id = 1

    def __init__(self, name: str, position: list = None, rotation: list = None, fov: int = None, near_plane: float = None, far_plane: float = None, rotation_order : list = None, x_clamp: list = None, y_clamp: list = None, z_clamp: list = None):
        
        if position is None:
            position = [0, 0, 0]
        if rotation is None:
            rotation = [0, 0, 0]
        if fov is None:
            fov = 60
        if near_plane is None:
            near_plane = 0.1
        if far_plane is None:
            far_plane = 1000
        if rotation_order is None:
            rotation_order = ['y','x','z']
        if x_clamp is None: x_clamp = None
        if y_clamp is None: z_clamp = None
        if z_clamp is None: z_clamp = None

        if any(obj._name == name for obj in self._global_memory):
            raise DuplicateNameError()
        self._name = name

        self._position = position
        self._rotation = rotation
        self.fov = fov
        self.near_plane = near_plane
        self.far_plane = far_plane
        self.rotation_order = rotation_order
        self.x_clamp = x_clamp
        self.y_clamp = y_clamp
        self.z_clamp = z_clamp

        self._id = self._next_memory_id
        self._global_memory.append(self)
        self._next_memory_id += 1

    def get_forward_vector(self):
        """
        Get the vector containing the relative forward direction of the camera.

        Returns:
        forward_vector (list): 3-dimensional vector for relative forward direction.
        """
        pitch, yaw, _ = [math.radians(angle) for angle in self._rotation]
        
        forward_x = -math.sin(-yaw) * math.cos(pitch)
        forward_y = math.sin(pitch)
        forward_z = math.cos(pitch) * math.cos(-yaw)
        
        return [forward_x, forward_y, forward_z]
    
    def get_up_vector(self):
        """
        Get the vector containing the relative up direction of the camera.

        Returns:
        up_vector (list): 3-dimensional vector for relative up direction.
        """
        pitch, yaw, roll = [math.radians(angle) for angle in self._rotation]

        cos_yaw = math.cos(-yaw)
        sin_yaw = math.sin(-yaw)

        up_x = (cos_yaw * math.sin(roll)) - (sin_yaw * math.sin(pitch) * math.cos(roll))
        up_y = math.cos(pitch) * math.cos(roll)
        up_z = (sin_yaw * math.sin(roll)) + (cos_yaw * math.sin(pitch) * math.cos(roll))

        return [up_x, up_y, up_z]
    
    def get_product_vector(self, vector_1, vector_2):
        """
        Get the dot product of two 3-dimensional vectors.

        Returns:
        dot_product (list): Dot product vector.
        """
        x = vector_2[1] * vector_1[2] - vector_2[2] * vector_1[1]
        y = vector_2[2] * vector_1[0] - vector_2[0] * vector_1[2]
        z = vector_2[0] * vector_1[1] - vector_2[1] * vector_1[0]
        
        return [x,y,z]

    def set_rotation(self, x: float = None, y: float = None, z: float = None):
        """
        Set camera rotation on multiple axis around its center (clamped).

        Parameters:
        - x (float): The amount of degrees to set X axis rotation to.
        - y (float): The amount of degrees to set Y axis rotation to.
        - z (float): The amount of degrees to set Z axis rotation to.
        """
        if x:
            if self.x_clamp:
                if x < self.x_clamp[0]: x = self.x_clamp[0]
                elif x > self.x_clamp[1]: x = self.x_clamp[1] 
            self._rotation[0] = x 
        if y:
            if self.y_clamp:
                if y < self.y_clamp[0]: y = self.y_clamp[0]
                elif y > self.y_clamp[1]: y = self.y_clamp[1] 
            self._rotation[1] = y 
        if z:
            if self.z_clamp:
                if z < self.z_clamp[0]: z = self.z_clamp[0]
                elif z > self.z_clamp[1]: z = self.z_clamp[1] 
            self._rotation[0] = z

    
    def rotate(self, x: float = None, y: float = None, z: float = None):
        """
        Rotate camera on multiple axis around its center (clamped).

        Parameters:
        - x (float): The amount of degrees to turn around X axis by.
        - y (float): The amount of degrees to turn around Y axis by.
        - z (float): The amount of degrees to turn around Z axis by.
        """
        if x:
            if self.x_clamp:
                if x + self._rotation[0] < self.x_clamp[0]: x = self.x_clamp[0] - self._rotation[0]
                elif x + self._rotation[0] > self.x_clamp[1]: x = self.x_clamp[1] - self._rotation[0]     
            self._rotation[0] += x 
        if y:
            if self.y_clamp:
                if y + self._rotation[1] < self.y_clamp[0]: y = self.y_clamp[0] - self._rotation[1]
                elif y + self._rotation[1] > self.y_clamp[1]: y = self.y_clamp[1] - self._rotation[1]     
            self._rotation[1] += y 
        if z:
            if self.z_clamp:
                if z + self._rotation[2] < self.z_clamp[0]: z = self.z_clamp[0] - self._rotation[2]
                elif z + self._rotation[2] > self.z_clamp[1]: z = self.z_clamp[1] - self._rotation[2]     
            self._rotation[2] += z
            
    def translate(self, x : float = None, y : float = None, z : float = None):
        """
        Translates camera induvidually on all 3 axis.

        Parameters:
        - x (float): The translation amount for the X axis.
        - y (float): The translation amount for the Y axis.
        - z (float): The translation amount for the Z axis.
        """
        if x: self._position[0] += x
        if y: self._position[1] += y
        if z: self._position[2] += z

    def set_position(self, x : float = None, y : float = None, z : float = None):
        """
        Sets position for the camera on all 3 axis.

        Parameters:
        - x (float): The position on the X axis.
        - y (float): The position on the Y axis.
        - z (float): The position on the Z axis.
        """
        if x: self._position[0] = x
        if y: self._position[1] = y
        if z: self._position[2] = z
        
    def add_to_scene(self, scene: Scene):
        """
        Adds the object to a specified scene's memory.
        
        Parameters:
        - scene (Scene): The Scene object for the scene the camera is to be added to.
        """
        scene.set_active_camera(self)

    def remove_from_scene(self, scene: Scene):
        """
        Removes the object from a specified scene's memory.
        
        Parameters:
        - scene (Scene): The Scene object for the scene the camera is to be removed from.
        """
        if scene._active_camera == self: scene.remove_active_camera()
        else: raise NoScenePermission(scene._name, "_active_camera", "Cannot remove active camera from scene '{}' when value'{}' is taken by a different camera instance!")

    def change_name(self, new_name: str):
        """
        Changes the name of the camera, ensuring it remains unique in the global memory.
        
        Parameters:
        - new_name (str): New name assigned to the camera, must be unique among all scenes.
        """
        if any(obj._name == new_name for obj in self._global_memory):
            raise DuplicateNameError()
        self._name = new_name

class Object:
    """
    Represents a renderable object that can be applied to multiple scenes, with various transformation properties.

    Parameters:
    - name (str): Name of the renderable object, must be unique in the global memory.
    - vertex_array (list): A list of vertices that defines the shape of the object.
    - face_array (list): A list of indexes used to construct faces to define the shape of the object (starts at 1 by .obj convention).
    - position (list): A list of three floats or integers representing the object's position on the x, y, and z axis - Defaults to [0,0,0].
    - rotation (list): A list of three floats or integers representing the rotation transformation around the x, y, and z axis - Defaults to [0,0,0].
    - scale (float | int | list): A list of three floats or integers representing how much the object should be scaled, where 1 represents original size. A singular float or int represent uniform scaling. Defaults to [1,1,1].
    - material (Material): An instance of Material containing the lighting properties for the object - Defaults to default Material instance.
    - visible (bool): A boolean indicating whether the object is visible in the scene - Defaults to True.
    """
    _global_memory = []
    _next_memory_id = 1

    def __init__(self, name: str, vertex_array: list, face_array : list, position: list = None, rotation: list = None, scale: float | int | list = None, material: Material = None, visible: bool = None):
        
        if position is None:
            position = [0, 0, 0]
        if rotation is None:
            rotation = [0, 0, 0]
        if scale is None:
            scale = [1, 1, 1]
        if material is None:
            material = Material()
        if visible is None:
            visible = True
        
        self._face_array = face_array

        vertex_array = self._center_vertex_array(vertex_array, [0,0,0])
        self._original_vertex_array = vertex_array
        self._transformed_vertex_array = vertex_array
        self._translated_vertex_array = vertex_array
        self._camera_perspective_vertex_array = None # Only updated during render

        if any(obj._name == name for obj in self._global_memory):
            raise DuplicateNameError()
        self._name = name

        position[2] = 0 - position[2]
        self._position = position
        self._rotation = rotation
        if isinstance(scale, float) or isinstance(scale, int): scale = [scale, scale, scale]
        self._scale = scale

        self.material = material
        self.visible = visible

        self._scenes = []
        self._id = self._next_memory_id
        self._global_memory.append(self)
        self._next_memory_id += 1
        
        self._update_transformed_vertices()

    def update_vertex_array(self, new_vertex_array: list, new_face_array: list = None):
        """
        Update the vertex array (and optionally the face array). Object will be automatically repositioned, scaled, and rotated.

        Parameters:
        - new_vertex_array (list): The new vertex array for the object.
        - new_face_array (list): The new face array for the object - Defaults to None.
        """
        if new_face_array: self._face_array = new_face_array
        new_vertex_array = self._center_vertex_array(new_vertex_array, [0,0,0])
        self._original_vertex_array = new_vertex_array
        self._transformed_vertex_array = new_vertex_array
        self._translated_vertex_array = new_vertex_array
        self._camera_perspective_vertex_array = None
        self._update_transformed_vertices()        
        
    def get_distance_to_camera(self, camera: Camera):
        """
        Get the distance from a camera to the closest vertex in the object.

        Parameters:
        - camera (Camera): The camera object to measure distance from.
        
        Returns:
        - distance (float): The shortest distance from the object to the camera.
        """
        camera_position = camera._position
        camera_rotation = camera._rotation
        
        self._camera_perspective_vertex_array = copy.deepcopy(self._translated_vertex_array)

        for step in camera.rotation_order:
            if step == 'x': self._rotate_x(-camera_rotation[0], self._camera_perspective_vertex_array, camera_position)
            if step == 'y': self._rotate_y(-camera_rotation[1], self._camera_perspective_vertex_array, camera_position)
            if step == 'z': self._rotate_z(-camera_rotation[2], self._camera_perspective_vertex_array, camera_position)
            
        distances = []    
            
        for vertex in self._camera_perspective_vertex_array:
            x1, y1, z1 = camera_position
            x2, y2, z2 = vertex
            
            dx = (x2 - x1) ** 2
            dy = (y2 - y1) ** 2
            dz = (z2 - z1) ** 2

            distances.append(math.sqrt(dx + dy + dz))
            
        distances.sort()
        return distances[0]

    def _update_transformed_vertices(self):
        """
        Applies all transformations (excluding translation) to original vertex data.
        """
        self._transformed_vertex_array = copy.deepcopy(self._original_vertex_array)
        self._transformed_vertex_array = [[x * self._scale[0], y * self._scale[1], z * self._scale[2]] for x, y, z in self._transformed_vertex_array]
        self._rotate_x(self._rotation[0], self._transformed_vertex_array, [0,0,0])
        self._rotate_y(self._rotation[1], self._transformed_vertex_array, [0,0,0])
        self._rotate_z(self._rotation[2], self._transformed_vertex_array, [0,0,0])
        self._update_translated_vertices()

    def _update_translated_vertices(self):
        """
        Applies translations to transformed vertex data (world-space).
        """
        self._translated_vertex_array = copy.deepcopy(self._transformed_vertex_array)
        for i in range(len(self._translated_vertex_array)):
            vertex = self._translated_vertex_array[i]
            self._translated_vertex_array[i] = [vertex[0]+self._position[0], vertex[1]+self._position[1], vertex[2]-self._position[2]]
    
    def _center_vertex_array(self, vertex_array, new_centroid: list = None, current_centroid = None):
        """
        Adjusts an object's vertex array to make the centroid at the specified new centroid position, with an optional parameter to specify the current centroid to create offsets.

        Parameters:
        - vertex_array (list): 2D list of an object's vertices.
        - new_centroid (list): The x, y, z coordinates of the new centroid position.
        - current_centroid (list): The x, y, z coordinates of the current centroid position - Defaults to calculated current centroid.

        Returns:
        - new_vertex_array (list): Centered 2D list of an object's vertices with centroid at new_centroid
        """
        num_vertices = len(vertex_array)
        if num_vertices == 0:
            return []

        if current_centroid is None:
            sum_x = sum_y = sum_z = 0
            for vertex in vertex_array:
                sum_x += vertex[0]
                sum_y += vertex[1]
                sum_z += vertex[2]

            current_centroid = [sum_x / num_vertices, sum_y / num_vertices, sum_z / num_vertices]

        dx = new_centroid[0] - current_centroid[0]
        dy = new_centroid[1] - current_centroid[1]
        dz = new_centroid[2] - current_centroid[2]

        new_vertex_array = [[vertex[0] + dx, vertex[1] + dy, vertex[2] + dz] for vertex in vertex_array]

        return new_vertex_array
    
    def set_rotation(self, x: float = None, y: float = None, z: float = None):
        """
        Set object rotation on multiple axis around its center.

        Parameters:
        - x (float): The amount of degrees to set X axis rotation to.
        - y (float): The amount of degrees to set Y axis rotation to.
        - z (float): The amount of degrees to set Z axis rotation to.
        """
        if x: self._rotation[0] = x 
        if y: self._rotation[1] = y
        if z: self._rotation[2] = z
        self._update_transformed_vertices()

    
    def rotate(self, x: float = None, y: float = None, z: float = None):
        """
        Rotate object on multiple axis around its center.

        Parameters:
        - x (float): The amount of degrees to turn around X axis by.
        - y (float): The amount of degrees to turn around Y axis by.
        - z (float): The amount of degrees to turn around Z axis by.
        """
        if x: self._rotation[0] += x 
        if y: self._rotation[1] += y
        if z: self._rotation[2] += z
        self._update_transformed_vertices()
    
    def _rotate_x(self, angle: float, vertex_array: list, pivot: list):
        """
        Rotate vertex array by a certain amount of degrees on the X axis around a pivot.

        Parameters:
        - angle (float): The amount of degrees to turn by.
        - vertex_array (list): The vertices to rotate.
        - pivot (list): The point to turn around.
        """
        angle = math.radians(angle)
        sinTheata = math.sin(angle)
        cosTheata = math.cos(angle)
        
        py, pz = pivot[1], pivot[2]
        
        for a in range(len(vertex_array)):
            y = vertex_array[a][1] - py
            z = vertex_array[a][2] - pz
            
            new_y = y * cosTheata + z * sinTheata
            new_z = z * cosTheata - y * sinTheata
            
            vertex_array[a][1] = new_y + py
            vertex_array[a][2] = new_z + pz

    def _rotate_y(self, angle: float, vertex_array: list, pivot: list):
        """
        Rotate vertex array by a certain amount of degrees on the Y axis around a pivot.

        Parameters:
        - angle (float): The amount of degrees to turn by.
        - vertex_array (list): The vertices to rotate.
        - pivot (list): The point to turn around.
        """
        angle = math.radians(angle)
        sinTheata = math.sin(angle)
        cosTheata = math.cos(angle)
        
        px, pz = pivot[0], pivot[2]

        for a in range(len(vertex_array)):
            x = vertex_array[a][0] - px
            z = vertex_array[a][2] - pz
            
            new_x = x * cosTheata + z * sinTheata
            new_z = z * cosTheata - x * sinTheata
            
            vertex_array[a][0] = new_x + px
            vertex_array[a][2] = new_z + pz

    def _rotate_z(self, angle: float, vertex_array: list, pivot: list):
        """
        Rotate vertex array by a certain amount of degrees on the Z axis around a pivot.

        Parameters:
        - angle (float): The amount of degrees to turn by.
        - vertex_array (list): The vertices to rotate.
        - pivot (list): The point to turn around.
        """
        angle = math.radians(angle)
        sinTheata = math.sin(angle)
        cosTheata = math.cos(angle)
        
        px, py = pivot[0], pivot[1]
        
        for a in range(len(vertex_array)):
            x = vertex_array[a][0] - px
            y = vertex_array[a][1] - py
            
            new_x = x * cosTheata + y * sinTheata
            new_y = y * cosTheata - x * sinTheata
            
            vertex_array[a][0] = new_x + px
            vertex_array[a][1] = new_y + py

    def set_scale(self, x_axis_multiplier : float = None, y_axis_multiplier : float = None, z_axis_multiplier : float = None, uniform = False):
        """
        Sets the object scale on all 3 axis, with the option of uniform rescaling (takes only x_axis_mulitplier).

        Parameters:
        - x_axis_multiplier (float): The multiplier for rescaling the X axis.
        - y_axis_multiplier (float): The multiplier for rescaling the Y axis.
        - z_axis_multiplier (float): The multiplier for rescaling the Z axis.
        - uniform (bool): When True, x_axis_multiplier becomes multiplier for all axis.
        """ 
        if uniform: z_axis_multiplier = y_axis_multiplier = x_axis_multiplier
        self._scale = [x_axis_multiplier, y_axis_multiplier, z_axis_multiplier]
        self._update_transformed_vertices()


    def scale(self, x_axis_multiplier : float = None, y_axis_multiplier : float = None, z_axis_multiplier : float = None, uniform = False):
        """
        Rescales the object on all 3 axis, with the option of uniform rescaling (takes only x_axis_mulitplier).

        Parameters:
        - x_axis_multiplier (float): The multiplier for rescaling the X axis.
        - y_axis_multiplier (float): The multiplier for rescaling the Y axis.
        - z_axis_multiplier (float): The multiplier for rescaling the Z axis.
        - uniform (bool): When True, x_axis_multiplier becomes multiplier for all axis.
        """
        if uniform: z_axis_multiplier = y_axis_multiplier = x_axis_multiplier
        self._scale = [self._scale[0] * x_axis_multiplier, self._scale[1] * y_axis_multiplier, self._scale[2] * z_axis_multiplier]
        self._update_transformed_vertices()

    def translate(self, x : float = None, y : float = None, z : float = None):
        """
        Translates object induvidually on all 3 axis.

        Parameters:
        - x (float): The translation amount for the X axis.
        - y (float): The translation amount for the Y axis.
        - z (float): The translation amount for the Z axis.
        """
        if x: self._position[0] += x
        if y: self._position[1] += y
        if z: self._position[2] += z
        self._update_transformed_vertices()

    def set_position(self, x : float = None, y : float = None, z : float = None):
        """
        Sets position for the object on all 3 axis.

        Parameters:
        - x (float): The position on the X axis.
        - y (float): The position on the Y axis.
        - z (float): The position on the Z axis.
        """
        if x: self._position[0] = x
        if y: self._position[1] = y
        if z: self._position[2] = z
        self._update_transformed_vertices()
        
    def add_to_scene(self, scene: Scene):
        """
        Adds the object to a specified scene's memory.
        
        Parameters:
        - scene (Scene): The Scene object for the scene the object is to be added to.
        """
        scene.add_object(self)

    def remove_from_scene(self, scene: Scene):
        """
        Removes the object from a specified scene's memory.
        
        Parameters:
        - scene (Scene): The Scene object for the scene the object is to be removed from.
        """
        try:
            scene.remove_object(self)
        except ValueError:
            raise IDNotFoundError(self._id)

    def change_name(self, new_name: str):
        """
        Changes the name of the object, ensuring it remains unique in the global memory.
        
        Parameters:
        - new_name (str): New name assigned to the object, must be unique among all scenes.
        """
        if any(obj._name == new_name for obj in self._global_memory):
            raise DuplicateNameError()
        self._name = new_name

    def _render(self, pointer: turtle.Turtle, camera: Camera, ambient_light: tuple, lights, mode: str = "face"):
        """
        Renders object from the perspective of a camera with lighting data.

        Parameters:
        - pointer (turtle.Turtle): Turtle pointer used to render object.
        - camera (Camera): Camera instance to use for rendering.
        - ambient_light (tuple): An RGB tuple containing the ambient light colour.
        - lights (list): A list of Light objects used to light the object.
        - mode (str): Rendering mode, can be 'wire' or 'face'.
        """
        if not self.visible:
            return

        camera_position = camera._position
        camera_rotation = camera._rotation
        fov = camera.fov
        near_plane = camera.near_plane
        far_plane = camera.far_plane

        window_width = turtle.window_width()
        window_height = turtle.window_height()
        aspect_ratio = window_width / window_height

        def precompute_normals():
            self._face_normals = []
            for face in self._face_array:
                face_vertices = [self._translated_vertex_array[i - 1] for i in face]
                normal = calculate_normal(face_vertices[:3]) 
                self._face_normals.append(normal)

        def calculate_normal(face_vertices):
            u = [face_vertices[1][i] - face_vertices[0][i] for i in range(3)]
            v = [face_vertices[2][i] - face_vertices[0][i] for i in range(3)]
            normal = [
                u[1]*v[2] - u[2]*v[1],
                u[2]*v[0] - u[0]*v[2],
                u[0]*v[1] - u[1]*v[0],
            ]
            return normalize_vector(normal)
        
        def normalize_vector(vector):
            norm = (vector[0] ** 2 + vector[1] ** 2 + vector[2] ** 2) ** 0.5
            if norm < 1e-6:
                return [0, 0, 0]
            return [v / norm for v in vector]

        def perspective_transform(vert):
            fov_rad = math.radians(fov)
            half_width = math.tan(fov_rad / 2)
            half_height = half_width / aspect_ratio

            x_offset = vert[0] - camera_position[0]
            y_offset = vert[1] - camera_position[1]
            z_offset = vert[2] - camera_position[2]

            if z_offset <= near_plane:
                return None
            elif z_offset > far_plane:
                return None

            x_proj = x_offset / (z_offset * half_width)
            y_proj = y_offset / (z_offset * half_height)

            x_ndc = x_proj * 2 - 1
            y_ndc = 1 - y_proj * 2

            x_screen = (x_ndc + 1) / 2 * window_width
            y_screen = (1 - y_ndc) / 2 * window_height

            return [x_screen, y_screen]

        def compute_lighting(face_vertices, normal, lights, camera_position, material):
            color = [material.ambient_color[i] * ambient_light[i] / 255 for i in range(3)]

            normalized_normal = normalize_vector(normal)

            for light in lights:
                light_dir = [light.position[i] - face_vertices[0][i] for i in range(3)]
                light_distance = math.sqrt(sum([d ** 2 for d in light_dir]))
                normalized_light_dir = normalize_vector(light_dir)

                dot_product = max(sum(n * l for n, l in zip(normalized_normal, normalized_light_dir)), 0)
                diffuse_intensity = dot_product * light.intensity
                diffuse = [material.diffuse_color[i] * diffuse_intensity * light.color[i] / 255 for i in range(3)]
                
                reflect_dir = [2 * normalized_normal[i] * dot_product - normalized_light_dir[i] for i in range(3)]
                normalized_reflect_dir = normalize_vector(reflect_dir)
                view_dir = normalize_vector([camera_position[i] - face_vertices[0][i] for i in range(3)])
                spec_angle = max(sum(r * v for r, v in zip(normalized_reflect_dir, view_dir)), 0)
                spec_intensity = (spec_angle ** material.specular_coefficient) / (light_distance + 1)
                specular = [material.specular_color[i] * spec_intensity * light.color[i] / 255 for i in range(3)]

                color = [min(255, color[i] + diffuse[i] + specular[i]) for i in range(3)]

            return color
        
        def draw_filled_polygon(vertices, color):
            color = [int(c) for c in color]
            pointer.fillcolor(color)
            pointer.penup() 
            pointer.goto(vertices[0][0], vertices[0][1])
            pointer.begin_fill()
            for vertex in vertices[1:]:
                pointer.goto(vertex[0], vertex[1])
            pointer.goto(vertices[0][0], vertices[0][1])
            pointer.end_fill()

        def draw_wireframe(vertex_array):
            pointer.pensize(1)
            pointer.color(self.material.ambient_color)
            for face in self._face_array:
                projected_face = []
                for vertex_index in face:
                    vertex = perspective_transform(vertex_array[vertex_index - 1])
                    if vertex is not None:
                        projected_face.append(vertex)
                if len(projected_face) < 3:
                    continue
                pointer.penup()
                pointer.goto(projected_face[0][0], projected_face[0][1])
                pointer.pendown()
                for vertex in projected_face[1:]:
                    pointer.goto(vertex[0], vertex[1])
                pointer.goto(projected_face[0][0], projected_face[0][1])

        def draw_faces(vertex_array):
            precompute_normals()
            
            sorted_faces = sorted(enumerate(self._face_array), key=lambda item: -numpy.mean([vertex_array[i - 1][2] + camera_position[2] for i in item[1]]))
            for index, face in sorted_faces:
                face_vertices = [vertex_array[i - 1] for i in face]
                projected_vertices = [perspective_transform(vertex) for vertex in face_vertices]
                projected_vertices = [v for v in projected_vertices if v is not None]
                if len(projected_vertices) < 3: continue
                normal = self._face_normals[index]
                color = compute_lighting(face_vertices, normal, lights, camera_position, self.material)
                draw_filled_polygon(projected_vertices, color)
            
        self._camera_perspective_vertex_array = copy.deepcopy(self._translated_vertex_array)

        for step in camera.rotation_order:
            if step == 'x': self._rotate_x(-camera_rotation[0], self._camera_perspective_vertex_array, camera_position)
            if step == 'y': self._rotate_y(-camera_rotation[1], self._camera_perspective_vertex_array, camera_position)
            if step == 'z': self._rotate_z(-camera_rotation[2], self._camera_perspective_vertex_array, camera_position)

        if mode == 'wire':
            draw_wireframe(self._camera_perspective_vertex_array)
        elif mode == 'face':
            draw_faces(self._camera_perspective_vertex_array)
        else:
            raise Turtle3DError("Invalid rendering mode. Choose from 'wire', 'face'.")