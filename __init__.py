# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2025 deepseek

bl_info = {
    "name": "Batch Bone Constraints",
    "author": "distinctive-mark",
    "version": (1, 1, 1),
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

# 约束类型定义 Constraint type definitions
IMITATE_CONSTRAINTS = [
    ('COPY_LOCATION', "Copy Location", ""),
    ('COPY_ROTATION', "Copy Rotation", ""),
    ('COPY_SCALE', "Copy Scale", ""),
    ('COPY_TRANSFORMS', "Copy Transforms", ""),
]

ALL_CONSTRAINTS = [
    ('COPY_LOCATION', "Copy Location", ""),
    ('COPY_ROTATION', "Copy Rotation", ""),
    ('COPY_SCALE', "Copy Scale", ""),
    ('COPY_TRANSFORMS', "Copy Transforms", ""),
    ('DAMPED_TRACK', "Damped Track", ""),
    ('TRACK_TO', "Track To", ""),
    ('STRETCH_TO', "Stretch To", ""),
    ('CLAMP_TO', "Clamp To", ""),
    ('TRANSFORM', "Transform", ""),
    ('SHRINKWRAP', "Shrinkwrap", ""),
    ('LIMIT_LOCATION', "Limit Location", ""),
    ('LIMIT_ROTATION', "Limit Rotation", ""),
    ('LIMIT_SCALE', "Limit Scale", ""),
    ('MAINTAIN_VOLUME', "Maintain Volume", ""),
    ('ACTION', "Action", ""),
    ('LOCKED_TRACK', "Locked Track", ""),
    ('STRETCH_TO', "Stretch To", ""),
    ('FLOOR', "Floor", ""),
    ('FULLTRACK', "Full Track", ""),
    ('RIGID_BODY_JOINT', "Rigid Body Joint", ""),
    ('CHILD_OF', "Child Of", ""),
    ('PIVOT', "Pivot", ""),
    ('FOLLOW_PATH', "Follow Path", ""),
    ('CAMERA_SOLVER', "Camera Solver", ""),
    ('OBJECT_SOLVER', "Object Solver", ""),
    ('ARMATURE', "Armature", ""),
    ('SPLINE_IK', "Spline IK", ""),
]

# 在 ALL_CONSTRAINTS 定义后添加以下代码

def get_available_constraint_types(context, mode):
    """获取可用约束类型"""
    available_types = set()
    
    active_obj = context.active_object
    selected_objs = [obj for obj in context.selected_objects if obj.type == 'ARMATURE']
    
    if not selected_objs:
        return available_types
    
    if mode == 'IMITATE':
        # 模仿模式：检查活动项和选中项是否有同名骨骼/顶点组
        if active_obj:
            for target_obj in selected_objs:
                if target_obj == active_obj:
                    continue
                if active_obj.type == 'ARMATURE':
                    # 活动项是骨架：检查同名骨骼
                    active_bone_names = {bone.name for bone in active_obj.pose.bones}
                    target_bone_names = {bone.name for bone in target_obj.pose.bones}
                    if active_bone_names & target_bone_names:  # 有交集
                        # 总是显示4种变换约束
                        available_types.update(['COPY_LOCATION', 'COPY_ROTATION', 'COPY_SCALE', 'COPY_TRANSFORMS'])
                        break
                elif active_obj.type == 'MESH':
                    # 活动项是网格：检查同名顶点组
                    active_vgroup_names = {vg.name for vg in active_obj.vertex_groups}
                    target_bone_names = {bone.name for bone in target_obj.pose.bones}
                    if active_vgroup_names & target_bone_names:  # 有交集
                        # 总是显示4种变换约束
                        available_types.update(['COPY_LOCATION', 'COPY_ROTATION', 'COPY_SCALE', 'COPY_TRANSFORMS'])
                        break
    
    elif mode == 'REMOVE_IMITATE':
        # 移除模仿模式：检查选中项中已有的以活动项为目标的约束
        if active_obj:
            for target_obj in selected_objs:
                if target_obj == active_obj:
                    continue
                for bone in target_obj.pose.bones:
                    for constraint in bone.constraints:
                        # 检查约束是否以活动项为目标
                        if (constraint.target == active_obj and 
                            constraint.type in ['COPY_LOCATION', 'COPY_ROTATION', 'COPY_SCALE', 'COPY_TRANSFORMS']):
                            # 检查是否有同名骨骼/顶点组
                            if active_obj.type == 'ARMATURE':
                                if bone.name in active_obj.pose.bones:
                                    available_types.add(constraint.type)
                            elif active_obj.type == 'MESH':
                                if bone.name in active_obj.vertex_groups:
                                    available_types.add(constraint.type)
    
    elif mode == 'COPY':
        # 复制模式：检查活动项有而选中项没有的约束（针对同名骨骼）
        if active_obj and active_obj.type == 'ARMATURE':
            for target_obj in selected_objs:
                if target_obj == active_obj:
                    continue
                for active_bone in active_obj.pose.bones:
                    if active_bone.name in target_obj.pose.bones:
                        target_bone = target_obj.pose.bones[active_bone.name]
                        for constraint in active_bone.constraints:
                            # 检查目标骨骼是否还没有相同的约束
                            if not any(
                                c.type == constraint.type and 
                                c.target == constraint.target and 
                                getattr(c, 'subtarget', '') == getattr(constraint, 'subtarget', '')
                                for c in target_bone.constraints
                            ):
                                available_types.add(constraint.type)
    
    elif mode == 'REMOVE_COPY':
        # 移除复制模式：检查活动项和选中项有相同约束（针对同名骨骼）
        if active_obj and active_obj.type == 'ARMATURE':
            for target_obj in selected_objs:
                if target_obj == active_obj:
                    continue
                for active_bone in active_obj.pose.bones:
                    if active_bone.name in target_obj.pose.bones:
                        target_bone = target_obj.pose.bones[active_bone.name]
                        for constraint in active_bone.constraints:
                            # 检查目标骨骼是否有相同的约束
                            if any(
                                c.type == constraint.type and 
                                c.target == constraint.target and 
                                getattr(c, 'subtarget', '') == getattr(constraint, 'subtarget', '')
                                for c in target_bone.constraints
                            ):
                                available_types.add(constraint.type)
    
    elif mode == 'DELETE':
        # 删除模式：检查所有选中骨架的约束（包括活动项）
        for obj in selected_objs:
            for bone in obj.pose.bones:
                for constraint in bone.constraints:
                    available_types.add(constraint.type)
    
    return available_types

# 约束类型图标映射
CONSTRAINT_ICONS = {
    'COPY_LOCATION': 'CON_LOCLIKE',
    'COPY_ROTATION': 'CON_ROTLIKE',
    'COPY_SCALE': 'CON_SIZELIKE',
    'COPY_TRANSFORMS': 'CON_TRANSFORM',
    'LIMIT_LOCATION': 'CON_LOCLIMIT',
    'LIMIT_ROTATION': 'CON_ROTLIMIT',
    'LIMIT_SCALE': 'CON_SIZELIMIT',
    'DAMPED_TRACK': 'CON_TRACKTO',
    'TRACK_TO': 'CON_TRACKTO',
    'STRETCH_TO': 'CON_STRETCHTO',
    'CLAMP_TO': 'CON_CLAMPTO',
    'TRANSFORM': 'CON_TRANSFORM',
    'SHRINKWRAP': 'CON_SHRINKWRAP',
    'MAINTAIN_VOLUME': 'CON_SAMEVOL',
    'ACTION': 'CON_ACTION',
    'LOCKED_TRACK': 'CON_LOCKTRACK',
    'FLOOR': 'CON_FLOOR',
    'FULLTRACK': 'CON_FOLLOWPATH',
    'RIGID_BODY_JOINT': 'CON_ROTLIKE',
    'CHILD_OF': 'CON_CHILDOF',
    'PIVOT': 'CON_PIVOT',
    'FOLLOW_PATH': 'CON_FOLLOWPATH',
    'CAMERA_SOLVER': 'CON_CAMERASOLVER',
    'OBJECT_SOLVER': 'CON_OBJECTSOLVER',
    'ARMATURE': 'CON_ARMATURE',
    'SPLINE_IK': 'CON_SPLINEIK',
}

def get_constraint_icon(constraint_type):
    """获取约束类型图标"""
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
        # 活动项可以是骨架或网格 Active object can be armature or mesh
        if active_obj.type not in {'ARMATURE', 'MESH'}:
            cls.poll_message_set("Active object must be armature or mesh")
            return False
        # 至少有一个选中的骨架 At least one selected armature
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
                # 检查是否已存在相同约束 Check if same constraint already exists
                existing = any(c.type == self.constraint_type and 
                             c.target == active_obj and 
                             c.subtarget == target_bone.name 
                             for c in target_bone.constraints)
                if not existing:
                    # 使用Blender内置方法创建约束 Use Blender's built-in method to create constraints
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
        
        # 检查活动骨架是否有约束 Check if active armature has constraints
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
                            
                            # 使用Blender内置方法复制约束 Use Blender's built-in method to copy constraints
                            new_constraint = target_bone.constraints.new(
                                type=source_constraint.type
                            )
                            
                            # 复制所有属性 Copy all properties
                            for prop in dir(source_constraint):
                                if (not prop.startswith('_') and 
                                    not prop.startswith('bl_') and
                                    prop not in ['rna_type', 'type', 'name']):
                                    try:
                                        setattr(new_constraint, prop, 
                                               getattr(source_constraint, prop))
                                    except (AttributeError, TypeError):
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
                    source_constraint_types = [c.type for c in source_bone.constraints]
                    
                    for constraint in list(target_bone.constraints):
                        if (constraint.type in source_constraint_types and
                            (self.constraint_type == 'ALL' or 
                             constraint.type == self.constraint_type)):
                            target_bone.constraints.remove(constraint)
                            total_removed += 1
        
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
                # 使用Blender内置方法创建约束 Use Blender's built-in method to create constraints
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

# 菜单定义
class VIEW3D_MT_batch_constraints_menu(Menu):
    bl_label = "Batch Bone Constraints"
    bl_idname = "VIEW3D_MT_batch_constraints_menu"
    
    @classmethod
    def poll(cls, context):
        # 检查活动对象或选中对象中是否有骨架 Check if active object or selected objects include armatures
        if context.active_object and context.active_object.type == 'ARMATURE':
            return True
        # 检查选中对象中是否有骨架 Check if selected objects include armatures
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
    bl_label = "Imitate"
    bl_idname = "VIEW3D_MT_imitate_menu"
    
    def draw(self, context):
        layout = self.layout
        available_types = get_available_constraint_types(context, 'IMITATE')
        
        if not available_types:
            # 没有可用项时显示提示
            layout.label(text="No options available", icon='INFO')
            return
        
        for constraint_type in IMITATE_CONSTRAINTS:
            icon = get_constraint_icon(constraint_type[0])
            op = layout.operator("anim.batch_imitate", text=constraint_type[1], icon=icon)
            op.constraint_type = constraint_type[0]

class VIEW3D_MT_remove_imitate_menu(Menu):
    bl_label = "Remove Imitate"
    bl_idname = "VIEW3D_MT_remove_imitate_menu"
    
    def draw(self, context):
        layout = self.layout
        available_types = get_available_constraint_types(context, 'REMOVE_IMITATE')
        
        if not available_types:
            # 没有可用项时显示提示
            layout.label(text="No options available", icon='INFO')
            return
        
        # 只有当可用类型大于1时才显示"All"选项
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
    bl_label = "Copy"
    bl_idname = "VIEW3D_MT_copy_menu"
    
    def draw(self, context):
        layout = self.layout
        available_types = get_available_constraint_types(context, 'COPY')
        
        if not available_types:
            # 没有可用项时显示提示
            layout.label(text="No options available", icon='INFO')
            return
        
        # 只有当可用类型大于1时才显示"All"选项
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
    bl_label = "Remove Copy"
    bl_idname = "VIEW3D_MT_remove_copy_menu"
    
    def draw(self, context):
        layout = self.layout
        available_types = get_available_constraint_types(context, 'REMOVE_COPY')
        
        if not available_types:
            # 没有可用项时显示提示
            layout.label(text="No options available", icon='INFO')
            return
        
        # 只有当可用类型大于1时才显示"All"选项
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
    bl_label = "New"
    bl_idname = "VIEW3D_MT_new_menu"
    
    def draw(self, context):
        layout = self.layout
        # 新建模式显示所有约束类型
        for constraint_type in ALL_CONSTRAINTS:
            icon = get_constraint_icon(constraint_type[0])
            op = layout.operator("anim.batch_new", text=constraint_type[1], icon=icon)
            op.constraint_type = constraint_type[0]

class VIEW3D_MT_delete_menu(Menu):
    bl_label = "Delete"
    bl_idname = "VIEW3D_MT_delete_menu"
    
    def draw(self, context):
        layout = self.layout
        available_types = get_available_constraint_types(context, 'DELETE')
        
        if not available_types:
            # 没有可用项时显示提示
            layout.label(text="No options available", icon='INFO')
            return
        
        # 只有当可用类型大于1时才显示"All"选项
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
    # 只在活动项或选中项中有骨架时才显示菜单 Only show menu when active or selected objects include armatures
    if (context.active_object and context.active_object.type == 'ARMATURE') or \
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