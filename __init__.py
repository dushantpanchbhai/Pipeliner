import bpy
import os
import sys
import pip
import subprocess
import json
import datetime

bl_info = {
    "name": "Pipeliner",
    "author": "Dushant Panchbhai",
    "version": (1, 0),
    "blender": (4, 2, 0),
    "location": "3D View > Sidebar > Pipeliner",
    "description": "Automated project setup and model importing",
    "category": "3D View",
}

try:
    import zipfile
except ImportError:
    pip.main(['install', 'zipfile', '--target', (sys.exec_prefix) + '\\lib\\site-packages']) 
    import zipfile

try:
    import patoolib
except ImportError:    
    pip.main(['install', 'patool', '--target', (sys.exec_prefix) + '\\lib\\site-packages']) 
    import patoolib 

try:
    import py7zr
except ImportError:
    pip.main(['install', 'py7zr', '--target', (sys.exec_prefix) + '\\lib\\site-packages'])
    import py7zr

# pip.main(['install', 'shutil', '--target', (sys.exec_prefix) + '\\lib\\site-packages'])
# import shutil #need to install this

bl_info = {
    "name": "Pipeliner",
    "author": "Dushant Panchbhai",
    "version": (1, 0),
    "blender": (4, 2, 0),
    "location": "3D View > Sidebar > Pipeliner",
    "description": "Automated project setup and model importing",
    "category": "3D View",
}

bpy.types.Scene.extracted_filenames = bpy.props.CollectionProperty(type=bpy.types.PropertyGroup)

def extract_file(filepath, extract_to,delete_archieve):
    if filepath in [file.name for file in bpy.context.scene.extracted_filenames]:
        # Check if the extracted folder exists
        basename = os.path.splitext(os.path.basename(filepath))[0]
        extracted_folder = os.path.join(extract_to, basename)
        if os.path.exists(extracted_folder):
            print(f"[Warn] Folder '{extracted_folder}' already exists, skipping extraction.")
            return
        
    # Append the filename to the list
    item = bpy.context.scene.extracted_filenames.add()
    item.name = filepath

    if filepath.lower().endswith('.zip'):
        try:
            basename = os.path.splitext(os.path.basename(filepath))[0]
            new_directory = os.path.join(extract_to, basename)
            os.makedirs(new_directory, exist_ok=True)

            with zipfile.ZipFile(filepath, 'r') as zip_ref:
                zip_ref.extractall(new_directory)
            # Recursively check for archives in the extracted directory
            unzip_files(new_directory,delete_archieve)
        except Exception as e:
            print(f"[Error] Failed to extract zip file, exception -> {e}")

    elif filepath.lower().endswith('.rar'):
        try:
            basename = os.path.splitext(os.path.basename(filepath))[0]
            new_directory = os.path.join(extract_to, basename)
            os.makedirs(new_directory, exist_ok=True)
            patoolib.extract_archive(filepath, outdir=new_directory)

            # Recursively check for archives in extracted directory
            unzip_files(new_directory,delete_archieve)

        except Exception as e:
            print(f"[Error] Failed to extract rar file, exception -> {e}")

    elif filepath.lower().endswith('.7z'):
        try:
            basename = os.path.splitext(os.path.basename(filepath))[0]
            new_directory = os.path.join(extract_to, basename)
            os.makedirs(new_directory, exist_ok=True)
            archive = py7zr.SevenZipFile(filepath, mode='r')
            archive.extractall(new_directory)
            archive.close()

            # Recursively check for archives in extracted directory
            unzip_files(new_directory,delete_archieve)
        except Exception as e:
            print(f"[Error] failed to extrarct .7z file, exception -> {e}")

def unzip_files(directory,delete_archieve):
    """Recursively unzip .zip and .rar files in the given directory."""
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(('.zip', '.rar', '.7z')):
                file_path = os.path.join(root, file)
                print(f"Extracting file: {file_path}")
                extract_file(file_path, root,delete_archieve)
                # Optional: remove the archive file after extracting
                if delete_archieve==True:
                    os.remove(file_path)

# Importing file logic
def import_obj(filepath):
    print(f"[Message] Importing OBJ file: {filepath}")
    # Store the names of existing objects before import
    existing_objects = set(bpy.data.objects.keys())

    # Import the obj file
    bpy.ops.wm.obj_import(filepath=filepath)

    # Get the names of newly imported objects
    imported_objects = [obj for obj in bpy.context.selected_objects if obj.name not in existing_objects]

    # Create an empty object
    empty_name = os.path.basename(filepath).replace('.obj', '') + "_root"
    empty = bpy.data.objects.new(empty_name, None)
    bpy.context.collection.objects.link(empty)

    # Parent all imported objects to the empty object
    for obj in imported_objects:
        obj.parent = empty

def import_fbx(filepath):
    """Import an FBX file into Blender, parent parts to an empty, and mark as assets."""
    print(f"[Message] Importing FBX file: {filepath}")
    # Store the names of existing objects before import
    existing_objects = set(bpy.data.objects.keys())

    # Import the FBX file
    bpy.ops.import_scene.fbx(filepath=filepath)

    # Get the names of newly imported objects
    imported_objects = [obj for obj in bpy.context.selected_objects if obj.name not in existing_objects]

    # Create an empty object
    empty_name = os.path.basename(filepath).replace('.fbx', '') + "_root"
    empty = bpy.data.objects.new(empty_name, None)
    bpy.context.collection.objects.link(empty)

    # Parent all imported objects to the empty object
    for obj in imported_objects:
        obj.parent = empty

def import_gltf(filepath):
    """Import a GLTF file into Blender, parent parts to an empty, and mark as assets."""
    print(f"[Message] Importing GLTF file: {filepath}")

    # Store the names of existing objects before import
    existing_objects = set(bpy.data.objects.keys())

    # Import the GLTF file
    bpy.ops.import_scene.gltf(filepath=filepath)

    # Get the names of newly imported objects
    imported_objects = [obj for obj in bpy.context.selected_objects if obj.name not in existing_objects]

    # Determine the name for the empty object
    if os.path.basename(filepath).endswith(".glb"):
        empty_name = os.path.basename(filepath).replace('.glb', '') + "_root"
    elif os.path.basename(filepath).endswith(".gltf"):
        empty_name = os.path.basename(filepath).replace('.gltf', '') + "_root"

    # Ensure we have at least one imported object to get the collection
    if imported_objects:
        # Get the collection of the first imported object
        collection = imported_objects[0].users_collection[0]

        # Create an empty object in the same collection
        empty = bpy.data.objects.new(empty_name, None)
        collection.objects.link(empty)

        # Parent all imported objects to the empty object
        for obj in imported_objects:
            obj.parent = empty

    else:
        print("No objects were imported.")

def import_usd(filepath):
    """Import a USD file into Blender, parent parts to an empty, and mark as assets."""
    print(f"[Message] Importing USD file: {filepath}")

    # Store the names of existing objects before import
    existing_objects = set(bpy.data.objects.keys())

    # Import the GLTF file
    bpy.ops.wm.usd_import(filepath=filepath)

    # Get the names of newly imported objects
    imported_objects = [obj for obj in bpy.context.selected_objects if obj.name not in existing_objects]

def import_hdri(filepath):
    """Import an HDRI file into Blender's environment texture."""
    print(f"[Message] Importing HDRI file: {filepath}")
    
    # Ensure the World uses nodes
    if not bpy.context.scene.world.use_nodes:
        bpy.context.scene.world.use_nodes = True

    # Get the nodes
    world_nodes = bpy.context.scene.world.node_tree.nodes

    # Clear existing nodes
    world_nodes.clear()

    # Add Environment Texture node
    env_tex_node = world_nodes.new(type='ShaderNodeTexEnvironment')
    env_tex_node.image = bpy.data.images.load(filepath)
    env_tex_node.location = (-300, 0)  # Set location of the Environment Texture node

    # Add Background node
    bg_node = world_nodes.new(type='ShaderNodeBackground')
    bg_node.location = (0, 0)  # Set location of the Background node

    # Add Output node
    output_node = world_nodes.new(type='ShaderNodeOutputWorld')
    output_node.location = (300, 0)  # Set location of the Output node

    # Link nodes
    bpy.context.scene.world.node_tree.links.new(env_tex_node.outputs['Color'], bg_node.inputs['Color'])
    bpy.context.scene.world.node_tree.links.new(bg_node.outputs['Background'], output_node.inputs['Surface'])

    print("HDRI Imported successfully.")

# Blender UI Panel
#Refresh Button
class WM_OT_refresh_imports(bpy.types.Operator):
    bl_label = "Refresh Imports"
    bl_idname = "wm.refresh_imports"

    def execute(self, context):

        if context.scene.pipeliner.pipeline_setup == False:
            self.report({'ERROR'}, "Pipeline is not setup. First setup pipeline")
            return {'CANCELLED'}
        

        # Clear the list of FBX files and OBJ files
        context.scene.fbx_files.clear()
        context.scene.obj_files.clear()
        context.scene.gltf_files.clear()
        context.scene.usd_files.clear()
        context.scene.hdri_files.clear()

        # Scan the directory, extract files and find FBX, Obj, gltf, hdri, usd files
        unzip_files(os.path.join(context.scene.pipeliner.imports_path,"FBX"), context.scene.delete_archive)
        unzip_files(os.path.join(context.scene.pipeliner.imports_path,"OBJ"), context.scene.delete_archive)
        unzip_files(os.path.join(context.scene.pipeliner.imports_path,"GLTF"), context.scene.delete_archive)
        unzip_files(os.path.join(context.scene.pipeliner.imports_path,"USD"), context.scene.delete_archive)
        unzip_files(context.scene.pipeliner.hdri_path, context.scene.delete_archive)

        # Scanning fbx files
        for root, dirs, files in os.walk(os.path.join(context.scene.pipeliner.imports_path,"FBX")):
            for file in files:
                if file.lower().endswith('.fbx'):
                    file_path = os.path.join(root, file)
                    item = context.scene.fbx_files.add()
                    item.name = os.path.basename(file_path)
                    item.filepath = file_path
        
        # Scanning obj files
        for root, dirs, files in os.walk(os.path.join(context.scene.pipeliner.imports_path,"OBJ")):
            for file in files:
                if file.lower().endswith('.obj'):
                    file_path = os.path.join(root,file)
                    item = context.scene.obj_files.add()
                    item.name = os.path.basename(file_path)
                    item.filepath = file_path
        
        # Scanning gltf files
        for root, dirs, files in os.walk(os.path.join(context.scene.pipeliner.imports_path,"GLTF")):
            for file in files:
                if file.lower().endswith('.gltf') or file.lower().endswith('.glb'):
                    file_path = os.path.join(root,file)
                    item = context.scene.gltf_files.add()
                    item.name = os.path.basename(file_path)
                    item.filepath = file_path
                
        # Scanning usd files
        for root, dirs, files in os.walk(os.path.join(context.scene.pipeliner.imports_path,"USD")):
            for file in files:
                if file.lower().endswith('.usd') or file.lower().endswith('.usdz'):
                    file_path = os.path.join(root,file)
                    item = context.scene.usd_files.add()
                    item.name = os.path.basename(file_path)
                    item.filepath = file_path
        
        # Scanning exr files for hdri
        for root, dirs, files in os.walk(context.scene.pipeliner.hdri_path):
            for file in files:
                if file.lower().endswith('.exr'):
                    file_path = os.path.join(root,file)
                    item = context.scene.hdri_files.add()
                    item.name = os.path.basename(file_path)
                    item.filepath = file_path

        return {'FINISHED'}

#Import Fbx Operator
class WM_OT_import_fbx(bpy.types.Operator):
    bl_label = "Import FBX"
    bl_idname = "wm.import_fbx"
    filepath : bpy.props.StringProperty()

    def execute(self, context):
        try:
            import_fbx(self.filepath)
            self.report({'INFO'}, f"Imported {self.filepath}")
        except Exception as e:
            self.report({'ERROR'}, f"Failed to import {self.filepath}: {e}")
        return {'FINISHED'}

#Import Obj Operator
class WM_OT_import_obj(bpy.types.Operator):
    bl_label = "Import OBJ"
    bl_idname = "wm.import_obj"
    filepath: bpy.props.StringProperty()

    def execute(self, context):
        try:
            print("[Warning] objfile called")
            import_obj(self.filepath)
            self.report({'INFO'}, f"Imported {self.filepath}")
        except Exception as e:
            self.report({'ERROR'}, f"Failed to import {self.filepath}: {e}")
        return {'FINISHED'}

#Import Gltf Operator
class WM_OT_import_gltf(bpy.types.Operator):
    bl_label = "Import GLTF"
    bl_idname = "wm.import_gltf"
    filepath: bpy.props.StringProperty()

    def execute(self, context):
        try:
            print("[Warning] gltf called")
            import_gltf(self.filepath)
            self.report({'INFO'}, f"Imported {self.filepath}")
        except Exception as e:
            self.report({'ERROR'}, f"Failed to import {self.filepath}: {e}")
        return {'FINISHED'}

#Import USD Operator 
class WM_OT_import_usd(bpy.types.Operator):
    bl_label = "Import usd"
    bl_idname = "wm.import_usd"
    filepath: bpy.props.StringProperty()

    def execute(self, context):
        try:
            print("[Warning] usd called")
            import_usd(self.filepath)
            self.report({'INFO'}, f"Imported {self.filepath}")
        except Exception as e:
            self.report({'ERROR'}, f"Failed to import {self.filepath}: {e}")
        return {'FINISHED'}

#Import HDRI Operator
class WM_OT_import_hdri(bpy.types.Operator):
    bl_label = "Import HDRI"
    bl_idname = "wm.import_hdri"
    filepath: bpy.props.StringProperty()

    def execute(self, context):
        try:
            import_hdri(self.filepath)
            self.report({'INFO'}, f"Imported {self.filepath}")
        except Exception as e:
            self.report({'ERROR'}, f"Failed to import {self.filepath}: {e}")
        return {'FINISHED'}

# FilePath String Property for each Extension file.
class OBJFileProperty(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Name")
    filepath: bpy.props.StringProperty(name="Filepath")

class FBXFileProperty(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Name")
    filepath: bpy.props.StringProperty(name="Filepath")
    
class GLTFFileProperty(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Name")
    filepath: bpy.props.StringProperty(name="Filepath")

class USDFileProperty(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Name")
    filepath: bpy.props.StringProperty(name="Filepath")

class HDRIFileProperty(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Name")
    filepath: bpy.props.StringProperty(name="Filepath")

# Base Import Panel
class BaseImportPanel:
    bl_label = "Imports"
    bl_category = "Import Panel"
    
    def draw(self, context):

        layout = self.layout
        layout.operator('wm.refresh_imports', text='Refresh')

        row = layout.row()
        row.alignment = 'RIGHT'
        row.prop(context.scene, "delete_archive", text="Delete Archive")

        # Create a collapsible layout for FBX
        fbx_col = layout.column(align=True)
        row = fbx_col.row()
        row.prop(context.scene, "fbx_expand", icon="DOWNARROW_HLT" if context.scene.fbx_expand else "RIGHTARROW", icon_only=True, emboss=False)
        row.label(text="FBX")
        if context.scene.fbx_expand:
            for fbx_file in context.scene.fbx_files:
                layout.operator('wm.import_fbx', text=fbx_file.name).filepath = fbx_file.filepath
        
        # Create a collapsible layout for OBJ
        obj_col = layout.column(align=True)
        row = obj_col.row()
        row.prop(context.scene, "obj_expand", icon="DOWNARROW_HLT" if context.scene.obj_expand else "RIGHTARROW", icon_only=True, emboss=False)
        row.label(text="OBJ")
        if context.scene.obj_expand:
            for obj_file in context.scene.obj_files:
                layout.operator('wm.import_obj', text=obj_file.name).filepath = obj_file.filepath

        # Create a collapsible layout for GLTF/GLB
        gltf_col = layout.column(align=True)
        row = gltf_col.row()
        row.prop(context.scene, "gltf_expand", icon="DOWNARROW_HLT" if context.scene.gltf_expand else "RIGHTARROW", icon_only=True, emboss=False)
        row.label(text="GLTF/GLB")
        if context.scene.gltf_expand:
            for gltf_file in context.scene.gltf_files:
                layout.operator('wm.import_gltf', text=gltf_file.name).filepath = gltf_file.filepath

        # Create a collapsible layout for USDZ
        usdz_col = layout.column(align=True)
        row = usdz_col.row()
        row.prop(context.scene, "usdz_expand", icon="DOWNARROW_HLT" if context.scene.usdz_expand else "RIGHTARROW", icon_only=True, emboss=False)
        row.label(text="USD")
        if context.scene.usdz_expand:
            for usd_file in context.scene.usd_files:
                layout.operator('wm.import_usd', text=usd_file.name).filepath = usd_file.filepath

        # Create a collapsible layout for HDRI
        hdri_col = layout.column(align=True)
        row = hdri_col.row()
        row.prop(context.scene, "hdri_expand", icon="DOWNARROW_HLT" if context.scene.hdri_expand else "RIGHTARROW", icon_only=True, emboss=False)
        row.label(text="HDRI")
        if context.scene.hdri_expand:
            for hdri_file in context.scene.hdri_files:
                layout.operator('wm.import_hdri', text=hdri_file.name).filepath = hdri_file.filepath

class PipelinerProperties(bpy.types.PropertyGroup):
    base_dir: bpy.props.StringProperty(name="Base Directory", subtype='DIR_PATH', update=lambda s, c: s.update_paths())
    project_name: bpy.props.StringProperty(name="Project Name", update=lambda s, c: s.update_paths())
    file_name: bpy.props.StringProperty(name="File Name")
    custom_folder_1: bpy.props.StringProperty(name="Custom Folder 1", default="")
    custom_folder_2: bpy.props.StringProperty(name="Custom Folder 2", default="")
    
    # Checkbox options for folders
    create_reference: bpy.props.BoolProperty(name="Create Reference Folder", default=True)
    create_imports: bpy.props.BoolProperty(name="Create Imports Folder", default=True)
    create_hdri: bpy.props.BoolProperty(name="Create HDRI Folder", default=True)
    create_render: bpy.props.BoolProperty(name="Create Render Folder", default=True)
    pipeline_setup: bpy.props.BoolProperty(name="Pipeline Setup", default=False)

    # Paths
    base_dir_path: bpy.props.StringProperty(name="Base Directory Path", default="")
    reference_path: bpy.props.StringProperty(name="Reference Path", default="")
    hdri_path: bpy.props.StringProperty(name="HDRI Path", default="")
    imports_path: bpy.props.StringProperty(name="Imports Path", default="")
    render_path: bpy.props.StringProperty(name="Render Path", default="")
    vcs_path: bpy.props.StringProperty(name="VCS Path", default="")
    version_history_file: bpy.props.StringProperty(name="Version History File", default="")
    vcs_head : bpy.props.StringProperty(name="VCS Head", default="")

    def update_paths(self):
        if self.base_dir and self.project_name:
            self.base_dir_path = os.path.join(self.base_dir, self.project_name)
            self.reference_path = os.path.join(self.base_dir_path, "Reference")
            self.hdri_path = os.path.join(self.base_dir_path, "HDRI")
            self.imports_path = os.path.join(self.base_dir_path, "Imports")
            self.render_path = os.path.join(self.base_dir_path, "Render")
            self.vcs_path = os.path.join(self.base_dir_path, "vcs")

################################################################
# Main Panel
class PipelinerPanel(bpy.types.Panel):
    bl_idname = "PIPELINER_PT_panel"
    bl_label = "Pipeliner"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Pipeliner"

    def draw(self, context):
        layout = self.layout
        pipeliner_props = context.scene.pipeliner

        if pipeliner_props.pipeline_setup:
            layout.label(text="Pipeline has been set up")

            #  import panel code
            import_col = layout.column(align=True)
            row = import_col.row()
            row.prop(context.scene,"import_expand",icon="DOWNARROW_HLT" if context.scene.import_expand else "RIGHTARROW", icon_only=True, emboss=False)
            row.label(text="Imports")
            if context.scene.import_expand:         
                BaseImportPanel.draw(self,context)

            # pure ref panel
            refrence_col = layout.column(align=True)
            row = refrence_col.row()
            row.prop(context.scene,"refrence_expand",icon="DOWNARROW_HLT" if context.scene.refrence_expand else "RIGHTARROW", icon_only=True, emboss=False)
            row.label(text="Refrences")
            if context.scene.refrence_expand:
                # List all .pur files in the folder
                if os.path.exists(context.scene.pipeliner.reference_path):
                    for file_name in os.listdir(context.scene.pipeliner.reference_path):
                        if file_name.endswith(".pur"):
                            row = layout.row()
                            operator = row.operator("pure_ref.open_ref", text=file_name)
                            operator.file_path = os.path.join(context.scene.pipeliner.reference_path, file_name)

                # Create Ref button at the bottom
                row = layout.row()
                row.operator("pure_ref.create_ref", text="Create Ref")

            #Render Panel
            render_col = layout.column(align=True)
            row = render_col.row()
            row.prop(context.scene,"render_expand",icon="DOWNARROW_HLT" if context.scene.render_expand else "RIGHTARROW", icon_only=True, emboss=False)
            row.label(text="Render")
            if context.scene.render_expand:
                layout.operator("render.setup_pipeline", text="Setup Render Passes")
                layout.operator("render.setup_comp", text="Setup Composition")



        else:
            layout.operator("pipeliner.setup_pipeline", text="Setup Pipeline")

class SetupPipelineOperator(bpy.types.Operator):
    bl_idname = "pipeliner.setup_pipeline"
    bl_label = "Setup Pipeline"

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        pipeliner_props = context.scene.pipeliner

        if not pipeliner_props.base_dir or not pipeliner_props.project_name or not pipeliner_props.file_name:
            self.report({'ERROR'}, "Please provide all fields.")
            return {'CANCELLED'}
        
        pipeliner_props.base_dir_path = os.path.abspath(pipeliner_props.base_dir)

        # Create the main project folder
        os.makedirs(pipeliner_props.base_dir_path, exist_ok=True)

        # Create specified folders
        if pipeliner_props.create_reference:
            os.makedirs(pipeliner_props.reference_path, exist_ok=True)

        if pipeliner_props.create_hdri:
            os.makedirs(pipeliner_props.hdri_path, exist_ok=True)
        
        if pipeliner_props.create_imports:
            os.makedirs(pipeliner_props.imports_path, exist_ok=True)
            
            # creating Imports folder subfolder
            os.makedirs(os.path.join(pipeliner_props.imports_path, "FBX"), exist_ok=True)
            os.makedirs(os.path.join(pipeliner_props.imports_path, "OBJ"), exist_ok=True)
            os.makedirs(os.path.join(pipeliner_props.imports_path, "GLTF"), exist_ok=True)
            os.makedirs(os.path.join(pipeliner_props.imports_path, "USD"), exist_ok=True)
            

        if pipeliner_props.create_render:
            os.makedirs(pipeliner_props.render_path, exist_ok=True)
            context.scene.render.filepath = pipeliner_props.render_path

        # creating vcs path
        os.makedirs(pipeliner_props.vcs_path, exist_ok=True)
        pipeliner_props.version_history_file = os.path.join(pipeliner_props.vcs_path, "version_history.json")

        # Create custom folders
        if pipeliner_props.custom_folder_1:
            os.makedirs(os.path.join(pipeliner_props.base_dir_path, pipeliner_props.custom_folder_1), exist_ok=True)
        
        if pipeliner_props.custom_folder_2:
            os.makedirs(os.path.join(pipeliner_props.base_dir_path, pipeliner_props.custom_folder_2), exist_ok=True)

        # Save the current Blender file in the specified directory
        blend_file_path = os.path.join(pipeliner_props.base_dir_path,pipeliner_props.project_name, f"{pipeliner_props.file_name}.blend")
        bpy.ops.wm.save_as_mainfile(filepath=blend_file_path)
        # setting up vcs head
        pipeliner_props.vcs_head = blend_file_path

        # Set the pipeline_setup flag to True
        pipeliner_props.pipeline_setup = True

        self.report({'INFO'}, "Pipeline setup complete.")
        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        pipeliner_props = context.scene.pipeliner

        layout.prop(pipeliner_props, "base_dir")
        layout.prop(pipeliner_props, "project_name")
        layout.prop(pipeliner_props, "file_name")

        layout.separator()

        layout.prop(pipeliner_props, "create_reference")
        layout.prop(pipeliner_props, "create_imports")
        layout.prop(pipeliner_props, "create_hdri")
        layout.prop(pipeliner_props, "create_render")

        layout.separator()

        layout.prop(pipeliner_props, "custom_folder_1")
        layout.prop(pipeliner_props, "custom_folder_2")

# Collections Import Panel
class IMPORT_PT_main_panel(BaseImportPanel,bpy.types.Panel):
    bl_idname = "IMPORT_PT_main_panel"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "collection"

# pureref code
class PURE_REF_OT_OpenRef(bpy.types.Operator):
    bl_idname = "pure_ref.open_ref"
    bl_label = "Open PureRef File"

    file_path: bpy.props.StringProperty()

    def execute(self, context):
        if os.path.exists(self.file_path):
            os.startfile(self.file_path)  # For Windows
            # subprocess.call(('xdg-open', self.file_path))  # For Linux
            # subprocess.call(('open', self.file_path))  # For MacOS
            self.report({'INFO'}, f"Opened PureRef File: {self.file_path}")
        else:
            self.report({'ERROR'}, "File not found")
        return {'FINISHED'}


class PURE_REF_OT_CreateRef(bpy.types.Operator):
    bl_idname = "pure_ref.create_ref"
    bl_label = "Create PureRef File"

    def execute(self, context):
        pureref_executable = context.scene.pure_ref_executable
        try:
            if not os.path.exists(pureref_executable):
                raise FileNotFoundError
            subprocess.Popen([pureref_executable])
            self.report({'INFO'}, "Opened PureRef application for new file")
        except FileNotFoundError:
            self.report({'ERROR'}, "PureRef executable not found. Please ensure PureRef is installed and the path is configured correctly.")
            bpy.ops.pure_ref.configure_path('INVOKE_DEFAULT')
        except Exception as e:
            self.report({'ERROR'}, f"An error occurred while trying to open PureRef: {str(e)}")
        return {'FINISHED'}


class PURE_REF_OT_ConfigurePath(bpy.types.Operator):
    bl_idname = "pure_ref.configure_path"
    bl_label = "Configure PureRef Path"

    directory: bpy.props.StringProperty(subtype='DIR_PATH')

    def execute(self, context):
        context.scene.pure_ref_executable = os.path.join(self.directory, "PureRef.exe")
        self.report({'INFO'}, f"PureRef path set to: {context.scene.pure_ref_executable}")
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

# Rendering pipeline code
class RENDER_OT_SetupPipeline(bpy.types.Operator):
    bl_idname = "render.setup_pipeline"
    bl_label = "Setup Render Pipeline"

    diffuse: bpy.props.BoolProperty(name="Diffuse")
    glossy: bpy.props.BoolProperty(name="Specular")
    transmission: bpy.props.BoolProperty(name="Transmission")
    volume: bpy.props.BoolProperty(name="Volume")
    emission: bpy.props.BoolProperty(name="Emission")
    environment: bpy.props.BoolProperty(name="Environment")
    output_folder: bpy.props.StringProperty(name="Output Folder", subtype='DIR_PATH')

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.label(text="Select Passes you want:")

        layout.prop(self, "diffuse")
        layout.prop(self, "glossy")
        
        if context.scene.render.engine == 'CYCLES':
            layout.prop(self, "transmission")

        # layout.prop(self, "volume")    
        layout.prop(self, "emission")
        layout.prop(self, "environment")

        layout.prop(self, "output_folder")

    def execute(self, context):
        scene = context.scene
        scene.use_nodes = True
        tree = scene.node_tree

        # Clear default nodes
        for node in tree.nodes:
            tree.nodes.remove(node)

        # Add Render Layers node
        render_layers = tree.nodes.new(type='CompositorNodeRLayers')
        render_layers.location = (0, 0)

        # Add File Output node
        file_output = tree.nodes.new(type='CompositorNodeOutputFile')
        file_output.base_path = bpy.path.abspath(self.output_folder)
        file_output.format.file_format = 'OPEN_EXR_MULTILAYER'
        file_output.location = (300, 0)

        # Set up passes
        passes = None
        if context.scene.render.engine == 'CYCLES':
            passes = {
                "diffuse": ["diffuse_direct", "diffuse_indirect", "diffuse_color"],
                "glossy": ["glossy_direct", "glossy_indirect", "glossy_color"],
                "transmission": ["transmission_direct", "transmission_indirect", "transmission_color"],
                # "volume": ["volume_direct", "volume_indirect"],
                "emission": ["emit"],
                "environment": ["environment"]
            }
        else:
            passes = {
                "diffuse": ["diffuse_direct", "diffuse_color"],
                "glossy": ["glossy_direct", "glossy_color"],
                "transmission": [],
                "emission": ["emit"],
                "environment": ["environment"]
            }

        output_Name = {"diffuse_direct" : "DiffDir", 
                       "diffuse_indirect" : "DiffInd",
                       "diffuse_color" : "DiffCol",
                       "glossy_direct" : "GlossDir", 
                       "glossy_indirect" : "GlossInd", 
                       "glossy_color" : "GlossCol",
                       "transmission_direct" : "TransDir", 
                       "transmission_indirect" : "TransInd", 
                       "transmission_color" : "TransCol",
                       "emit" : "Emit",
                       "environment" : "Env"
                        }

        selected_passes = []
        if self.diffuse: selected_passes.extend(passes["diffuse"])
        if self.glossy: selected_passes.extend(passes["glossy"])
        if self.transmission: selected_passes.extend(passes["transmission"])
        if self.emission: selected_passes.extend(passes["emission"])
        if self.environment: selected_passes.extend(passes["environment"])

        # Enable selected passes in the active view layer
        view_layer = bpy.context.view_layer
        for p in selected_passes:
            setattr(view_layer, f"use_pass_{p}", True)

        # Create outputs for each pass
        for p in selected_passes:
            file_output.file_slots.new(name=p)
            tree.links.new(render_layers.outputs[output_Name[p]], file_output.inputs[p])

        # linking image node
        tree.links.new(render_layers.outputs["Image"],file_output.inputs["Image"])

        context.window.workspace = bpy.data.workspaces['Compositing']

        self.report({'INFO'}, "Render Pipeline Setup Complete")
        return {'FINISHED'}

class RENDER_OT_SetupComp(bpy.types.Operator):
    bl_idname = "render.setup_comp"
    bl_label = "Setup Comp"

    input_folder: bpy.props.StringProperty(name="Input File Dir", subtype='DIR_PATH')
    output_folder: bpy.props.StringProperty(name="Output Folder", subtype='DIR_PATH')

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "input_folder")
        layout.prop(self, "output_folder")

    def execute(self, context):
        self.input_folder = bpy.path.abspath(self.input_folder)
        self.output_folder = bpy.path.abspath(self.output_folder)

        # Verify the input directory
        if not os.path.exists(self.input_folder):
            self.report({'ERROR'}, "Input directory does not exist")
            return {'CANCELLED'}
        
        # Verify the output directory
        if not os.path.exists(self.output_folder):
            self.report({'ERROR'}, "Output directory does not exist")
            return {'CANCELLED'}

        # # Get list of .exr files
        # exr_files = sorted([f for f in os.listdir(self.input_folder) if f.endswith('.exr')])

        # if not exr_files:
        #     self.report({'ERROR'}, "No .exr files found in the input directory")
        #     return {'CANCELLED'}

        # Ensure nodes are enabled
        scene = context.scene
        scene.use_nodes = True
        tree = scene.node_tree

        
        # Clear default nodes
        for node in tree.nodes:
            tree.nodes.remove(node)

        # Get the first .exr file in the input folder
        exr_file = None
        for file in os.listdir(self.input_folder):
            if file.endswith(".exr"):
                exr_file = os.path.join(self.input_folder, file)
                break
            
        # exr_files = []

        # # Iterate through the files in the base folder
        # for file in os.listdir(self.input_folder):
        #     if file.endswith(".exr"):
        #         exr_files.append(os.path.join(self.input_folder, file))

        # # Sort the files to maintain order (optional)
        # exr_files.sort()

        # Check if we found any EXR files
        if not exr_file:
            self.report({'ERROR'}, "No .exr files found in the input directory")
            return {'CANCELLED'}
        
        # Create a new image node in the Compositing Nodes
        comp_nodes = bpy.context.scene.node_tree.nodes
        image_node = comp_nodes.new("CompositorNodeImage")

        # Load the first image to create the image data block
        # image_node.image = bpy.data.images.load(exr_files[0])
        image_node.image = bpy.data.images.load(exr_file)

        # Set the image node properties for the image sequence
        # image_node.image.use_sequence = True

        # image_node.image.source = 'SEQUENCE'
        
        # image_node.image.frame_duration = len(exr_files)

        # Set the paths for the image sequence
        # for i, exr_file in enumerate(exr_files):
        #     # Load each image and set it in the sequence
        #     img = bpy.data.images.load(exr_file)
        #     img.name = f"Image_{i:03d}"  # Give a unique name to each image
        #     image_node.image.sequence[0].image = img  # Assign the image to the sequence

        # Set the image node location
        image_node.location = (-300, 200)
        # image_node.select = True

        # for indirect passes.
        if ("diffuse_indirect" in image_node.outputs) or ("glossy_indirect" in image_node.outputs):
            previous_output_pointer = None
            location_var = [200,200]
            location_var_adder = [400,150]

            if "diffuse_indirect" in image_node.outputs:
                # creating multiply node
                multiply_diffuse_passes = tree.nodes.new(type="CompositorNodeMixRGB")
                multiply_diffuse_passes.blend_type = "MULTIPLY"
                multiply_diffuse_passes.location = location_var
                location_var[1] -= 200

                #connecting multiply node
                tree.links.new(image_node.outputs['diffuse_indirect'],multiply_diffuse_passes.inputs[1])
                tree.links.new(image_node.outputs['diffuse_direct'],multiply_diffuse_passes.inputs[2])

                # creating add node
                add_diffuse_passes = tree.nodes.new(type="CompositorNodeMixRGB")
                add_diffuse_passes.blend_type = "ADD"
                add_diffuse_passes.location = location_var_adder
                location_var_adder[0] += 200
                location_var_adder[1] -= 150
                
                #connecting nodes
                tree.links.new(multiply_diffuse_passes.outputs[0], add_diffuse_passes.inputs[1])
                tree.links.new(image_node.outputs['diffuse_color'], add_diffuse_passes.inputs[2])

                previous_output_pointer = add_diffuse_passes

            if "glossy_direct" in image_node.outputs:
                # creating multiply node
                multiply_glossy_passes = tree.nodes.new(type="CompositorNodeMixRGB")
                multiply_glossy_passes.blend_type = "MULTIPLY"
                multiply_glossy_passes.location = location_var
                location_var[1] -= 200

                #connecting multiply node
                tree.links.new(image_node.outputs['glossy_indirect'],multiply_glossy_passes.inputs[1])
                tree.links.new(image_node.outputs['glossy_direct'],multiply_glossy_passes.inputs[2])

                # creating add node
                add_glossy_passes = tree.nodes.new(type="CompositorNodeMixRGB")
                add_glossy_passes.blend_type = "ADD"
                add_glossy_passes.location = location_var_adder
                location_var_adder[0] += 200
                location_var_adder[1] -= 150
                
                #connecting nodes
                tree.links.new(multiply_glossy_passes.outputs[0], add_glossy_passes.inputs[1])
                tree.links.new(image_node.outputs['glossy_color'], add_glossy_passes.inputs[2])

                #connecting to add node
                add_result = tree.nodes.new(type="CompositorNodeMixRGB")
                add_result.blend_type = "ADD"
                add_result.location = location_var_adder
                location_var_adder[0] += 200
                location_var_adder[1] -= 150

                tree.links.new(previous_output_pointer.outputs[0],add_result.inputs[1])
                tree.links.new(add_glossy_passes.outputs[0],add_result.inputs[2])

                previous_output_pointer = add_result

            if "emit" in image_node.outputs:
                #creating add node
                add_emit_pass = tree.nodes.new(type="CompositorNodeMixRGB")
                add_emit_pass.blend_type = "ADD"
                add_emit_pass.location = location_var_adder
                location_var_adder[0] += 200
                location_var_adder[1] -= 150
                #connecting node
                tree.links.new(previous_output_pointer.outputs[0],add_emit_pass.inputs[1])
                tree.links.new(image_node.outputs['emit'],add_emit_pass.inputs[2])
                
                previous_output_pointer = add_emit_pass

            if "environment" in image_node.outputs:
                #creating add node
                add_env_pass = tree.nodes.new(type="CompositorNodeMixRGB")
                add_env_pass.blend_type = "ADD"
                add_env_pass.location = location_var_adder
                location_var_adder[0] += 200
                location_var_adder[1] -= 150
                #connecting node
                tree.links.new(previous_output_pointer.outputs[0],add_env_pass.inputs[1])
                tree.links.new(image_node.outputs['environment'],add_env_pass.inputs[2])
                
                previous_output_pointer = add_env_pass

            #connecting final node to compositior

            # Add a Composite node to output the result
            composite_node = tree.nodes.new(type='CompositorNodeComposite')
            composite_node.location = (location_var_adder[0],200)
            # Connect the Multiply node output to the Composite node
            tree.links.new(previous_output_pointer.outputs[0], composite_node.inputs[0])

            # Adding viewer Node
            viewer_node = tree.nodes.new(type='CompositorNodeViewer')
            viewer_node.location = (location_var_adder[0],0)
            # connecting nodes
            tree.links.new(previous_output_pointer.outputs[0],viewer_node.inputs[0])

            
            print("CYCLES RENDER COMP")
        else:
            previous_output_pointer = None
            location_var = [200,200]
            location_var_adder = [400,150]

            if "diffuse_direct" in image_node.outputs:
                # creating add node
                add_diffuse_passes = tree.nodes.new(type="CompositorNodeMixRGB")
                add_diffuse_passes.blend_type = "ADD"
                add_diffuse_passes.location = location_var
                location_var[1] -= 200
                
                #connecting nodes
                tree.links.new(image_node.outputs['diffuse_direct'], add_diffuse_passes.inputs[1])
                tree.links.new(image_node.outputs['diffuse_color'], add_diffuse_passes.inputs[2])

                previous_output_pointer = add_diffuse_passes

            if "glossy_direct" in image_node.outputs:
                # creating add node
                add_glossy_passes = tree.nodes.new(type="CompositorNodeMixRGB")
                add_glossy_passes.blend_type = "ADD"
                add_glossy_passes.location = location_var
                location_var[0] -= 200
                
                #connecting nodes
                tree.links.new(image_node.outputs['glossy_direct'], add_glossy_passes.inputs[1])
                tree.links.new(image_node.outputs['glossy_color'], add_glossy_passes.inputs[2])

                #connecting to add node
                add_result = tree.nodes.new(type="CompositorNodeMixRGB")
                add_result.blend_type = "ADD"
                add_result.location = location_var_adder
                location_var_adder[0] += 200
                location_var_adder[1] -= 150

                tree.links.new(previous_output_pointer.outputs[0],add_result.inputs[1])
                tree.links.new(add_glossy_passes.outputs[0],add_result.inputs[2])

                previous_output_pointer = add_result

            if "emit" in image_node.outputs:
                #creating add node
                add_emit_pass = tree.nodes.new(type="CompositorNodeMixRGB")
                add_emit_pass.blend_type = "ADD"
                add_emit_pass.location = location_var_adder
                location_var_adder[0] += 200
                location_var_adder[1] -= 150
                #connecting node
                tree.links.new(previous_output_pointer.outputs[0],add_emit_pass.inputs[1])
                tree.links.new(image_node.outputs['emit'],add_emit_pass.inputs[2])
                
                previous_output_pointer = add_emit_pass

            if "environment" in image_node.outputs:
                #creating add node
                add_env_pass = tree.nodes.new(type="CompositorNodeMixRGB")
                add_env_pass.blend_type = "ADD"
                add_env_pass.location = location_var_adder
                location_var_adder[0] += 200
                location_var_adder[1] -= 150
                #connecting node
                tree.links.new(previous_output_pointer.outputs[0],add_env_pass.inputs[1])
                tree.links.new(image_node.outputs['environment'],add_env_pass.inputs[2])
                
                previous_output_pointer = add_env_pass


            #connecting final node to compositior

            # Add a Composite node to output the result
            composite_node = tree.nodes.new(type='CompositorNodeComposite')
            composite_node.location = (location_var_adder[0],200)
            # Connect the Multiply node output to the Composite node
            tree.links.new(previous_output_pointer.outputs[0], composite_node.inputs[0])

            # Adding viewer Node
            viewer_node = tree.nodes.new(type='CompositorNodeViewer')
            viewer_node.location = (location_var_adder[0],0)
            # connecting nodes
            tree.links.new(previous_output_pointer.outputs[0],viewer_node.inputs[0])
            
            print("eevee render comp")

        # Switch to Compositing workspace
        context.window.workspace = bpy.data.workspaces['Compositing']
        context.space_data.show_backdrop = False


        # # Clear default nodes
        # for node in tree.nodes:
        #     tree.nodes.remove(node)

        # # Add Image node for the sequence
        # image_node = tree.nodes.new(type='CompositorNodeImage')
        # image_node.location = (0, 0)
        
        #  # Load images as a sequence
        # image_node.image = bpy.data.images.load(os.path.join(self.input_folder, exr_files[0]), check_existing=True)
        # image_node.image.source = 'SEQUENCE'
        # image_node.image.filepath = os.path.join(self.input_folder, exr_files[0])
        # # image_node.image.frame_start = 1

        # # Set the sequence length and frame rate
        # # image_node.image.frame_duration = len(exr_files)
        # # image_node.image.fps = 24

        # # Add a Composite node and link it to the Image node
        # composite_node = tree.nodes.new(type='CompositorNodeComposite')
        # composite_node.location = (300, 0)
        # tree.links.new(image_node.outputs['Image'], composite_node.inputs['Image'])

        self.report({'INFO'}, "Composition Setup Complete")
        return {'FINISHED'}

# todo panel code
class ToDoItem(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="ToDo")
    completed: bpy.props.BoolProperty(name="Completed", default=False)

class BaseToDoListPanel:
    bl_label = "ToDo List"
    bl_category = 'ToDo List'
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        todo_list = scene.todo_list
        
        row = layout.row()
        row.prop(scene, "new_todo", text="")
        row.operator("todo_list.add_item", text="Add")
        
        for i, item in enumerate(todo_list):
            row = layout.row()
            row.prop(item, "completed", text="")
            row.prop(item, "name", text="")
            row.operator("todo_list.remove_item", text="", icon='X').index = i

class VIEW3D_PT_todo_list(BaseToDoListPanel, bpy.types.Panel):
    bl_idname = "VIEW3D_PT_todo_list"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'

class TEXTEDITOR_PT_todo_list(BaseToDoListPanel, bpy.types.Panel):
    # bl_idname = "TEXTEDITOR_PT_todo_list"
    # bl_space_type = 'TEXT_EDITOR'
    # bl_region_type = 'UI'
    bl_idname = "TEXTEDITOR_PT_todo_list"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "collection"

class AddToDoItem(bpy.types.Operator):
    bl_idname = "todo_list.add_item"
    bl_label = "Add ToDo Item"
    
    def execute(self, context):
        if context.scene.new_todo.strip():
            scene = context.scene
            new_item = scene.todo_list.add()
            new_item.name = scene.new_todo
            scene.new_todo = ""
            return {'FINISHED'}
        return {'PASS_THROUGH'}

class RemoveToDoItem(bpy.types.Operator):
    bl_idname = "todo_list.remove_item"
    bl_label = "Remove ToDo Item"
    
    index: bpy.props.IntProperty()
    
    def execute(self, context):
        scene = context.scene
        scene.todo_list.remove(self.index)
        return {'FINISHED'}
    
# vcs addition ->  -----------------------------------------


def load_version_history(context):
    """Load version history from the JSON file."""
    version_history_file = context.scene.pipeliner.version_history_file

    if os.path.exists(version_history_file):
        with open(version_history_file, 'r') as file:
            return json.load(file)
    else:
        return []


def save_version_history(history,context):
    """Save the updated version history to the JSON file."""
    version_history_file = context.scene.pipeliner.version_history_file

    if os.path.exists(version_history_file):
        with open(version_history_file, 'w') as file:
            json.dump(history, file, indent=4)
    else:
        context.scene.pipeliner.version_history_file = os.path.join(context.scene.pipeliner.vcs_path,"version_history.json")
        version_history_file = context.scene.pipeliner.version_history_file

        with open(version_history_file, 'w') as file:
            json.dump([], file)  # Create an empty list in the file
        with open(version_history_file, 'w') as file:
            json.dump(history, file, indent=4)


class VCS_PT_panel(bpy.types.Panel):
    """Creates a panel in the 3D View for version control"""
    bl_label = "Version Control System"
    bl_idname = "VCS_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'VCS'

    def draw(self, context):
        layout = self.layout

        # Buttons for commit and set as current version
        row = layout.row()
        row.operator("vcs.commit_version", text="Commit Version",icon='SORT_DESC')

        row = layout.row()
        row.operator("vcs.set_as_current_version", text="Set as Current Version",icon='DOWNARROW_HLT')

        # Reverting to the current version main file.
        if context.scene.pipeliner.vcs_head: 
            layout.label(text="Main File:")
            row = layout.row()
            row.operator("vcs.open_main_file", text="Main Blend File",icon='FILE_REFRESH')

        # List all commits with buttons
        layout.label(text="All Commits:")
        version_history = load_version_history(context)

        if version_history:
            for version_data in version_history:
                row = layout.row()
                row.operator("vcs.load_version", text=version_data["version_name"],icon='LOOP_BACK').version_name = version_data["version_name"]
        else:
            layout.label(text="No version commits found.")

class VCS_OT_open_main_file(bpy.types.Operator):
    bl_idname = "vcs.open_main_file"
    bl_label = "Open Main File"

    def execute(self,context):
        bpy.ops.wm.save_mainfile()
        bpy.ops.wm.open_mainfile(filepath=context.scene.pipeliner.vcs_head)
        self.report({'INFO'}, f"Main File '{context.scene.pipeliner.vcs_head}' opened successfully")
        return {'FINISHED'}


class VCS_OT_commit_version(bpy.types.Operator):
    """Operator to commit the current version"""
    bl_idname = "vcs.commit_version"
    bl_label = "Commit Version"

    # Properties for version name and description
    version_name: bpy.props.StringProperty(name="Version Name", default="v1")
    version_description: bpy.props.StringProperty(name="Description", default="")

    def invoke(self, context, event):
        # Open a popup to get version name and description
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        vcs_path = context.scene.pipeliner.vcs_path
        vcs_head = context.scene.pipeliner.vcs_head

        # logic for not having the vcs_head set 
        if not vcs_head and not vcs_path:
            current_file_path = bpy.data.filepath

            # case in which the file is not saved
            if not current_file_path:
                self.report({'WARNING'}, "The current file has not been saved yet. Please save the file first.")
                return {'CANCELLED'}


            context.scene.pipeliner.vcs_head = bpy.data.filepath
            self.report({'INFO'}, f"saving current file as vcs head")

            # Get the directory of the current file
            current_directory = os.path.dirname(current_file_path)

            # Create a 'vcs' folder in the current file's directory
            vcs_directory = os.path.join(current_directory, "vcs")
            os.makedirs(vcs_directory, exist_ok=True)  # Create the 'vcs' directory if it doesn't exist

            # Set the VCS path and head in the Blender scene properties
            context.scene.pipeliner.vcs_path = vcs_directory
            context.scene.pipeliner.vcs_head = current_file_path

            vcs_path = vcs_directory
            vcs_head = current_file_path
            # saving version history file
            # context.scene.pipeliner.version_history_file = os.path.join(vcs_path,"version_history.json")

            # Report success message
            self.report({'INFO'}, f"VCS initialized. VCS head set to '{context.scene.pipeliner.vcs_head}' and VCS path set to '{vcs_directory}'.")
        
        # logic if vcs head is there but not the vcs director
        if vcs_head and not vcs_path:
            current_directory = os.path.dirname(context.scene.pipeliner.vcs_head)

            # Create a 'vcs' folder in the current file's directory
            vcs_directory = os.path.join(current_directory, "vcs")
            os.makedirs(vcs_directory, exist_ok=True)  # Create the 'vcs' directory if it doesn't exist

            # Set the VCS path and head in the Blender scene properties
            context.scene.pipeliner.vcs_path = vcs_directory

        

        # Create a dictionary to hold version information
        version_data = {
            "version_name": self.version_name,
            "description": self.version_description,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "filePath": os.path.join(vcs_path,self.version_name)
        }

        # Save the version data to the JSON file
        version_history = load_version_history(context)
        version_history.append(version_data)
        save_version_history(version_history,context)

        # Save a copy of the current file as a new version in the commit directory
        blend_file_path = os.path.join(vcs_path, f"{self.version_name}.blend")
        
        # Use `bpy.ops.wm.save_as_mainfile` with `copy=True` to save a copy without changing the currently open file
        bpy.ops.wm.save_as_mainfile(filepath=blend_file_path, copy=True)

        self.report({'INFO'}, f"Version '{self.version_name}' committed successfully.")
        return {'FINISHED'}


class VCS_OT_set_as_current_version(bpy.types.Operator):
    """Operator to set a commit version as the current .blend file"""
    bl_idname = "vcs.set_as_current_version"
    bl_label = "Set as Current Version"

    def execute(self, context):
        # Get the paths for the VCS directory and the VCS head (main file)
        vcs_head = context.scene.pipeliner.vcs_head  # Path to the main .blend file (vcs_head)

        # Check if the VCS head path is valid
        if not os.path.exists(vcs_head):
            current_file_path = bpy.data.filepath
            if not current_file_path:
                self.report({'WARNING'}, "The current file has not been saved yet. Please save the file first.")
                return {'CANCELLED'}

            context.scene.pipeliner.vcs_head = bpy.data.filepath
            self.report({'WARNING'}, f"VCS head file not found, making current file as vcs head")
    
            return {'FINISHED'}

        # Save the currently open .blend file as the main file (vcs_head) without changing its name
        try:
            bpy.ops.wm.save_as_mainfile(filepath=vcs_head)
            self.report({'INFO'}, f"Current file saved as '{vcs_head}' successfully.")
        except Exception as e:
            self.report({'ERROR'}, f"Failed to save the current file as '{vcs_head}': {str(e)}")
            return {'CANCELLED'}

        return {'FINISHED'}


class VCS_OT_load_version(bpy.types.Operator):
    """Operator to load a specific version"""
    bl_idname = "vcs.load_version"
    bl_label = "Load Version"

    version_name: bpy.props.StringProperty()

    def execute(self, context):
        vcs_path = context.scene.pipeliner.vcs_path

        # Save the current .blend file before switching
        bpy.ops.wm.save_as_mainfile()

        # Load the selected version
        blend_file_path = os.path.join(vcs_path, f"{self.version_name}.blend")
        bpy.ops.wm.open_mainfile(filepath=blend_file_path)

        self.report({'INFO'}, f"Switched to version '{self.version_name}'.")
        return {'FINISHED'}

def register():
    bpy.utils.register_class(PipelinerProperties)
    bpy.utils.register_class(PipelinerPanel)
    bpy.utils.register_class(SetupPipelineOperator)
    bpy.types.Scene.pipeliner = bpy.props.PointerProperty(type=PipelinerProperties)

    bpy.utils.register_class(IMPORT_PT_main_panel)

    bpy.utils.register_class(WM_OT_refresh_imports)
    bpy.utils.register_class(WM_OT_import_obj)
    bpy.utils.register_class(WM_OT_import_fbx)
    bpy.utils.register_class(WM_OT_import_gltf)
    bpy.utils.register_class(WM_OT_import_usd)
    bpy.utils.register_class(WM_OT_import_hdri)

    bpy.utils.register_class(FBXFileProperty)
    bpy.utils.register_class(OBJFileProperty)
    bpy.utils.register_class(GLTFFileProperty)
    bpy.utils.register_class(USDFileProperty)
    bpy.utils.register_class(HDRIFileProperty)
    
    bpy.types.Scene.fbx_expand = bpy.props.BoolProperty(name="Expand FBX", default=False)
    bpy.types.Scene.obj_expand = bpy.props.BoolProperty(name="Expand OBJ", default=False)
    bpy.types.Scene.gltf_expand = bpy.props.BoolProperty(name="Expand GLTF", default=False)
    bpy.types.Scene.usdz_expand = bpy.props.BoolProperty(name="Expand USD", default=False)
    bpy.types.Scene.hdri_expand = bpy.props.BoolProperty(name="Expand HDRI", default=False)
    bpy.types.Scene.import_expand = bpy.props.BoolProperty(name="Expand Import", default=False)
    bpy.types.Scene.refrence_expand = bpy.props.BoolProperty(name="Expand Refrence", default=False)
    bpy.types.Scene.render_expand = bpy.props.BoolProperty(name="Expand Render", default=False)

    bpy.types.Scene.fbx_files = bpy.props.CollectionProperty(type=FBXFileProperty)
    bpy.types.Scene.obj_files = bpy.props.CollectionProperty(type=OBJFileProperty)
    bpy.types.Scene.gltf_files = bpy.props.CollectionProperty(type=GLTFFileProperty)
    bpy.types.Scene.usd_files = bpy.props.CollectionProperty(type=USDFileProperty)
    bpy.types.Scene.hdri_files = bpy.props.CollectionProperty(type=HDRIFileProperty)
    
    bpy.types.Scene.delete_archive = bpy.props.BoolProperty(name="Delete Archive", default=False)

    # pureref
    bpy.utils.register_class(PURE_REF_OT_OpenRef)
    bpy.utils.register_class(PURE_REF_OT_CreateRef)
    bpy.utils.register_class(PURE_REF_OT_ConfigurePath)
    bpy.types.Scene.pure_ref_executable = bpy.props.StringProperty(
        name="PureRef Executable",
        description="Path to the PureRef executable",
        default="C:/Program Files/PureRef/PureRef.exe"
    )

    bpy.utils.register_class(RENDER_OT_SetupPipeline)
    bpy.utils.register_class(RENDER_OT_SetupComp)

    # todo
    bpy.utils.register_class(ToDoItem)
    bpy.utils.register_class(VIEW3D_PT_todo_list)
    bpy.utils.register_class(TEXTEDITOR_PT_todo_list)
    bpy.utils.register_class(AddToDoItem)
    bpy.utils.register_class(RemoveToDoItem)
    
    bpy.types.Scene.todo_list = bpy.props.CollectionProperty(type=ToDoItem)
    bpy.types.Scene.new_todo = bpy.props.StringProperty(name="New ToDo")

    bpy.utils.register_class(VCS_PT_panel)
    bpy.utils.register_class(VCS_OT_commit_version)
    bpy.utils.register_class(VCS_OT_set_as_current_version)
    bpy.utils.register_class(VCS_OT_load_version)
    bpy.utils.register_class(VCS_OT_open_main_file)



def unregister():
    bpy.utils.unregister_class(PipelinerProperties)
    bpy.utils.unregister_class(PipelinerPanel)
    bpy.utils.unregister_class(SetupPipelineOperator)
    del bpy.types.Scene.pipeliner

    bpy.utils.unregister_class(IMPORT_PT_main_panel)
    # bpy.utils.unregister_class(IMPORT_PT_3DVIEW_panel)

    bpy.utils.unregister_class(WM_OT_refresh_imports)
    bpy.utils.unregister_class(WM_OT_import_obj)
    bpy.utils.unregister_class(WM_OT_import_fbx)
    bpy.utils.unregister_class(WM_OT_import_gltf)
    bpy.utils.unregister_class(WM_OT_import_usd)
    bpy.utils.unregister_class(WM_OT_import_hdri)
    
    bpy.utils.unregister_class(FBXFileProperty)
    bpy.utils.unregister_class(OBJFileProperty)
    bpy.utils.unregister_class(GLTFFileProperty)
    bpy.utils.unregister_class(USDFileProperty)
    bpy.utils.unregister_class(HDRIFileProperty)

    bpy.utils.unregister_class(PURE_REF_OT_OpenRef)
    bpy.utils.unregister_class(PURE_REF_OT_CreateRef)
    bpy.utils.unregister_class(PURE_REF_OT_ConfigurePath)

    bpy.utils.unregister_class(RENDER_OT_SetupPipeline)
    bpy.utils.unregister_class(RENDER_OT_SetupComp)

    del bpy.types.Scene.pure_ref_executable

    del bpy.types.Scene.fbx_expand
    del bpy.types.Scene.obj_expand
    del bpy.types.Scene.fbx_files
    del bpy.types.Scene.obj_files
    del bpy.types.Scene.gltf_files
    del bpy.types.Scene.usd_files
    del bpy.types.Scene.hdri_expand
    del bpy.types.Scene.delete_archive
    del bpy.types.Scene.reference_expand
    del bpy.types.Scene.render_expand

    # todo
    bpy.utils.unregister_class(ToDoItem)
    bpy.utils.unregister_class(VIEW3D_PT_todo_list)
    bpy.utils.unregister_class(TEXTEDITOR_PT_todo_list)
    bpy.utils.unregister_class(AddToDoItem)
    bpy.utils.unregister_class(RemoveToDoItem)
    
    del bpy.types.Scene.todo_list
    del bpy.types.Scene.new_todo

    bpy.utils.unregister_class(VCS_PT_panel)
    bpy.utils.unregister_class(VCS_OT_commit_version)
    bpy.utils.unregister_class(VCS_OT_set_as_current_version)
    bpy.utils.unregister_class(VCS_OT_load_version)
    bpy.utils.unregister_class(VCS_OT_open_main_file)

if __name__ == "__main__":
    register()
