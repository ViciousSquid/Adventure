# flowchart.py

import graphviz
from PyQt5.QtWidgets import QApplication, QGraphicsView, QGraphicsScene, QLineEdit
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import QByteArray
from graphviz import Source

def generate_flowchart_image(story_editor_widget):
    dot = graphviz.Digraph(comment='Story Flowchart')

    start_room = story_editor_widget.startRoomInput.currentText()
    dot.node('start', start_room, shape='rectangle')

    for i in range(story_editor_widget.roomsTabWidget.count()):
        room_widget = story_editor_widget.roomsTabWidget.widget(i)
        room_name = room_widget.roomNameInput.text()
        room_node = dot.node(room_name, room_name, shape='rectangle')

        room_data = {
            'description': room_widget.roomDescriptionInput.toPlainText(),
            'exits': {}
        }

        for j in range(room_widget.exitsLayout.count()):
            exit_widget = room_widget.exitsLayout.itemAt(j).widget()
            exit_name_input = exit_widget.findChild(QLineEdit, "exitNameInput")
            exit_name = exit_name_input.text() if exit_name_input else ''
            exit_destination_input = exit_widget.findChild(QLineEdit, "exitDestinationInput")
            exit_destination = exit_destination_input.text() if exit_destination_input else ''

            if exit_widget.skillCheckData:
                room_data['exits'][exit_name] = {'skill_check': exit_widget.skillCheckData}
            else:
                room_data['exits'][exit_name] = exit_destination

            if isinstance(room_data['exits'][exit_name], str):
                destination_node = dot.node(room_data['exits'][exit_name], room_data['exits'][exit_name], shape='rectangle')
                if exit_name:  # Check if exit_name is not None
                    dot.edge(room_node, destination_node, label=exit_name)
            elif isinstance(room_data['exits'][exit_name], dict):
                condition_name = f"{exit_name}_condition"
                condition_node = dot.node(condition_name, exit_name, shape='diamond')
                if exit_name:  # Check if exit_name is not None
                    dot.edge(room_node, condition_node, label=exit_name)

                success_room = room_data['exits'][exit_name]['skill_check']['success']['room']
                failure_room = room_data['exits'][exit_name]['skill_check']['failure']['room']

                success_node = dot.node(success_room, success_room, shape='rectangle') if success_room else None
                failure_node = dot.node(failure_room, failure_room, shape='rectangle') if failure_room else None

                if success_node and failure_node:
                    dot.edge(condition_node, success_node, label='Success')
                    dot.edge(condition_node, failure_node, label='Failure')

    dot.node('start', shape='rectangle')
    dot.edge('start', start_room)

    # Render the flowchart as an image
    flowchart_source = Source(dot.source)
    rendered_image = flowchart_source.render(format='png')

    # Create a QGraphicsScene and QGraphicsView
    flowchart_scene = QGraphicsScene()
    flowchart_view = QGraphicsView(flowchart_scene)
    flowchart_view.setWindowTitle("Story Flowchart")

    # Load the rendered image into the QGraphicsScene
    image_data = QByteArray(rendered_image.encode())
    image = QImage.fromData(image_data)
    pixmap = QPixmap.fromImage(image)
    flowchart_scene.addPixmap(pixmap)

    # Show the QGraphicsView
    flowchart_view.show()

    # Run the event loop if there is no existing event loop
    if not QApplication.instance():
        app = QApplication([])
        app.exec_()