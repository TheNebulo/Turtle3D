# This is the Demo/example script on how to use Turtle3D
# When running this demo, the controls are as follows:
# - Hold W/A/S/D for Forwards/Backwards/Left/Right movement respectfully
# - Hold arrow keys for rotating in each direction.
# This script should showcase the basic abilities of Turtle3D.

import Turtle3D
import time
import keyboard

def create_material():
    """Create a shiny gold material for the 3D objects."""
    return Turtle3D.Material(
        name="Shiny Gold Metal",
        ambient_color=(255, 255, 255),
        diffuse_color=(255, 255, 255),
        specular_color=(255, 255, 255),
        specular_coefficient=100
    )

def setup_scene():
    """Set up the scene with lights and a camera."""
    scene = Turtle3D.Scene("Test Scene", ambient_light=(25, 25, 25))

    # Add lights to the scene
    light_1 = Turtle3D.Light('Blue', position=[0, 0, -20], color=(64, 64, 255), intensity=0.7)
    light_2 = Turtle3D.Light('Red', position=[75, 0, -20], color=(255, 64, 64), intensity=0.7)
    scene.add_light(light_1)
    scene.add_light(light_2)

    # Set up the camera
    camera = Turtle3D.Camera("Main Camera", x_clamp=[-89, 89], fov=90, position=[37.5,0,-100])
    scene.set_active_camera(camera)

    return scene, camera

def load_objects(scene, material):
    """Load the 3D objects and add them to the scene."""
    # Load an OBJ file
    vertices, faces = Turtle3D.load_obj_file('teapot.obj')

    # Create multiple objects with the same model but different positions
    objects = [
        Turtle3D.Object(f"Teapot_{i}", vertices, faces, material=material, scale=0.075, position=[i*25, 0, 0])
        for i in range(4)
    ]
    
    # Add objects to the scene
    for obj in objects:
        scene.add_object(obj)

def camera_controls(camera):
    """Add interactive camera controls with keyboard."""
    # Define camera control settings
    forward = camera.get_forward_vector()
    back = [-vector for vector in forward]
    up = camera.get_up_vector()
    down = [-vector for vector in up]
    right = camera.get_product_vector(forward, up)
    left = [-vector for vector in right]

    # Check for keyboard inputs and move the camera accordingly
    if keyboard.is_pressed('w'): 
        camera.translate(*forward)
    if keyboard.is_pressed('s'): 
        camera.translate(*back)
    if keyboard.is_pressed('a'): 
        camera.translate(*left)
    if keyboard.is_pressed('d'): 
        camera.translate(*right)
    if keyboard.is_pressed('left'): 
        camera.rotate(y=-1)
    if keyboard.is_pressed('right'):
        camera.rotate(y=1)
    if keyboard.is_pressed('up'): 
        camera.rotate(x=1)
    if keyboard.is_pressed('down'): 
        camera.rotate(x=-1)
    if keyboard.is_pressed('space'): 
        camera.translate(*up)
    if keyboard.is_pressed('c'): 
        camera.translate(*down)

def main():
    """Main function to set up and run the demo."""
    # Initialize scene and material
    material = create_material()
    scene, camera = setup_scene()

    # Load objects into the scene
    load_objects(scene, material)

    # Toggle full screen for the global window
    Turtle3D.global_window.toggle_full_screen()

    # Start the main loop
    while True:

        # Rotate every object in the scene
        for object in scene._object_memory:
            object.rotate(1,1,1)

        # Process camera controls
        camera_controls(camera)

        # Render the scene
        try:
            scene.render_scene()
        except:
            break
        
        # Sleep to achieve the desired frame rate (approximately 60 FPS)
        time.sleep(1/60)

if __name__ == "__main__":
    main()