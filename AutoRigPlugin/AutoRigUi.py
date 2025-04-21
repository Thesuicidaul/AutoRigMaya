import sys
import os
sys.path.append("A:/Rangement/Etribart/AutoRigPlugin")
from PySide2.QtGui import *
from PySide2.QtCore import *
from PySide2.QtWidgets import *
import maya.OpenMayaUI as mui
import shiboken2
import maya.cmds as cmds
import AutoRigCore as arc  # Import des fonctions utilitaires

def get_maya_window():
    """Récupère la fenêtre principale de Maya."""
    main_window_ptr = mui.MQtUtil.mainWindow()
    return shiboken2.wrapInstance(int(main_window_ptr), QWidget)

class AutoRigUI(QDialog):
    def __init__(self, parent=get_maya_window()):
        super().__init__(parent)
        self.setWindowTitle("AutoRig")
        self.setFixedSize(400, 500)
        self.setWindowFlags(Qt.Window)

        self.main_layout = QVBoxLayout(self)

        # Partie initiale de l'interface : Sélection du type de rig
        self.rig_type_label = QLabel("Type de Rig:")
        self.rig_type_combo = QComboBox()
        self.rig_type_combo.addItems(["Biped", "Quadruped", "Autre"])
        
        self.create_button = QPushButton("Créer")
        
        top_layout = QHBoxLayout()
        top_layout.addWidget(self.rig_type_label)
        top_layout.addWidget(self.rig_type_combo)
        top_layout.addWidget(self.create_button)
        
        # Layout principal (sélection du type de rig)
        self.initial_layout = QVBoxLayout()
        self.initial_layout.addLayout(top_layout)

        # Options dynamiques
        self.options_widget = QWidget()
        self.options_layout = QVBoxLayout(self.options_widget)
        self.initial_layout.addWidget(self.options_widget)

        self.setup_options()

        # Outils Multi_Join
        tools_group = QGroupBox("Outils")
        tools_layout = QVBoxLayout()

        self.split_button = QPushButton("Scinder")
        self.split_value = QSpinBox()
        self.split_value.setMinimum(2)

        tools_controls = QHBoxLayout()
        tools_controls.addWidget(self.split_button)
        tools_controls.addWidget(self.split_value)

        tools_layout.addLayout(tools_controls)
        tools_group.setLayout(tools_layout)
        self.initial_layout.addWidget(tools_group)

        self.split_button.clicked.connect(self.split_joint)
        
        self.rig_type_combo.currentIndexChanged.connect(self.update_options)

        # Mode guide (initialement caché)
        self.guide_mode_widget = QWidget()
        self.guide_layout = QVBoxLayout(self.guide_mode_widget)

        self.guide_title = QLabel("Guide")
        self.guide_subtitle = QLabel("Déplacer les guides pour la convenance de votre personnage")

        # Création du séparateur
        self.separator = QFrame()
        self.separator.setFrameShape(QFrame.HLine)
        self.separator.setFrameShadow(QFrame.Sunken)

        self.autorig_button = QPushButton("AutoRig")

        self.guide_layout.addWidget(self.guide_title)
        self.guide_layout.addWidget(self.separator)
        self.guide_layout.addWidget(self.guide_subtitle)
        self.guide_layout.addWidget(self.autorig_button)

        # Connecter les boutons
        self.create_button.clicked.connect(self.on_create_button_click)
        self.autorig_button.clicked.connect(self.on_autorig_button_click)

        # Initialiser l'interface avec le layout de sélection de rig
        self.main_layout.addLayout(self.initial_layout)

    def setup_options(self):
        """Crée les options dynamiques."""
        # Squash and Stretch
        squash_group = QGroupBox("Squash and Stretch")
        squash_layout = QVBoxLayout()
        
        self.squash_check = QCheckBox("Activer")
        self.squash_options = [QCheckBox(text) for text in ["Jambe Gauche", "Jambe Droite", "Bras Gauche", "Bras Droit", "Nuque", "Ventre"]]
        
        squash_layout.addWidget(self.squash_check)
        for box in self.squash_options:
            squash_layout.addWidget(box)
            box.setEnabled(False)
        
        squash_group.setLayout(squash_layout)
        self.options_layout.addWidget(squash_group)
        
        self.squash_check.stateChanged.connect(self.toggle_squash_options)
        
        # Bendable
        bendable_group = QGroupBox("Bendable")
        bendable_layout = QVBoxLayout()
        
        self.bendable_check = QCheckBox("Activer")
        self.bendable_options = [QCheckBox(text) for text in ["Bras Gauche", "Bras Droit", "Jambe Gauche", "Jambe Droite"]]
        
        bendable_layout.addWidget(self.bendable_check)
        for box in self.bendable_options:
            bendable_layout.addWidget(box)
            box.setEnabled(False)
        
        bendable_group.setLayout(bendable_layout)
        self.options_layout.addWidget(bendable_group)
        
        self.bendable_check.stateChanged.connect(self.toggle_bendable_options)
        
        # Déplacement Symétrique
        symmetry_group = QGroupBox("Déplacement Symétrique")
        symmetry_layout = QVBoxLayout()
        
        self.symmetry_check = QCheckBox("Activer")
        self.symmetry_options = [QCheckBox(text) for text in ["Bras", "Jambe"]]
        
        symmetry_layout.addWidget(self.symmetry_check)
        for box in self.symmetry_options:
            symmetry_layout.addWidget(box)
            box.setEnabled(False)
        
        symmetry_group.setLayout(symmetry_layout)
        self.options_layout.addWidget(symmetry_group)
        
        self.symmetry_check.stateChanged.connect(self.toggle_symmetry_options)

    def toggle_squash_options(self, state):
        for box in self.squash_options:
            box.setEnabled(state == Qt.Checked)
    
    def toggle_bendable_options(self, state):
        for box in self.bendable_options:
            box.setEnabled(state == Qt.Checked)
    
    def toggle_symmetry_options(self, state):
        for box in self.symmetry_options:
            box.setEnabled(state == Qt.Checked)

    def update_options(self):
        rig_type = self.rig_type_combo.currentText()
        self.options_widget.setVisible(rig_type == "Biped")
    
        if rig_type == "Quadruped":
            # Ajoute ici les options spécifiques aux quadrupèdes
            pass
        elif rig_type == "Autre":
            # Cache ou affiche des options spécifiques
            pass

    def split_joint(self):
        """Divise un joint sélectionné en plusieurs joints définis par la valeur du spinbox."""
        selected_joints = cmds.ls(selection=True, type="joint")
        if not selected_joints:
            cmds.warning("Aucun joint sélectionné!")
            return

        joint = selected_joints[0]
        num_splits = self.split_value.value()
        arc.split_joint(joint, num_splits)

    def on_create_button_click(self):
        rig_type = self.rig_type_combo.currentText()
        arc.realiser(f"A:/Rangement/Etribart/AutoRigPlugin/{rig_type.lower()}.json")
        self.show_guide_mode()

    def show_guide_mode(self):
        self.new_window = QDialog(parent=get_maya_window())
        self.new_window.setWindowTitle("Mode Guide")
        self.new_window.setFixedSize(400, 300)
        self.new_window.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
    
        guide_layout = QVBoxLayout(self.new_window)
    
        # Nouveau bouton AutoRig pour cette fenêtre
        autorig_button_guide = QPushButton("AutoRig")
        autorig_button_guide.clicked.connect(self.on_autorig_button_click)
    
        
    
        guide_layout.addWidget(QLabel("Guide"))
        guide_layout.addWidget(self.separator)
        guide_layout.addWidget(QLabel("Déplacer les guides pour la convenance de votre personnage"))
        guide_layout.addWidget(autorig_button_guide)
    
        self.new_window.show()

    def on_autorig_button_click(self):
        rig_type = self.rig_type_combo.currentText()

        options = {
            "squash": self.squash_check.isChecked(),
            "squash_parts": [box.text() for box in self.squash_options if box.isChecked()],
            "bendable": self.bendable_check.isChecked(),
            "bendable_parts": [box.text() for box in self.bendable_options if box.isChecked()],
            "symmetry": self.symmetry_check.isChecked(),
            "symmetry_parts": [box.text() for box in self.symmetry_options if box.isChecked()]
        }

        if rig_type == "Biped":
            arc.Crig_Bp(options)
        elif rig_type == "Quadruped":
            if hasattr(arc, "Crig_Qd"):
                arc.Crig_Qd(options)
            else:
                cmds.warning("Fonction Crig_Qd non implémentée.")
        elif rig_type == "Autre":
            if hasattr(arc, "Crig_Custom"):
                arc.Crig_Custom(options)
            else:
                cmds.warning("Fonction Crig_Custom non implémentée.")


if __name__ == "__main__":
    try:
        for widget in get_maya_window().findChildren(AutoRigUI):
            widget.close()
    except:
        pass

    window = AutoRigUI()
    window.show()
