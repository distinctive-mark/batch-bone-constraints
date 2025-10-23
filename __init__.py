# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2025 deepseek
# -*- coding: utf-8 -*-

bl_info = {
    "name": "Batch Bone Constraints",
    "author": "distinctive-mark",
    "version": (1, 1, 2),
    "blender": (4, 2, 0),
    "location": "3D Viewport > Header > Batch Bone Constraints",
    "description": "Batch bone constraints to the selected multiple armatures",
    "category": "Rigging",
    "doc_url": "https://github.com/distinctive-mark/batch-bone-constraints",
    "tracker_url": "https://github.com/distinctive-mark/batch-bone-constraints/issues",
}

import bpy
from bpy.types import Operator, Menu
from bpy.props import EnumProperty
from bpy.app.translations import pgettext_iface as iface_
from bpy.app.translations import pgettext_tip as _

# Constraint type definitions
IMITATE_CONSTRAINTS = [
    ('COPY_LOCATION', _("Copy Location"), ""),
    ('COPY_ROTATION', _("Copy Rotation"), ""),
    ('COPY_SCALE', _("Copy Scale"), ""),
    ('COPY_TRANSFORMS', _("Copy Transforms"), ""),
]

ALL_CONSTRAINTS = [
    ('COPY_LOCATION', _("Copy Location"), ""),
    ('COPY_ROTATION', _("Copy Rotation"), ""),
    ('COPY_SCALE', _("Copy Scale"), ""),
    ('COPY_TRANSFORMS', _("Copy Transforms"), ""),
    ('LIMIT_DISTANCE', _("Limit Distance"), ""),
    ('LIMIT_LOCATION', _("Limit Location"), ""),
    ('LIMIT_ROTATION', _("Limit Rotation"), ""),
    ('LIMIT_SCALE', _("Limit Scale"), ""),
    ('MAINTAIN_VOLUME', _("Maintain Volume"), ""),
    ('TRANSFORMATION', _("Transformation"), ""),
    ('TRANSFORM_CACHE', _("Transform Cache"), ""),

    ('CLAMP_TO', _("Clamp To"), ""),
    ('DAMPED_TRACK', _("Damped Track"), ""),
    ('IK', _("Inverse Kinematics"), ""),
    ('LOCKED_TRACK', _("Locked Track"), ""),
    ('SPLINE_IK', _("Spline IK"), ""),
    ('STRETCH_TO', _("Stretch To"), ""),
    ('TRACK_TO', _("Track To"), ""),

    ('ACTION', _("Action"), ""),
    ('ARMATURE', _("Armature"), ""),
    ('CHILD_OF', _("Child Of"), ""),
    ('FLOOR', _("Floor"), ""),
    ('FOLLOW_PATH', _("Follow Path"), ""),
    ('PIVOT', _("Pivot"), ""),
    ('SHRINKWRAP', _("Shrinkwrap"), ""),

    ('CAMERA_SOLVER', _("Camera Solver"), ""),
    ('FOLLOW_TRACK', _("Follow Track"), ""),
    ('OBJECT_SOLVER', _("Object Solver"), ""),
]


def get_available_constraint_types(context, mode):
    """获取可用约束类型"""
    available_types = set()
    
    active_obj = context.active_object
    selected_objs = [obj for obj in context.selected_objects if obj.type == 'ARMATURE']
    
    if not selected_objs:
        return available_types
    
    if mode == 'IMITATE':
        # Imitate mode: Check if active and selected items have bones/vertex groups with same names
        if active_obj:
            for target_obj in selected_objs:
                if target_obj == active_obj:
                    continue
                if active_obj.type == 'ARMATURE':
                    # Active object is armature: Check for bones with same names
                    active_bone_names = {bone.name for bone in active_obj.pose.bones}
                    target_bone_names = {bone.name for bone in target_obj.pose.bones}
                    if active_bone_names & target_bone_names:  # 有交集 Has intersection
                        # Always show 4 transform constraints
                        available_types.update(['COPY_LOCATION', 'COPY_ROTATION', 'COPY_SCALE', 'COPY_TRANSFORMS'])
                        break
                elif active_obj.type == 'MESH':
                    # Active object is mesh: Check for vertex groups with same names
                    active_vgroup_names = {vg.name for vg in active_obj.vertex_groups}
                    target_bone_names = {bone.name for bone in target_obj.pose.bones}
                    if active_vgroup_names & target_bone_names:  # Has intersection
                        # Always show 4 transform constraints
                        available_types.update(['COPY_LOCATION', 'COPY_ROTATION', 'COPY_SCALE', 'COPY_TRANSFORMS'])
                        break
    
    elif mode == 'REMOVE_IMITATE':
        # Remove imitate mode: Check for existing constraints targeting active object in selected items
        if active_obj:
            for target_obj in selected_objs:
                if target_obj == active_obj:
                    continue
                for bone in target_obj.pose.bones:
                    for constraint in bone.constraints:
                        # Only check four transform constraints
                        if constraint.type in ['COPY_LOCATION', 'COPY_ROTATION', 'COPY_SCALE', 'COPY_TRANSFORMS']:
                            # Check if there are bones/vertex groups with same names
                            name_match = False
                            if active_obj.type == 'ARMATURE':
                                if bone.name in active_obj.pose.bones:
                                    name_match = True
                            elif active_obj.type == 'MESH':
                                if bone.name in active_obj.vertex_groups:
                                    name_match = True
                            
                            if name_match:
                                # Check if constraint targets active object and subtarget is current bone name
                                if (hasattr(constraint, 'target') and constraint.target == active_obj and
                                    hasattr(constraint, 'subtarget') and constraint.subtarget == bone.name):
                                    available_types.add(constraint.type)
    
    elif mode == 'COPY':
        # Copy mode: Check for constraints in active object that are missing in selected objects (for bones with same names)
        if active_obj and active_obj.type == 'ARMATURE':
            for target_obj in selected_objs:
                if target_obj == active_obj:
                    continue
                for active_bone in active_obj.pose.bones:
                    if active_bone.name in target_obj.pose.bones:
                        target_bone = target_obj.pose.bones[active_bone.name]
                        for constraint in active_bone.constraints:
                            # Check if target bone doesn't have the same constraint yet
                            constraint_exists = False
                            
                            for target_constraint in target_bone.constraints:
                                if target_constraint.type == constraint.type:
                                    # Check if all properties match
                                    properties_match = True
                                    
                                    # Check all properties (exclude some unimportant ones)
                                    exclude_props = {'rna_type', 'type', 'name', 'is_valid', 'error_message'}
                                    
                                    for prop in dir(constraint):
                                        if (not prop.startswith('_') and 
                                            not prop.startswith('bl_') and
                                            prop not in exclude_props and
                                            not callable(getattr(constraint, prop))):
                                            
                                            try:
                                                constraint_val = getattr(constraint, prop)
                                                target_val = getattr(target_constraint, prop)
                                                
                                                # Special treatment: None and empty strings are considered equal
                                                if constraint_val is None and target_val is None:
                                                    continue
                                                if constraint_val == '' and target_val == '':
                                                    continue
                                                if constraint_val == target_val:
                                                    continue
                                                    
                                                # Values ​​do not match
                                                properties_match = False
                                                break
                                                
                                            except (AttributeError, TypeError):
                                                # If an attribute exists in one constraint but not in another, it is not considered a mismatch
                                                pass
                                    
                                    if properties_match:
                                        constraint_exists = True
                                        break
                            
                            if not constraint_exists:
                                available_types.add(constraint.type)
    
    elif mode == 'REMOVE_COPY':
        # Remove copy mode: Check for same constraints in both active and selected objects (for bones with same names)
        if active_obj and active_obj.type == 'ARMATURE':
            for target_obj in selected_objs:
                if target_obj == active_obj:
                    continue
                for active_bone in active_obj.pose.bones:
                    if active_bone.name in target_obj.pose.bones:
                        target_bone = target_obj.pose.bones[active_bone.name]
                        for constraint in active_bone.constraints:
                            # Check if target bone has the same constraint
                            for target_constraint in target_bone.constraints:
                                if target_constraint.type == constraint.type:
                                    match = True
                                    
                                    # Check all properties (exclude some unimportant ones)
                                    exclude_props = {'rna_type', 'type', 'name', 'is_valid', 'error_message'}
                                    
                                    for prop in dir(constraint):
                                        if (not prop.startswith('_') and 
                                            not prop.startswith('bl_') and
                                            prop not in exclude_props and
                                            not callable(getattr(constraint, prop))):
                                            
                                            try:
                                                constraint_val = getattr(constraint, prop)
                                                target_val = getattr(target_constraint, prop)
                                                
                                                # Special treatment: None and empty strings are considered equal
                                                if constraint_val is None and target_val is None:
                                                    continue
                                                if constraint_val == '' and target_val == '':
                                                    continue
                                                if constraint_val == target_val:
                                                    continue
                                                    
                                                # Values ​​do not match
                                                match = False
                                                break
                                                
                                            except (AttributeError, TypeError):
                                                # If an attribute exists in one constraint but not in another, it is not considered a mismatch
                                                pass
                                    
                                    if match:
                                        available_types.add(constraint.type)
                                        break  # When a match is found, break out of the inner loop
    
    elif mode == 'DELETE':
        # Delete mode: Check constraints in all selected armatures (including active object)
        for obj in selected_objs:
            for bone in obj.pose.bones:
                for constraint in bone.constraints:
                    available_types.add(constraint.type)
    
    return available_types

# Constraint type icon mapping
CONSTRAINT_ICONS = {
    'COPY_LOCATION': 'CON_LOCLIKE',
    'COPY_ROTATION': 'CON_ROTLIKE',
    'COPY_SCALE': 'CON_SIZELIKE',
    'COPY_TRANSFORMS': 'CON_TRANSLIKE',
    'LIMIT_DISTANCE': 'CON_DISTLIMIT',
    'LIMIT_LOCATION': 'CON_LOCLIMIT',
    'LIMIT_ROTATION': 'CON_ROTLIMIT',
    'LIMIT_SCALE': 'CON_SIZELIMIT',
    'MAINTAIN_VOLUME': 'CON_SAMEVOL',
    'TRANSFORMATION': 'CON_TRANSFORM',
    'TRANSFORM_CACHE': 'CON_TRANSFORM_CACHE',

    'CLAMP_TO': 'CON_CLAMPTO',
    'DAMPED_TRACK': 'CON_TRACKTO',
    'IK': 'CON_KINEMATIC',
    'LOCKED_TRACK': 'CON_LOCKTRACK',
    'SPLINE_IK': 'CON_SPLINEIK',
    'STRETCH_TO': 'CON_STRETCHTO',
    'TRACK_TO': 'CON_TRACKTO',

    'ACTION': 'CON_ACTION',
    'ARMATURE': 'CON_ARMATURE',
    'CHILD_OF': 'CON_CHILDOF',
    'FLOOR': 'CON_FLOOR',
    'FOLLOW_PATH': 'CON_FOLLOWPATH',
    'PIVOT': 'CON_PIVOT',
    'SHRINKWRAP': 'CON_SHRINKWRAP',

    'CAMERA_SOLVER': 'CON_CAMERASOLVER',
    'FOLLOW_TRACK': 'CON_FOLLOWTRACK',
    'OBJECT_SOLVER': 'CON_OBJECTSOLVER',
}

def get_constraint_icon(constraint_type):
    """Get constraint type icon"""
    return CONSTRAINT_ICONS.get(constraint_type, 'CONSTRAINT')

class ANIM_OT_batch_imitate(Operator):
    """Batch create constraints for selected armatures targeting bones with same name in active armature"""
    bl_idname = "anim.batch_imitate"
    bl_label = "Batch Imitate"
    bl_options = {'REGISTER', 'UNDO'}
    
    constraint_type: EnumProperty(
        name="Constraint Type",
        items=IMITATE_CONSTRAINTS,
        default='COPY_ROTATION'
    )
    
    @classmethod
    def poll(cls, context):
        if not context.selected_objects:
            return False
        active_obj = context.active_object
        if not active_obj:
            cls.poll_message_set("No active object")
            return False
        # Active object can be armature or mesh
        if active_obj.type not in {'ARMATURE', 'MESH'}:
            cls.poll_message_set("Active object must be armature or mesh")
            return False
        # At least one selected armature
        selected_armatures = [obj for obj in context.selected_objects 
                            if obj.type == 'ARMATURE' and obj != active_obj]
        if not selected_armatures:
            cls.poll_message_set("Select at least one target armature")
            return False
        return True
    
    def execute(self, context):
        active_obj = context.active_object
        target_armatures = [obj for obj in context.selected_objects 
                          if obj.type == 'ARMATURE' and obj != active_obj]
        
        total_added = 0
        
        for target_armature in target_armatures:
            for target_bone in target_armature.pose.bones:
                # Check if same constraint already exists
                existing = any(c.type == self.constraint_type and 
                             c.target == active_obj and 
                             c.subtarget == target_bone.name 
                             for c in target_bone.constraints)
                if not existing:
                    # Use Blender's built-in method to create constraints
                    constraint = target_bone.constraints.new(type=self.constraint_type)
                    constraint.target = active_obj
                    constraint.subtarget = target_bone.name
                    total_added += 1
        
        self.report({'INFO'}, f"Added {total_added} imitate constraints")
        return {'FINISHED'}

class ANIM_OT_remove_imitate(Operator):
    """Batch remove constraints from selected armatures targeting bones with same name in active armature"""
    bl_idname = "anim.remove_imitate"
    bl_label = "Remove Imitate Constraints"
    bl_options = {'REGISTER', 'UNDO'}
    
    constraint_type: EnumProperty(
        name="Constraint Type",
        items=[('ALL', "All", "")] + IMITATE_CONSTRAINTS,
        default='ALL'
    )
    
    @classmethod
    def poll(cls, context):
        if not context.selected_objects:
            return False
        active_obj = context.active_object
        if not active_obj or active_obj.type not in {'ARMATURE', 'MESH'}:
            cls.poll_message_set("Active object must be armature or mesh")
            return False
        selected_armatures = [obj for obj in context.selected_objects 
                            if obj.type == 'ARMATURE' and obj != active_obj]
        if not selected_armatures:
            cls.poll_message_set("Select at least one target armature")
            return False
        return True
    
    def execute(self, context):
        active_obj = context.active_object
        target_armatures = [obj for obj in context.selected_objects 
                          if obj.type == 'ARMATURE' and obj != active_obj]
        
        total_removed = 0
        
        for target_armature in target_armatures:
            for target_bone in target_armature.pose.bones:
                for constraint in list(target_bone.constraints):
                    if (constraint.target == active_obj and 
                        constraint.subtarget == target_bone.name and
                        (self.constraint_type == 'ALL' or constraint.type == self.constraint_type)):
                        target_bone.constraints.remove(constraint)
                        total_removed += 1
        
        self.report({'INFO'}, f"Removed {total_removed} imitate constraints")
        return {'FINISHED'}

class ANIM_OT_batch_copy(Operator):
    """Copy constraints from bones with same name in active armature to selected armatures"""
    bl_idname = "anim.batch_copy"
    bl_label = "Batch Copy Constraints"
    bl_options = {'REGISTER', 'UNDO'}
    
    constraint_type: EnumProperty(
        name="Constraint Type",
        items=[('ALL', "All", "")] + ALL_CONSTRAINTS,
        default='ALL'
    )
    
    @classmethod
    def poll(cls, context):
        active_obj = context.active_object
        if not active_obj or active_obj.type != 'ARMATURE':
            cls.poll_message_set("Active object must be an armature")
            return False
        
        # Check if active armature has constraints
        has_constraints = any(len(bone.constraints) > 0 
                            for bone in active_obj.pose.bones)
        if not has_constraints:
            cls.poll_message_set("Active armature has no bone constraints")
            return False
        
        selected_armatures = [obj for obj in context.selected_objects 
                            if obj.type == 'ARMATURE' and obj != active_obj]
        if not selected_armatures:
            cls.poll_message_set("Select at least one target armature")
            return False
            
        return True
    
    def execute(self, context):
        active_obj = context.active_object
        target_armatures = [obj for obj in context.selected_objects 
                          if obj.type == 'ARMATURE' and obj != active_obj]
        
        total_copied = 0
        
        for target_armature in target_armatures:
            for target_bone in target_armature.pose.bones:
                if target_bone.name in active_obj.pose.bones:
                    source_bone = active_obj.pose.bones[target_bone.name]
                    
                    for source_constraint in source_bone.constraints:
                        if (self.constraint_type == 'ALL' or 
                            source_constraint.type == self.constraint_type):
                            
                            # Check if the same constraint already exists
                            constraint_exists = False
                            for target_constraint in target_bone.constraints:
                                if target_constraint.type == source_constraint.type:
                                    # Simple check if key attributes match
                                    properties_match = True
                                    if hasattr(source_constraint, 'target') and hasattr(target_constraint, 'target'):
                                        if source_constraint.target != target_constraint.target:
                                            properties_match = False
                                    if hasattr(source_constraint, 'subtarget') and hasattr(target_constraint, 'subtarget'):
                                        if source_constraint.subtarget != target_constraint.subtarget:
                                            properties_match = False
                                    if properties_match:
                                        constraint_exists = True
                                        break
                            
                            if not constraint_exists:
                                # Copy constraints using blender built-in methods
                                new_constraint = target_bone.constraints.new(
                                    type=source_constraint.type
                                )
                                
                                # Copy all properties
                                exclude_props = {'rna_type', 'type', 'name', 'is_valid', 'error_message'}
                                
                                for prop in dir(source_constraint):
                                    if (not prop.startswith('_') and 
                                        not prop.startswith('bl_') and
                                        prop not in exclude_props and
                                        not callable(getattr(source_constraint, prop))):
                                        try:
                                            setattr(new_constraint, prop, 
                                                   getattr(source_constraint, prop))
                                        except (AttributeError, TypeError):
                                            # Ignore properties that cannot be set
                                            pass
                                
                                total_copied += 1
        
        self.report({'INFO'}, f"Copied {total_copied} constraints")
        return {'FINISHED'}

class ANIM_OT_remove_copy(Operator):
    """Remove constraints from selected armatures that match constraints on bones with same name in active armature"""
    bl_idname = "anim.remove_copy"
    bl_label = "Remove Copied Constraints"
    bl_options = {'REGISTER', 'UNDO'}
    
    constraint_type: EnumProperty(
        name="Constraint Type",
        items=[('ALL', "All", "")] + ALL_CONSTRAINTS,
        default='ALL'
    )
    
    @classmethod
    def poll(cls, context):
        active_obj = context.active_object
        if not active_obj or active_obj.type != 'ARMATURE':
            cls.poll_message_set("Active object must be an armature")
            return False
            
        selected_armatures = [obj for obj in context.selected_objects 
                            if obj.type == 'ARMATURE' and obj != active_obj]
        if not selected_armatures:
            cls.poll_message_set("Select at least one target armature")
            return False
            
        return True
    
    def execute(self, context):
        active_obj = context.active_object
        target_armatures = [obj for obj in context.selected_objects 
                          if obj.type == 'ARMATURE' and obj != active_obj]
        
        total_removed = 0
        
        for target_armature in target_armatures:
            for target_bone in target_armature.pose.bones:
                if target_bone.name in active_obj.pose.bones:
                    source_bone = active_obj.pose.bones[target_bone.name]
                    
                    # Check each constraint of the target bone
                    for target_constraint in list(target_bone.constraints):
                        # If a constraint type is specified, checks for a match
                        if (self.constraint_type != 'ALL' and 
                            target_constraint.type != self.constraint_type):
                            continue
                            
                        # Find constraints of the same type with matching properties in the source skeleton
                        for source_constraint in source_bone.constraints:
                            if source_constraint.type == target_constraint.type:
                                # Check if all properties match
                                properties_match = True
                                exclude_props = {'rna_type', 'type', 'name', 'is_valid', 'error_message'}
                                
                                for prop in dir(source_constraint):
                                    if (not prop.startswith('_') and 
                                        not prop.startswith('bl_') and
                                        prop not in exclude_props and
                                        not callable(getattr(source_constraint, prop))):
                                        
                                        try:
                                            source_val = getattr(source_constraint, prop)
                                            target_val = getattr(target_constraint, prop)
                                            
                                            # Special treatment: None and empty strings are considered equal
                                            if source_val is None and target_val is None:
                                                continue
                                            if source_val == '' and target_val == '':
                                                continue
                                            if source_val == target_val:
                                                continue
                                                
                                            # Values ​​do not match
                                            properties_match = False
                                            break
                                            
                                        except (AttributeError, TypeError):
                                            # If an attribute exists in one constraint but not in another, it is considered a mismatch
                                            properties_match = False
                                            break
                                
                                # If a constraint with an exact matching attribute is found, delete the target constraint
                                if properties_match:
                                    target_bone.constraints.remove(target_constraint)
                                    total_removed += 1
                                    break  # After deletion, jump out of the inner loop and continue to check the next target constraint.
        
        self.report({'INFO'}, f"Removed {total_removed} copied constraints")
        return {'FINISHED'}

class ANIM_OT_batch_new(Operator):
    """Create new constraints for all bones in selected armatures"""
    bl_idname = "anim.batch_new"
    bl_label = "Batch New Constraints"
    bl_options = {'REGISTER', 'UNDO'}
    
    constraint_type: EnumProperty(
        name="Constraint Type",
        items=ALL_CONSTRAINTS,
        default='COPY_LOCATION'
    )
    
    @classmethod
    def poll(cls, context):
        selected_armatures = [obj for obj in context.selected_objects 
                            if obj.type == 'ARMATURE']
        return len(selected_armatures) >= 1
    
    def execute(self, context):
        selected_armatures = [obj for obj in context.selected_objects 
                            if obj.type == 'ARMATURE']
        
        total_added = 0
        
        for armature in selected_armatures:
            for bone in armature.pose.bones:
                # Use Blender's built-in method to create constraints
                bone.constraints.new(type=self.constraint_type)
                total_added += 1
        
        self.report({'INFO'}, f"Added {total_added} new constraints")
        return {'FINISHED'}

class ANIM_OT_batch_delete(Operator):
    """Delete constraints by type from all bones in selected armatures"""
    bl_idname = "anim.batch_delete"
    bl_label = "Batch Delete Constraints"
    bl_options = {'REGISTER', 'UNDO'}
    
    constraint_type: EnumProperty(
        name="Constraint Type",
        items=[('ALL', "All", "")] + ALL_CONSTRAINTS,
        default='ALL'
    )
    
    @classmethod
    def poll(cls, context):
        selected_armatures = [obj for obj in context.selected_objects 
                            if obj.type == 'ARMATURE']
        return len(selected_armatures) >= 1
    
    def execute(self, context):
        selected_armatures = [obj for obj in context.selected_objects 
                            if obj.type == 'ARMATURE']
        
        total_removed = 0
        
        for armature in selected_armatures:
            for bone in armature.pose.bones:
                for constraint in list(bone.constraints):
                    if (self.constraint_type == 'ALL' or 
                        constraint.type == self.constraint_type):
                        bone.constraints.remove(constraint)
                        total_removed += 1
        
        type_name = "All" if self.constraint_type == 'ALL' else self.constraint_type
        self.report({'INFO'}, f"Removed {total_removed} {type_name} constraints")
        return {'FINISHED'}

# Menu definitions
class VIEW3D_MT_batch_constraints_menu(Menu):
    bl_label = _("Batch Bone Constraints")
    bl_idname = "VIEW3D_MT_batch_constraints_menu"
    
    @classmethod
    def poll(cls, context):
        # Check if it is in object mode
        if context.mode != 'OBJECT':
            return False
        # Check if active object or selected objects include armatures
        if context.active_object and context.active_object.type == 'ARMATURE':
            return True
        # Check if selected objects include armatures
        selected_armatures = [obj for obj in context.selected_objects 
                            if obj.type == 'ARMATURE']
        return len(selected_armatures) >= 1
    
    def draw(self, context):
        layout = self.layout
        layout.menu("VIEW3D_MT_imitate_menu", icon='CONSTRAINT_BONE')
        layout.menu("VIEW3D_MT_remove_imitate_menu", icon='REMOVE')
        layout.menu("VIEW3D_MT_copy_menu", icon='DUPLICATE')
        layout.menu("VIEW3D_MT_remove_copy_menu", icon='REMOVE')
        layout.menu("VIEW3D_MT_new_menu", icon='ADD')
        layout.menu("VIEW3D_MT_delete_menu", icon='TRASH')

class VIEW3D_MT_imitate_menu(Menu):
    bl_label = _("Imitate")
    bl_idname = "VIEW3D_MT_imitate_menu"
    
    def draw(self, context):
        layout = self.layout
        available_types = get_available_constraint_types(context, 'IMITATE')
        
        if not available_types:
            # Show hint when no options available
            layout.label(text="No options available", icon='INFO')
            return
        
        for constraint_type in IMITATE_CONSTRAINTS:
            icon = get_constraint_icon(constraint_type[0])
            op = layout.operator("anim.batch_imitate", text=constraint_type[1], icon=icon)
            op.constraint_type = constraint_type[0]

class VIEW3D_MT_remove_imitate_menu(Menu):
    bl_label = _("Remove Imitate")
    bl_idname = "VIEW3D_MT_remove_imitate_menu"
    
    def draw(self, context):
        layout = self.layout
        available_types = get_available_constraint_types(context, 'REMOVE_IMITATE')
        
        if not available_types:
            # Show hint when no options available
            layout.label(text="No options available", icon='INFO')
            return
        
        # Only show "All" option when available types are more than 1
        if len(available_types) >1:
            op = layout.operator("anim.remove_imitate", text="All", icon='X')
            op.constraint_type = 'ALL'
            layout.separator()
        
        for constraint_type in IMITATE_CONSTRAINTS:
            if constraint_type[0] in available_types:
                icon = get_constraint_icon(constraint_type[0])
                op = layout.operator("anim.remove_imitate", text=constraint_type[1], icon=icon)
                op.constraint_type = constraint_type[0]

class VIEW3D_MT_copy_menu(Menu):
    bl_label = _("Copy")
    bl_idname = "VIEW3D_MT_copy_menu"
    
    def draw(self, context):
        layout = self.layout
        available_types = get_available_constraint_types(context, 'COPY')
        
        if not available_types:
            # Show hint when no options available
            layout.label(text="No options available", icon='INFO')
            return
        
        # Only show "All" option when available types are more than 1
        if len(available_types) >1:
            op = layout.operator("anim.batch_copy", text="All", icon='DUPLICATE')
            op.constraint_type = 'ALL'
            layout.separator()
        
        for constraint_type in ALL_CONSTRAINTS:
            if constraint_type[0] in available_types:
                icon = get_constraint_icon(constraint_type[0])
                op = layout.operator("anim.batch_copy", text=constraint_type[1], icon=icon)
                op.constraint_type = constraint_type[0]

class VIEW3D_MT_remove_copy_menu(Menu):
    bl_label = _("Remove Copy")
    bl_idname = "VIEW3D_MT_remove_copy_menu"
    
    def draw(self, context):
        layout = self.layout
        available_types = get_available_constraint_types(context, 'REMOVE_COPY')
        
        if not available_types:
            # Show hint when no options available
            layout.label(text="No options available", icon='INFO')
            return
        
        # Only show "All" option when available types are more than 1
        if len(available_types) >1:
            op = layout.operator("anim.remove_copy", text="All", icon='X')
            op.constraint_type = 'ALL'
            layout.separator()
        
        for constraint_type in ALL_CONSTRAINTS:
            if constraint_type[0] in available_types:
                icon = get_constraint_icon(constraint_type[0])
                op = layout.operator("anim.remove_copy", text=constraint_type[1], icon=icon)
                op.constraint_type = constraint_type[0]

class VIEW3D_MT_new_menu(Menu):
    bl_label = _("New")
    bl_idname = "VIEW3D_MT_new_menu"
    
    def draw(self, context):
        layout = self.layout
        # Show hint when no options available
        for constraint_type in ALL_CONSTRAINTS:
            icon = get_constraint_icon(constraint_type[0])
            op = layout.operator("anim.batch_new", text=constraint_type[1], icon=icon)
            op.constraint_type = constraint_type[0]

class VIEW3D_MT_delete_menu(Menu):
    bl_label = _("Delete")
    bl_idname = "VIEW3D_MT_delete_menu"
    
    def draw(self, context):
        layout = self.layout
        available_types = get_available_constraint_types(context, 'DELETE')
        
        if not available_types:
            # Show hint when no options available
            layout.label(text="No options available", icon='INFO')
            return
        
        # Only show "All" option when available types are more than 1
        if len(available_types) >1:
            op = layout.operator("anim.batch_delete", text="All", icon='X')
            op.constraint_type = 'ALL'
            layout.separator()
        
        for constraint_type in ALL_CONSTRAINTS:
            if constraint_type[0] in available_types:
                icon = get_constraint_icon(constraint_type[0])
                op = layout.operator("anim.batch_delete", text=constraint_type[1], icon=icon)
                op.constraint_type = constraint_type[0]

def menu_func(self, context):
    # Only show menu when active or selected objects include armatures
    if context.mode == 'OBJECT' and (context.active_object and context.active_object.type == 'ARMATURE') or \
       any(obj.type == 'ARMATURE' for obj in context.selected_objects):
        self.layout.menu("VIEW3D_MT_batch_constraints_menu")

classes = (
    ANIM_OT_batch_imitate,
    ANIM_OT_remove_imitate,
    ANIM_OT_batch_copy,
    ANIM_OT_remove_copy,
    ANIM_OT_batch_new,
    ANIM_OT_batch_delete,
    VIEW3D_MT_batch_constraints_menu,
    VIEW3D_MT_imitate_menu,
    VIEW3D_MT_remove_imitate_menu,
    VIEW3D_MT_copy_menu,
    VIEW3D_MT_remove_copy_menu,
    VIEW3D_MT_new_menu,
    VIEW3D_MT_delete_menu,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.VIEW3D_MT_editor_menus.append(menu_func)

def unregister():
    bpy.types.VIEW3D_MT_editor_menus.remove(menu_func)
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()