import json
import maya.cmds as cmds

def realiser(file):
    """
    Lit un fichier JSON, recrée les objets avec `C_Curve`, puis applique les hiérarchies.
    Effectue ensuite une symétrie sur certains objets spécifiques.
    """
    try:
        with open(file, 'r') as json_file:
            data = json.load(json_file)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        cmds.warning(f"Erreur lors de la lecture du fichier : {e}")
        return

    created_objects = {}  # Stocke les objets créés
    parent_relations = []  # Stocke les relations parent-enfant

    # Étape 1 : Création de tous les objets
    for obj_data in data:
        obj_type = obj_data.get('type')
        name = obj_data.get('name')
        position = obj_data.get('position', [0, 0, 0])
        orientation = obj_data.get('orientation', [0, 0, 0])
        scale = obj_data.get('scale', [1, 1, 1])  # Récupère la scale
        color = obj_data.get('color', 0) or 0  # Blanc par défaut

        # Création de l'objet via C_Curve
        created_obj = C_Curve(obj_type, name, position, orientation, color, scale)
        if not created_obj:
            cmds.warning(f"Impossible de créer l'objet {name}")
            continue

        created_objects[name] = created_obj  # Stocker l'objet

        # Gestion du parentage
        hierarchy = obj_data.get('hierarchy', [])
        if hierarchy:
            parent_name = hierarchy[-1]  # Récupérer le parent immédiat
            parent_relations.append((created_obj, parent_name))

    # Étape 2 : Application du parentage une fois que tout est créé
    for child_obj, parent_name in parent_relations:
        if parent_name in created_objects:
            cmds.parent(child_obj, created_objects[parent_name])
        else:
            cmds.warning(f"Parent {parent_name} non trouvé pour {child_obj}")

    # Étape 3 : Appliquer la symétrie sur certaines parties
    m_shoulder = symetrie("G_Shoulder_R", axe="x")
    m_hip = symetrie("G_Hip_R", axe="x")

    if m_shoulder and cmds.objExists("G_Chest"):
        cmds.parent(m_shoulder, "G_Chest")
    if m_hip and cmds.objExists("G_Hips"):
        cmds.parent(m_hip, "G_Hips")


    print(f"Les objets ont été créés, parentés, et la symétrie a été appliquée à partir de {file}.")



def C_Curve(obj_type, name, position, orientation, color_num, scale):
    """
    Crée une forme en fonction du type et applique position, orientation, scale et couleur.

    :param obj_type: Type de la forme ("Circle", "CubL", "SphL", "Grp")
    :param name: Nom de l'objet
    :param position: Position [x, y, z]
    :param orientation: Rotation [x, y, z]
    :param color_num: Couleur override (entier)
    :param scale: Échelle [x, y, z]
    :return: Nom de l'objet créé
    """

    obj = None

    if obj_type == "Circle":
        obj = cmds.circle(n=name, radius=3, normal=[0, 1, 0], constructionHistory=False)[0]

    elif obj_type == "CubL":
        obj = cmds.group(empty=True, name=name)
        
        # Création d'un cube en NURBS (taille 0.15)
        cube_size = 0.075
        cube = cmds.curve(d=1, p=[[-cube_size, -cube_size, -cube_size], [-cube_size, -cube_size,  cube_size], 
                                  [ cube_size, -cube_size,  cube_size], [ cube_size, -cube_size, -cube_size], 
                                  [-cube_size, -cube_size, -cube_size], [-cube_size,  cube_size, -cube_size], 
                                  [ cube_size,  cube_size, -cube_size], [ cube_size,  cube_size,  cube_size], 
                                  [-cube_size,  cube_size,  cube_size], [-cube_size,  cube_size, -cube_size], 
                                  [-cube_size,  cube_size,  cube_size], [-cube_size, -cube_size,  cube_size], 
                                  [ cube_size, -cube_size,  cube_size], [ cube_size,  cube_size,  cube_size], 
                                  [ cube_size,  cube_size, -cube_size], [ cube_size, -cube_size, -cube_size]
        ], k=list(range(16)))
        cmds.parent(cmds.listRelatives(cube, shapes=True)[0], obj, shape=True, relative=True)
        cmds.delete(cube)

        # Croisillons
        for axis in [[1, 0, 0], [0, 1, 0], [0, 0, 1]]:
            cross = cmds.curve(d=1, p=[[-0.125 * axis[0], -0.125 * axis[1], -0.125 * axis[2]], 
                                       [0.125 * axis[0], 0.125 * axis[1], 0.125 * axis[2]]], 
                               k=[0, 1])
            cmds.parent(cmds.listRelatives(cross, shapes=True)[0], obj, shape=True, relative=True)
            cmds.delete(cross)

    elif obj_type == "SphL":
        obj = cmds.group(empty=True, name=name)

        for axis in [[1, 0, 0], [0, 1, 0], [0, 0, 1]]:
            circle = cmds.circle(nr=axis, radius=0.15, constructionHistory=False)[0]
            cmds.parent(cmds.listRelatives(circle, shapes=True)[0], obj, shape=True, relative=True)
            cmds.delete(circle)

        for axis in [[1, 0, 0], [0, 1, 0], [0, 0, 1]]:
            cross = cmds.curve(d=1, p=[[-0.125 * axis[0], -0.125 * axis[1], -0.125 * axis[2]], 
                                       [0.125 * axis[0], 0.125 * axis[1], 0.125 * axis[2]]], 
                               k=[0, 1])
            cmds.parent(cmds.listRelatives(cross, shapes=True)[0], obj, shape=True, relative=True)
            cmds.delete(cross)

    elif obj_type == "Grp":
        obj = cmds.group(empty=True, name=name)

    else:
        cmds.warning(f"Type inconnu : {obj_type}")
        return None

     # Appliquer la position, orientation et scale correctement
    cmds.xform(obj, translation=position, rotation=orientation, worldSpace=True)

    # Appliquer le scale de manière explicite sur les axes X, Y, Z
    cmds.setAttr(f"{obj}.scale", scale[0], scale[1], scale[2])

    # Appliquer la couleur via override
    shape_nodes = cmds.listRelatives(obj, shapes=True, fullPath=True) or []
    for shape in shape_nodes:
        cmds.setAttr(f"{shape}.overrideEnabled", 1)
        cmds.setAttr(f"{shape}.overrideColor", color_num)

    return obj
    
    









def inverse_suffix(name):
    parts = name.split("_")
    if len(parts) < 2:
        return name  # Aucun suffixe détecté

    suffix = parts[-1]
    base = "_".join(parts[:-1])

    if suffix in ["R", "R1"]:
        return f"{base}_L"
    elif suffix in ["L", "L1"]:
        return f"{base}_R"
    return name


def rename_hierarchy(obj):
    """
    Renomme récursivement un objet et ses enfants en inversant le suffixe.
    """
    short_name = obj.split("|")[-1]
    new_short_name = inverse_suffix(short_name)

    if new_short_name != short_name:
        parent_path = "|".join(obj.split("|")[:-1])
        new_full_name = cmds.rename(obj, new_short_name)
        obj = f"{parent_path}|{new_short_name}" if parent_path else new_full_name

    children = cmds.listRelatives(obj, children=True, fullPath=True) or []
    for child in children:
        rename_hierarchy(child)

    return obj


def symetrie(obj, axe='x'):
    """
    Duplique un objet, inverse les noms (_L1 <-> _R1), 
    groupe sous M_<partie>, applique une inversion de scale.
    """
    if not cmds.objExists(obj):
        cmds.warning(f"L'objet {obj} n'existe pas.")
        return None

    dup = cmds.duplicate(obj, renameChildren=True)[0]
    dup = rename_hierarchy(dup)

    # Nettoyage du nom pour créer le nom de groupe
    parts = obj.split("_")

    # Retirer 'G' si présent au début
    if parts[0] == "G":
        parts = parts[1:]

    # Retirer le suffixe de côté s’il est présent
    if parts[-1] in ["R", "R1", "L", "L1"]:
        parts = parts[:-1]

    base = "_".join(parts)
    grp = cmds.group(empty=True, name=f'M_{base}')
    cmds.parent(dup, grp)

    axe_index = {'x': 0, 'y': 1, 'z': 2}[axe.lower()]
    scale = [1, 1, 1]
    scale[axe_index] = -1

    cmds.setAttr(f'{grp}.scaleX', scale[0])
    cmds.setAttr(f'{grp}.scaleY', scale[1])
    cmds.setAttr(f'{grp}.scaleZ', scale[2])

    return grp


###############################
############################# Boite a outils
###############################


def split_joint(joint, num_splits):
    """Divise un joint sélectionné en plusieurs joints définis par la valeur du spinbox."""
    if not cmds.objExists(joint) or cmds.nodeType(joint) != "joint":
        cmds.warning("Le joint sélectionné n'est pas valide.")
        return
    
    children = cmds.listRelatives(joint, children=True, type="joint")
    if not children:
        cmds.warning("Le joint sélectionné n'a pas d'enfants à scinder.")
        return
    
    child = children[0]  # Utilise le premier enfant pour la position de fin
    start_pos = cmds.xform(joint, query=True, worldSpace=True, translation=True)
    end_pos = cmds.xform(child, query=True, worldSpace=True, translation=True)
    
    prev_joint = joint
    for i in range(1, num_splits + 1):
        factor = i / float(num_splits + 1)
        new_pos = [(1 - factor) * start_pos[j] + factor * end_pos[j] for j in range(3)]
        new_joint_name = f"{joint}_Mid_{i}"
        new_joint = cmds.joint(position=new_pos, name=new_joint_name)
        
        
        # Vérifie si la parenté est correcte
        if cmds.listRelatives(new_joint, parent=True) != [prev_joint]:
            cmds.parent(new_joint, prev_joint)
        
        prev_joint = new_joint
    
    # Parent l'enfant original au dernier joint
    if cmds.listRelatives(child, parent=True) != [prev_joint]:
        cmds.parent(child, prev_joint)





##################################
############################    Partie création de Join
##################################




def Crig_Bp(options):
    """
    Crée un rig Biped en fonction des options passées depuis l'interface utilisateur.
    """
    
    # Création du contrôleur global avec une courbe carré arrondi
    if not cmds.objExists("C_World"):
        # Créer un cercle de base pour les bords arrondis
        world_ctrl = cmds.circle(name="C_World", normal=[0, 1, 0], radius=5, sections=8)[0]

        # Appliquer une couleur rouge
        cmds.setAttr(f"{world_ctrl}.overrideEnabled", 1)
        cmds.setAttr(f"{world_ctrl}.overrideColor", 13)  # Rouge
        print(">> Contrôleur principal 'C_World' créé.")
        
        # Ajouter des attributs de séparateur pour chaque partie du corps
        cmds.addAttr(world_ctrl, longName="Arm_Control", at="enum", enumName="----", keyable=False)
        
        # Séparateur gauche/droite pour les bras
        cmds.addAttr(world_ctrl, longName="Left_Arm_Control", at="enum", enumName="----", keyable=False)
        cmds.addAttr(world_ctrl, longName="IK_FK_Arm_L", at="enum", enumName="IK:FK", keyable=True)
        cmds.addAttr(world_ctrl, longName="Bendable_Arm_L", at="bool", keyable=True)
        cmds.addAttr(world_ctrl, longName="Squash_Stretch_Arm_L", at="bool", keyable=True)

        cmds.addAttr(world_ctrl, longName="Right_Arm_Control", at="enum", enumName="----", keyable=False)
        cmds.addAttr(world_ctrl, longName="IK_FK_Arm_R", at="enum", enumName="IK:FK", keyable=True)
        cmds.addAttr(world_ctrl, longName="Bendable_Arm_R", at="bool", keyable=True)
        cmds.addAttr(world_ctrl, longName="Squash_Stretch_Arm_R", at="bool", keyable=True)

        cmds.addAttr(world_ctrl, longName="Leg_Control", at="enum", enumName="----", keyable=False)

        # Séparateur gauche/droite pour les jambes
        cmds.addAttr(world_ctrl, longName="Left_Leg_Control", at="enum", enumName="----", keyable=False)
        cmds.addAttr(world_ctrl, longName="IK_FK_Leg_L", at="enum", enumName="IK:FK", keyable=True)
        cmds.addAttr(world_ctrl, longName="Bendable_Leg_L", at="bool", keyable=True)
        cmds.addAttr(world_ctrl, longName="Squash_Stretch_Leg_L", at="bool", keyable=True)

        cmds.addAttr(world_ctrl, longName="Right_Leg_Control", at="enum", enumName="----", keyable=False)
        cmds.addAttr(world_ctrl, longName="IK_FK_Leg_R", at="enum", enumName="IK:FK", keyable=True)
        cmds.addAttr(world_ctrl, longName="Bendable_Leg_R", at="bool", keyable=True)
        cmds.addAttr(world_ctrl, longName="Squash_Stretch_Leg_R", at="bool", keyable=True)

        # Ajouter un nouveau séparateur pour les paramètres de visibilité et de priorité
        cmds.addAttr(world_ctrl, longName="Visibility_Control", at="enum", enumName="----", keyable=False)
        
        # Paramètre pour afficher les contrôles au playblast
        cmds.addAttr(world_ctrl, longName="Show_Controls_Playblast", at="bool", keyable=True)
        
        # Paramètre pour activer/désactiver la visibilité des déformeurs
        cmds.addAttr(world_ctrl, longName="Show_Deformers", at="bool", keyable=True)
        
        # Paramètre pour afficher les contrôles en priorité
        cmds.addAttr(world_ctrl, longName="Priority_Display_Controls", at="bool", keyable=True)

        print(">> Attributs ajoutés au contrôleur 'C_World'.")
        
    squash_enabled = options.get("squash", False)
    squash_parts = options.get("squash_parts", [])

    bendable_enabled = options.get("bendable", False)
    bendable_parts = options.get("bendable_parts", [])

    print("==> Construction du Rig Biped avec les paramètres suivants :")
    print(f"  • Squash: {squash_enabled} → {squash_parts}")
    print(f"  • Bendable: {bendable_enabled} → {bendable_parts}")

    print(">> Création du bras droit...")
    create_arm_rig("R")
    print(">> Création du bras gauche...")
    create_arm_rig("L")

    print(">> Création de la jambe droite...")
    create_leg_rig("R")
    print(">> Création de la jambe gauche...")
    create_leg_rig("L")
    
    # Appliquer les contraintes IK/FK et les switches sur les déformeurs du bras et des jambes
    apply_constraints_and_switch("Arm_L", "Arm_R")
    apply_constraints_and_switch("Leg_L", "Leg_R")

    print("\n✅ Rig Biped généré avec succès.")



def create_arm_rig(side="R"):
    suffix = f"_{side}"

    d_joints = create_deform_joints(suffix, "Arm")
    ik_joints = create_ik_joints(suffix, "Arm")
    pole_vector = create_pole_vector(suffix, limb="Arm")
    ik_handle = create_ik_handle(ik_joints, suffix, pole_vector, limb="Arm")
    split_deformer_chain(d_joints)
    fk_ctrls = create_fk_controls(suffix, "Arm")
    ik_ctrl = create_ik_control(suffix, "Hand")
    cmds.parent(ik_handle, ik_ctrl)
    setup_constraints_and_switch(d_joints, ik_joints, fk_ctrls, ik_ctrl, suffix)


def create_leg_rig(side="R"):
    suffix = f"_{side}"

    d_joints = create_deform_joints(suffix, "Leg")
    ik_joints = create_ik_joints(suffix, "Leg")
    pole_vector = create_pole_vector(suffix, limb="Leg")
    ik_handle = create_ik_handle(ik_joints, suffix, pole_vector, limb="Leg")
    split_deformer_chain(d_joints)
    fk_ctrls = create_fk_controls(suffix, "Leg")
    ik_ctrl = create_ik_control(suffix, "Ankle")
    cmds.parent(ik_handle, ik_ctrl)
    setup_constraints_and_switch(d_joints, ik_joints, fk_ctrls, ik_ctrl, suffix)


def get_guide_position(name):
    return cmds.xform(name, q=True, ws=True, t=True)

def get_guide_rotation(name):
    return cmds.xform(name, q=True, ws=True, ro=True)


def create_deform_joints(suffix, limb):
    names = ["Arm", "ForeArm", "Hand"] if limb == "Arm" else ["Hip", "Knee", "Ankle"]
    guides = [f"G_{n}{suffix}" for n in names]
    joints = []

    cmds.select(clear=True)
    for n, g in zip(names, guides):
        j = cmds.joint(name=f"D_{n}{suffix}")
        cmds.xform(j, ws=True, t=get_guide_position(g), ro=get_guide_rotation(g))
        joints.append(j)

    # Parent uniquement si ce n'est pas déjà fait
    if cmds.objExists(joints[1]) and cmds.objExists(joints[0]):
        if cmds.listRelatives(joints[1], parent=True) != [joints[0]]:
            cmds.parent(joints[1], joints[0])

    if cmds.objExists(joints[2]) and cmds.objExists(joints[1]):
        if cmds.listRelatives(joints[2], parent=True) != [joints[1]]:
            cmds.parent(joints[2], joints[1])

    cmds.select(clear=True)
    return joints



def create_ik_joints(suffix, limb):
    names = ["Arm", "ForeArm", "Hand"] if limb == "Arm" else ["Hip", "Knee", "Ankle"]
    guides = [f"G_{n}{suffix}" for n in names]
    joints = []

    cmds.select(clear=True)
    for n, g in zip(names, guides):
        j = cmds.joint(name=f"Ik_{n}{suffix}")
        cmds.xform(j, ws=True, t=get_guide_position(g), ro=get_guide_rotation(g))
        joints.append(j)

    # Parent uniquement si nécessaire
    if cmds.objExists(joints[1]) and cmds.objExists(joints[0]):
        if cmds.listRelatives(joints[1], parent=True) != [joints[0]]:
            cmds.parent(joints[1], joints[0])

    if cmds.objExists(joints[2]) and cmds.objExists(joints[1]):
        if cmds.listRelatives(joints[2], parent=True) != [joints[1]]:
            cmds.parent(joints[2], joints[1])

    cmds.select(clear=True)
    return joints


def create_pole_vector(suffix, limb):
    if limb == "Arm":
        pv_guide = "G_PoleVB_D" if suffix == "_R" else "G_PoleVB_G"
    else:
        pv_guide = "G_PoleVJ_D" if suffix == "_R" else "G_PoleVJ_G"

    pv_joint = f"Ik_PoleV{suffix}_{limb}"

    if not cmds.objExists(pv_guide):
        cmds.warning(f"Pole vector guide {pv_guide} manquant.")
        return None

    cmds.select(clear=True)
    pv = cmds.joint(name=pv_joint)
    cmds.xform(pv, ws=True, t=get_guide_position(pv_guide))
    return pv


def create_ik_handle(joints, suffix, pole_vector, limb):
    handle_name = f"IkHandle_{limb}{suffix}"
    ik_handle = cmds.ikHandle(
        name=handle_name,
        sj=joints[0],
        ee=joints[2],
        sol="ikRPsolver"
    )[0]

    if pole_vector:
        cmds.poleVectorConstraint(pole_vector, ik_handle)

    return ik_handle


def split_deformer_chain(joints):
    for j in joints:
        if j.startswith("D_"):
            split_joint(j, 3)
            # Appliquer les contraintes de rotation X avec des pourcentages via multiplyDivide
            children = cmds.listRelatives(j, c=True, type="joint") or []
            if len(children) >= 3:
                blend_values = [0.2, 0.5, 0.8]
                target_joint = children[-1]  # Le dernier joint est le plus proche du bout
                for i, inter_joint in enumerate(children):
                    mult = cmds.shadingNode("multiplyDivide", asUtility=True, name=f"{inter_joint}_rotX_mult")
                    cmds.setAttr(f"{mult}.operation", 1)  # Multiply
                    cmds.connectAttr(f"{target_joint}.rotateX", f"{mult}.input1X", force=True)
                    cmds.setAttr(f"{mult}.input2X", blend_values[i])
                    cmds.connectAttr(f"{mult}.outputX", f"{inter_joint}.rotateX", force=True)


def create_fk_controls(suffix, limb):
    parts = ["Arm", "ForeArm", "Hand"] if limb == "Arm" else ["Hip", "Knee", "Ankle"]
    guides = [f"G_{p}{suffix}" for p in parts]
    ctrls = []

    for p, g in zip(parts, guides):
        ctrl = cmds.circle(name=f"C_FK_{p}{suffix}", normal=[1, 0, 0], radius=1.5)[0]
        cmds.xform(ctrl, ws=True, t=get_guide_position(g), ro=get_guide_rotation(g))
        ctrls.append(ctrl)

    cmds.parent(ctrls[2], ctrls[1])
    cmds.parent(ctrls[1], ctrls[0])
    return ctrls


def create_ik_control(suffix, end_joint_name):
    guide = f"G_{end_joint_name}{suffix}"
    ctrl = cmds.circle(name=f"C_IK_{end_joint_name}{suffix}", normal=[1, 0, 0], radius=2.0)[0]
    cmds.setAttr(f"{ctrl}.overrideEnabled", 1)
    cmds.setAttr(f"{ctrl}.overrideColor", 13)
    cmds.xform(ctrl, ws=True, t=get_guide_position(guide), ro=get_guide_rotation(guide))
    return ctrl


def setup_constraints_and_switch(d_joints, ik_joints, fk_ctrls, ik_ctrl, suffix):
    """
    Met en place les contraintes IK/FK et gère l'affichage dynamique des contrôleurs.
    """
    # Déterminer l'attribut de switch IK/FK selon le côté et le membre
    if suffix == "_L":
        attr = "C_World.IK_FK_Arm_L" if "Arm" in d_joints[0] else "C_World.IK_FK_Leg_L"
    else:
        attr = "C_World.IK_FK_Arm_R" if "Arm" in d_joints[0] else "C_World.IK_FK_Leg_R"

    # Switch de visibilité contrôlé par l'attribut
    create_ik_fk_switch(attr, fk_ctrls, ik_ctrl)

    # Blending dynamique entre rotations IK/FK → joint de déformation
    for i in range(3):
        blend = cmds.shadingNode("blendColors", asUtility=True, name=f"{d_joints[i]}_Blend")
        cmds.connectAttr(f"{fk_ctrls[i]}.rotate", f"{blend}.color1", force=True)
        cmds.connectAttr(f"{ik_joints[i]}.rotate", f"{blend}.color2", force=True)
        cmds.connectAttr(attr, f"{blend}.blender", force=True)
        cmds.connectAttr(f"{blend}.output", f"{d_joints[i]}.rotate", force=True)

    print(f"Contraintes et switch IK/FK dynamiques configurés pour le membre {suffix}.")
    
    
def create_ik_fk_switch(attr, fk_ctrls, ik_ctrl):
    """
    Crée un système dynamique de visibilité des contrôleurs IK/FK basé sur un attribut booléen ou enum.
    """
    condition_node = cmds.shadingNode("condition", asUtility=True, name=f"{attr}_cond")
    reverse_node = cmds.shadingNode("reverse", asUtility=True, name=f"{attr}_rev")

    # Le node condition active FK quand attr == 0 (FK est visible quand switch est sur 0)
    cmds.connectAttr(attr, f"{condition_node}.firstTerm")
    cmds.setAttr(f"{condition_node}.secondTerm", 0)
    cmds.setAttr(f"{condition_node}.operation", 0)  # Equal
    cmds.setAttr(f"{condition_node}.colorIfTrueR", 0)  # FK visible
    cmds.setAttr(f"{condition_node}.colorIfFalseR", 1)  # FK caché
    cmds.connectAttr(f"{condition_node}.outColorR", f"{fk_ctrls[0]}.visibility")
    cmds.connectAttr(f"{condition_node}.outColorR", f"{fk_ctrls[1]}.visibility")
    cmds.connectAttr(f"{condition_node}.outColorR", f"{fk_ctrls[2]}.visibility")

    # Le node reverse permet de cacher FK et afficher IK quand attr == 1 (IK visible)
    cmds.connectAttr(attr, f"{reverse_node}.inputX")
    cmds.setAttr(f"{reverse_node}.outputX", 1)
    cmds.connectAttr(f"{reverse_node}.outputX", f"{ik_ctrl}.visibility")


def create_constraints(deformer_names, fk_controls, ik_controls):
    """
    Crée des contraintes de parenté entre les déformeurs et les contrôleurs FK et IK.

    Args:
    - deformer_names (list): Liste des noms des joints de déformation (ex: ["D_Arm_L", "D_Forearm_L"]).
    - fk_controls (list): Liste des contrôleurs FK correspondants (ex: ["C_FK_Arm_L", "C_FK_Forearm_L"]).
    - ik_controls (list): Liste des contrôleurs IK correspondants (ex: ["C_IK_Arm_L", "C_IK_Forearm_L"]).

    Returns:
    - dict: Dictionnaire contenant les contraintes pour chaque déformeur.
    """
    constraints = {}

    # Créer les contraintes de parenté
    for i, deformer in enumerate(deformer_names):
        # Créer les contraintes FK et IK
        fk_constraint = cmds.parentConstraint(fk_controls[i], deformer, maintainOffset=True)[0]
        ik_constraint = cmds.parentConstraint(ik_controls[i], deformer, maintainOffset=True)[0]
        
        # Initialement, désactiver les deux contraintes
        cmds.setAttr(f"{fk_constraint}.weight", 0)
        cmds.setAttr(f"{ik_constraint}.weight", 0)

        constraints[deformer] = {"fk": fk_constraint, "ik": ik_constraint}

    return constraints

def switch_constraints(constraints, switch_type):
    """
    Active ou désactive les contraintes en fonction du mode (IK ou FK).

    Args:
    - constraints (dict): Dictionnaire des contraintes pour chaque déformeur.
    - switch_type (str): Le type de switch ("IK" ou "FK").
    """
    if switch_type == "IK":
        for deformer, cons in constraints.items():
            # Activer la contrainte IK et désactiver la contrainte FK
            cmds.setAttr(f"{cons['fk']}.weight", 0)
            cmds.setAttr(f"{cons['ik']}.weight", 1)
    elif switch_type == "FK":
        for deformer, cons in constraints.items():
            # Activer la contrainte FK et désactiver la contrainte IK
            cmds.setAttr(f"{cons['fk']}.weight", 1)
            cmds.setAttr(f"{cons['ik']}.weight", 0)
    else:
        cmds.error(f"Le type de switch '{switch_type}' est invalide. Utilise 'IK' ou 'FK'.")

def apply_constraints_and_switch(world_node, deformer_names, fk_controls, ik_controls):
    """
    Applique les contraintes et gère le switch entre IK et FK en fonction de l'attribut du node 'C_World'.

    Args:
    - world_node (str): Le nom du node `C_World` contenant l'attribut de switch.
    - deformer_names (list): Liste des noms des joints de déformation (ex: ["D_Arm_L", "D_Forearm_L"]).
    - fk_controls (list): Liste des contrôleurs FK correspondants (ex: ["C_FK_Arm_L", "C_FK_Forearm_L"]).
    - ik_controls (list): Liste des contrôleurs IK correspondants (ex: ["C_IK_Arm_L", "C_IK_Forearm_L"]).
    """
    # Récupérer l'état du switch depuis l'attribut du node 'C_World' (exemple: 'C_World.switchIKFK')
    try:
        switch_type = cmds.getAttr(f"{world_node}.switchIKFK")  # Assure-toi que l'attribut existe
    except:
        cmds.error(f"L'attribut 'switchIKFK' n'existe pas sur '{world_node}'.")

    # Créer les contraintes de parenté
    constraints = create_constraints(deformer_names, fk_controls, ik_controls)

    # Appliquer le switch en fonction de l'attribut de 'C_World'
    switch_constraints(constraints, switch_type)