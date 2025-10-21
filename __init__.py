# SPDX-License-Identifier: GPL-3.0-or-later
# SPDX-FileCopyrightText: 2025 deepseek

bl_info = {
    "name": "Batch Bone Constraints",
    "author": "distinctive-mark",
    "version": (1, 0, 1),
    "blender": (4, 2, 0),
    "location": "3D Viewport > Header > Batch Bone Constraints",
    "description": "Batch create bone constraints for selected armatures targeting active armature's same bones",
    "category": "Animation",
    "doc_url": "https://github.com/distinctive-mark/batch-bone-constraints",
    "tracker_url": "https://github.com/distinctive-mark/batch-bone-constraints/issues",
}

import bpy
from bpy.types import Operator, Menu, PropertyGroup
from bpy.props import EnumProperty, BoolProperty, FloatProperty, PointerProperty

# 约束类型枚举 # Constraint type enum
CONSTRAINT_TYPES = [
    ('COPY_LOCATION', "Copy Location", "Copy Location Constraint"),
    ('COPY_ROTATION', "Copy Rotation", "Copy Rotation Constraint"),
    ('COPY_SCALE', "Copy Scale", "Copy Scale Constraint"),
    ('COPY_TRANSFORMS', "Copy Transforms", "Copy Transforms Constraint"),
]

# 空间变换枚举 # Space transformation enum
SPACE_TYPES = [
    ('WORLD', "World Space", "World Space"),
    ('LOCAL', "Local Space", "Local Space"), 
    ('LOCAL_WITH_PARENT', "Local With Parent", "Local With Parent"),
    ('POSE', "Pose Space", "Pose Space"),
    ('CUSTOM', "Custom Space", "Custom Space"),
]

# 混合模式枚举 # Mix mode enum
MIX_MODES = [
    ('REPLACE', "Replace", "Replace Original Transform"),
    ('ADD', "Add", "Add to Original Transform"),
    ('BEFORE', "Before", "Apply Before Original Transform"),
    ('AFTER', "After", "Apply After Original Transform"),
]

class BoneConstraintSettings(PropertyGroup):
    """骨骼约束设置属性组"""
    """Bone Constraint Settings Property Group"""
    
    # 基础设置 # Basic settings
    constraint_type: EnumProperty(
        name="Type",
        description="Select the constraint Type to add",
        items=CONSTRAINT_TYPES,
        default='COPY_ROTATION'
    )
    
    influence: FloatProperty(
        name="Influence",
        description="The influence of the constraint",
        default=1.0,
        min=0.0,
        max=1.0,
        subtype='FACTOR'
    )
    
    # 空间设置 # Space settings
    target_space: EnumProperty(
        name="Target",
        description="The space in which the target is evaluated",
        items=SPACE_TYPES,
        default='LOCAL'
    )
    
    owner_space: EnumProperty(
        name="Owner",
        description="The space in which the owner is evaluated", 
        items=SPACE_TYPES,
        default='LOCAL'
    )
    
    # 通用约束属性 # General constraint properties
    use_offset: BoolProperty(
        name="Offset",
        description="offset",
        default=False
    )
    
    # 位置约束属性 # Location constraint properties
    use_x: BoolProperty(name="X", default=True)
    use_y: BoolProperty(name="Y", default=True)
    use_z: BoolProperty(name="Z", default=True)
    invert_x: BoolProperty(name="X", default=False)
    invert_y: BoolProperty(name="Y", default=False)
    invert_z: BoolProperty(name="Z", default=False)
    
    # 旋转约束属性 # Rotation constraint properties
    mix_mode: EnumProperty(
        name="Mix Mode",
        items=MIX_MODES,
        default='REPLACE'
    )
    
    # 缩放约束属性 # Scale constraint properties
    power: FloatProperty(
        name="Power",
        description="Multiply the target scale obtained by the constraint object",
        default=1.0,
        min=0.0,
        max=10.0
    )

class ANIM_OT_add_bone_constraints(Operator):
    """为选中骨架添加骨骼约束"""
    """Add bone constraints to selected armatures"""
    bl_idname = "anim.add_bone_constraints"
    bl_label = "Batch Add Bone Constraints"
    bl_description = "Add bone constraints to selected armatures targeting bones with same names in active armature"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return (context.active_object and 
                context.active_object.type == 'ARMATURE' and
                len(context.selected_objects) >= 2)
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=360)
    
    def draw(self, context):
        layout = self.layout
        settings = context.scene.bone_constraint_settings
        
        # 约束类型选择 # Constraint type selection
        split = layout.split(factor=0.5)
        split.label(text="Type")
        split.prop(settings, "constraint_type", text="")
        layout.separator()
        
        # 基础设置 # Basic settings
        layout.prop(settings, "influence")
        
        # 空间设置 # Space settings
        row = layout.row()
        row.prop(settings, "target_space")
        row.prop(settings, "owner_space")
        
        constraint_type = settings.constraint_type
        
        # 约束特定设置 # Constraint-specific settings
        if constraint_type == 'COPY_LOCATION':
            self._draw_location_settings(layout, settings)
        elif constraint_type == 'COPY_ROTATION':
            self._draw_rotation_settings(layout, settings)
        elif constraint_type == 'COPY_SCALE':
            self._draw_scale_settings(layout, settings)
        elif constraint_type == 'COPY_TRANSFORMS':
            self._draw_transform_settings(layout, settings)
    
    def _draw_location_settings(self, layout, settings):
        """绘制位置约束设置"""
        """Draw location constraint settings"""
        # 轴设置 # Axis settings
        row = layout.row()
        row.label(text="Axis")
        sub = row.row(align=True)
        sub.prop(settings, "use_x", toggle=True)
        sub.prop(settings, "use_y", toggle=True)
        sub.prop(settings, "use_z", toggle=True)
    
        # 反转设置 # Invert settings
        row = layout.row()
        row.label(text="Invert")
        sub = row.row(align=True)
        sub.prop(settings, "invert_x", toggle=True)
        sub.prop(settings, "invert_y", toggle=True)
        sub.prop(settings, "invert_z", toggle=True)
    
        # 偏移设置 # Offset settings
        layout.prop(settings, "use_offset")
    
    def _draw_rotation_settings(self, layout, settings):
        """绘制旋转约束设置"""
        """Draw rotation constraint settings"""
        # 轴设置 # Axis settings
        row = layout.row()
        row.label(text="Axis")
        sub = row.row(align=True)
        sub.prop(settings, "use_x", toggle=True)
        sub.prop(settings, "use_y", toggle=True)
        sub.prop(settings, "use_z", toggle=True)
    
        # 反转设置 # Invert settings
        row = layout.row()
        row.label(text="Invert")
        sub = row.row(align=True)
        sub.prop(settings, "invert_x", toggle=True)
        sub.prop(settings, "invert_y", toggle=True)
        sub.prop(settings, "invert_z", toggle=True)
    
        # 混合模式 # Mix mode
        layout.prop(settings, "mix_mode")
    
        # 偏移设置 # Offset settings
        layout.prop(settings, "use_offset")
    
    def _draw_scale_settings(self, layout, settings):
        """绘制缩放约束设置"""
        """Draw scale constraint settings"""
        # 轴设置 # Axis settings
        row = layout.row()
        row.label(text="Axis")
        sub = row.row(align=True)
        sub.prop(settings, "use_x", toggle=True)
        sub.prop(settings, "use_y", toggle=True)
        sub.prop(settings, "use_z", toggle=True)
    
        # 乘方设置 # Power settings
        layout.prop(settings, "power")
    
        # 偏移设置 # Offset settings
        layout.prop(settings, "use_offset")
        
    def _draw_transform_settings(self, layout, settings):
        """绘制变换约束设置"""
        """Draw transform constraint settings"""
        layout.prop(settings, "mix_mode")
    
    def execute(self, context):
        active_obj = context.active_object
        selected_objs = [obj for obj in context.selected_objects 
                        if obj != active_obj and obj.type == 'ARMATURE']
        
        if not active_obj or active_obj.type != 'ARMATURE':
            self.report({'ERROR'}, "Active object must be an armature")
            return {'CANCELLED'}
        
        if not selected_objs:
            self.report({'ERROR'}, "Please select at least one target armature")
            return {'CANCELLED'}
        
        settings = context.scene.bone_constraint_settings
        constraint_type = settings.constraint_type
        
        total_constraints_added = 0
        skipped_constraints = 0
        
        for target_obj in selected_objs:
            if target_obj.type != 'ARMATURE':
                continue
                
            constraints_added = self._add_constraints_to_armature(
                active_obj, target_obj, constraint_type, settings
            )
            total_constraints_added += constraints_added[0]
            skipped_constraints += constraints_added[1]
        
        self.report({'INFO'}, "Successfully added {0} constraints, skipped {1} existing constraints".format(
            total_constraints_added, skipped_constraints))
        return {'FINISHED'}
    
    def _add_constraints_to_armature(self, source_armature, target_armature, constraint_type, settings):
        """为骨架添加约束"""
        """Add constraints to armature"""
        constraints_added = 0
        skipped = 0
        
        source_bones = source_armature.pose.bones
        target_bones = target_armature.pose.bones
        
        for target_bone in target_bones:
            if target_bone.name in source_bones:
                source_bone = source_bones[target_bone.name]
                
                if not self._has_existing_constraint(target_bone, constraint_type, source_armature, source_bone.name):
                    self._add_single_constraint(target_bone, source_armature, source_bone.name, constraint_type, settings)
                    constraints_added += 1
                else:
                    skipped += 1
        
        return constraints_added, skipped
    
    def _has_existing_constraint(self, bone, constraint_type, target_armature, target_bone_name):
        """检查骨骼是否已经存在相同类型的约束"""
        """Check if bone already has same type of constraint"""
        for constraint in bone.constraints:
            if (constraint.type == constraint_type and 
                constraint.target == target_armature and
                constraint.subtarget == target_bone_name):
                return True
        return False
    
    def _add_single_constraint(self, bone, target_armature, target_bone_name, constraint_type, settings):
        """为单个骨骼添加约束"""
        """Add single constraint to bone"""
        constraint = bone.constraints.new(type=constraint_type)
        constraint.target = target_armature
        constraint.subtarget = target_bone_name
        
        # 设置基础属性 # Set basic properties
        constraint.influence = settings.influence
        
        # 设置空间属性 # Set space properties
        if hasattr(constraint, 'target_space'):
            constraint.target_space = settings.target_space
        if hasattr(constraint, 'owner_space'):
            constraint.owner_space = settings.owner_space
        
        # 设置约束特定属性 # Set constraint-specific properties
        if constraint_type == 'COPY_LOCATION':
            self._setup_location_constraint(constraint, settings)
        elif constraint_type == 'COPY_ROTATION':
            self._setup_rotation_constraint(constraint, settings)
        elif constraint_type == 'COPY_SCALE':
            self._setup_scale_constraint(constraint, settings)
        elif constraint_type == 'COPY_TRANSFORMS':
            self._setup_transform_constraint(constraint, settings)
    
    def _setup_location_constraint(self, constraint, settings):
        """设置位置约束属性"""
        """Setup location constraint properties"""
        constraint.use_x = settings.use_x
        constraint.use_y = settings.use_y
        constraint.use_z = settings.use_z
        constraint.invert_x = settings.invert_x
        constraint.invert_y = settings.invert_y
        constraint.invert_z = settings.invert_z
        constraint.use_offset = settings.use_offset
    
    def _setup_rotation_constraint(self, constraint, settings):
        """设置旋转约束属性"""
        """Setup rotation constraint properties"""
        constraint.use_x = settings.use_x
        constraint.use_y = settings.use_y
        constraint.use_z = settings.use_z
        constraint.invert_x = settings.invert_x
        constraint.invert_y = settings.invert_y
        constraint.invert_z = settings.invert_z
        constraint.mix_mode = settings.mix_mode
        constraint.use_offset = settings.use_offset
    
    def _setup_scale_constraint(self, constraint, settings):
        """设置缩放约束属性"""
        """Setup scale constraint properties"""
        constraint.use_x = settings.use_x
        constraint.use_y = settings.use_y
        constraint.use_z = settings.use_z
        constraint.power = settings.power
        constraint.use_offset = settings.use_offset
    
    def _setup_transform_constraint(self, constraint, settings):
        """设置变换约束属性"""
        """Setup transform constraint properties"""
        constraint.mix_mode = settings.mix_mode

class ANIM_OT_remove_bone_constraints(Operator):
    """从选中骨架移除骨骼约束"""
    """Remove bone constraints from selected armatures"""
    bl_idname = "anim.remove_bone_constraints"
    bl_label = "Remove Bone Constraints"
    bl_description = "Remove specified type of bone constraints from selected armatures"
    bl_options = {'REGISTER', 'UNDO'}
    
    constraint_type: EnumProperty(
        name="Constraint Type",
        description="Select the constraint Type to remove",
        items=CONSTRAINT_TYPES + [('ALL', "All", "Remove all types of constraints")],
        default='ALL'
    )
    
    @classmethod
    def poll(cls, context):
        return (context.active_object and 
                context.active_object.type == 'ARMATURE' and
                len(context.selected_objects) >= 1)
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
    
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "constraint_type")
    
    def execute(self, context):
        selected_objs = [obj for obj in context.selected_objects if obj.type == 'ARMATURE']
        
        if not selected_objs:
            self.report({'ERROR'}, "Please select at least one armature")
            return {'CANCELLED'}
        
        total_constraints_removed = 0
        
        for armature in selected_objs:
            constraints_removed = self._remove_constraints_from_armature(armature, self.constraint_type)
            total_constraints_removed += constraints_removed
        
        constraint_type_name = "All" if self.constraint_type == 'ALL' else self.constraint_type
        self.report({'INFO'}, "Removed {0} {1} constraints from {2} armatures".format(
            total_constraints_removed, constraint_type_name, len(selected_objs)))
        return {'FINISHED'}
    
    def _remove_constraints_from_armature(self, armature, constraint_type):
        """从骨架移除约束"""
        """Remove constraints from armature"""
        constraints_removed = 0
        
        for bone in armature.pose.bones:
            for i in range(len(bone.constraints) - 1, -1, -1):
                constraint = bone.constraints[i]
                if constraint_type == 'ALL' or constraint.type == constraint_type:
                    bone.constraints.remove(constraint)
                    constraints_removed += 1
        
        return constraints_removed

class ANIM_OT_remove_specific_bone_constraints(Operator):
    """移除特定目标的骨骼约束"""
    """Remove specific target bone constraints"""
    bl_idname = "anim.remove_specific_bone_constraints"
    bl_label = "Remove Specific Constraints"
    bl_description = "Remove constraints pointing to active armature"
    bl_options = {'REGISTER', 'UNDO'}
    
    constraint_type: EnumProperty(
        name="Constraint Type",
        description="Select the constraint type to remove",
        items=CONSTRAINT_TYPES + [('ALL', "All", "Remove all types of constraints")],
        default='ALL'
    )
    
    @classmethod
    def poll(cls, context):
        return (context.active_object and 
                context.active_object.type == 'ARMATURE' and
                len(context.selected_objects) >= 2)
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
    
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "constraint_type")
    
    def execute(self, context):
        active_obj = context.active_object
        selected_objs = [obj for obj in context.selected_objects if obj != active_obj and obj.type == 'ARMATURE']
        
        if not active_obj or active_obj.type != 'ARMATURE':
            self.report({'ERROR'}, "Active object must be an armature")
            return {'CANCELLED'}
        
        if not selected_objs:
            self.report({'ERROR'}, "Please select at least one target armature")
            return {'CANCELLED'}
        
        total_constraints_removed = 0
        
        for target_obj in selected_objs:
            constraints_removed = self._remove_specific_constraints(target_obj, active_obj, self.constraint_type)
            total_constraints_removed += constraints_removed
        
        constraint_type_name = "All" if self.constraint_type == 'ALL' else self.constraint_type
        self.report({'INFO'}, "Removed {0} constraints pointing to active armature of type {1}".format(
            total_constraints_removed, constraint_type_name))
        return {'FINISHED'}
    
    def _remove_specific_constraints(self, armature, target_armature, constraint_type):
        """移除指向特定骨架的约束"""
        """Remove constraints pointing to specific armature"""
        constraints_removed = 0
        
        for bone in armature.pose.bones:
            for i in range(len(bone.constraints) - 1, -1, -1):
                constraint = bone.constraints[i]
                if (constraint.target == target_armature and
                    (constraint_type == 'ALL' or constraint.type == constraint_type)):
                    bone.constraints.remove(constraint)
                    constraints_removed += 1
        
        return constraints_removed

class VIEW3D_MT_batch_constraint_menu(Menu):
    """批量骨骼约束菜单"""
    """Batch Bone Constraints Menu"""
    bl_label = "Batch Bone Constraints"
    bl_idname = "VIEW3D_MT_batch_constraint_menu"
    
    @classmethod
    def poll(cls, context):
        return (context.active_object and 
                context.active_object.type == 'ARMATURE')
    
    def draw(self, context):
        layout = self.layout
        
        layout.operator(
            "anim.add_bone_constraints", 
            text="Batch Add Bone Constraints", 
            icon='CONSTRAINT_BONE'
        )
        
        layout.separator()

        layout.operator(
            "anim.remove_specific_bone_constraints", 
            text="Remove Constraints Pointing to Active", 
            icon='X'
        )
        
        layout.operator(
            "anim.remove_bone_constraints", 
            text="Remove All Bone Constraints", 
            icon='TRASH'
        )

def draw_batch_menu(self, context):
    """在标题栏绘制批骨约束菜单"""
    """Draw batch bone constraints menu in header"""
    if context.active_object and context.active_object.type == 'ARMATURE':
        self.layout.menu("VIEW3D_MT_batch_constraint_menu", text="Batch Bone Constraints")

# 类列表 # Class list
classes = (
    BoneConstraintSettings,
    ANIM_OT_add_bone_constraints,
    ANIM_OT_remove_bone_constraints,
    ANIM_OT_remove_specific_bone_constraints,
    VIEW3D_MT_batch_constraint_menu,
)

def register():
    # 注册类 # Register classes
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # 注册场景属性 # Register scene properties
    bpy.types.Scene.bone_constraint_settings = PointerProperty(type=BoneConstraintSettings)
    
    # 注册菜单 # Register menu
    bpy.types.VIEW3D_MT_editor_menus.append(draw_batch_menu)

def unregister():
    # 注销菜单 # Unregister menu
    bpy.types.VIEW3D_MT_editor_menus.remove(draw_batch_menu)
    
    # 注销场景属性 # Unregister scene properties
    if hasattr(bpy.types.Scene, 'bone_constraint_settings'):
        del bpy.types.Scene.bone_constraint_settings
    
    # 注销类 # Unregister classes
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()