# -*- coding: utf-8 -*-
"""
/***************************************************************************
 AutoFilter
                                 A QGIS plugin
 AutoFilter
                              -------------------
        begin                : 2023-09-07
        git sha              : $Format:%H$
        copyright            : (C) 2023 by Hasan Sami
        email                : hasami@earthlink.iq
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt, QDate
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QMessageBox, QVBoxLayout, QLabel, QDialog, QComboBox, QLineEdit, QPushButton, QDateEdit, QFileDialog
from qgis.core import QgsProject, QgsVectorLayer
from qgis.utils import iface
import os.path
import pandas as pd

# Initialize Qt resources from file resources.py
from .resources import *

class AutoFilter:

    icon_path = ':/plugins/AutoFilter/icon.png'

    @staticmethod
    def icon():
        return QIcon(AutoFilter.icon_path)

    def __init__(self, iface):
        self.iface = iface
        self.tool = None

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""
        # Create action that will start plugin configuration
        self.action = QAction(QIcon(os.path.join(os.path.dirname(__file__), 'icon.png')), 'Single-Filter', self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        
        # Create action for multi-filter options
        self.multi_filter_action = QAction(QIcon(os.path.join(os.path.dirname(__file__), 'MultiFilter')), 'Multi-Filter', self.iface.mainWindow())
        self.multi_filter_action.triggered.connect(self.multiFilter)
        
        # Create action for clearing filters
        self.clear_action = QAction(QIcon(os.path.join(os.path.dirname(__file__), 'mActionDelete.png')), 'Clear Filters', self.iface.mainWindow())
        self.clear_action.triggered.connect(self.clearFilters)

        # Add toolbar buttons and menu items
        self.iface.addToolBarIcon(self.action)
        self.iface.addToolBarIcon(self.multi_filter_action)  # Add the multi-filter icon to the toolbar
        self.iface.addToolBarIcon(self.clear_action)
        self.iface.addPluginToMenu('&AutoFilter', self.action)
        self.iface.addPluginToMenu('&AutoFilter', self.multi_filter_action)  # Add the multi-filter option to the menu
        self.iface.addPluginToMenu('&AutoFilter', self.clear_action)

    def unload(self):
        # Remove the actions when the plugin is unloaded
        self.iface.removeToolBarIcon(self.action)
        self.iface.removeToolBarIcon(self.multi_filter_action)  # Remove the multi-filter icon from the toolbar
        self.iface.removeToolBarIcon(self.clear_action)

    def run(self):
        # Check if there are any layers in the project
        project = QgsProject.instance()
        if not project.mapLayers():
            QMessageBox.warning(None, 'Warning', 'The project is empty. Please add layers to the project before using this plugin.')
            return  # Exit the function

        # Create a QDialog for user input
        dialog = QDialog(self.iface.mainWindow())
        dialog.setWindowTitle('Select Filter Criteria')

        # Define filter criteria options
        filter_criteria_options = ["Exchange", "Route", "Cabinet ID", "Data Provider", "Contractor", "Coordinator", "Rework", "Date", "Period Of Time"]

        # Create a combo box for choosing filter criteria
        combo_box = QComboBox(dialog)
        combo_box.addItems(filter_criteria_options)
        combo_box.setEditable(False)
        combo_box.setCurrentIndex(0)

        # Create a QLineEdit for entering the filter value
        value_input = QLineEdit(dialog)
        
        # Create a QDateEdit widget for entering the date
        date_input = QDateEdit(QDate.currentDate(), dialog)
        date_input.setCalendarPopup(True)
        date_input.setDateRange(QDate(1900, 1, 1), QDate.currentDate())
        
        # Create a QDateEdit widget for entering the start date
        start_date_input = QDateEdit(QDate.currentDate(), dialog)
        start_date_input.setCalendarPopup(True)
        start_date_input.setDateRange(QDate(1900, 1, 1), QDate.currentDate())

        # Create a QDateEdit widget for entering the end date
        end_date_input = QDateEdit(QDate.currentDate(), dialog)
        end_date_input.setCalendarPopup(True)
        end_date_input.setDateRange(QDate(1900, 1, 1), QDate.currentDate())

        # Create a function to update the visibility of input widgets based on combo_box selection
        def update_input_widgets():
            selected_criteria = combo_box.currentText()
            if selected_criteria == "Date":
                value_input.hide()
                start_date_input.hide()
                end_date_input.hide()
                date_input.show()
            elif selected_criteria == "Period Of Time":
                value_input.hide()
                start_date_input.show()
                end_date_input.show()
                date_input.hide()
            else:
                value_input.show()
                start_date_input.hide()
                end_date_input.hide()
                date_input.hide()
                value_input.setPlaceholderText(f'Enter {selected_criteria}')

        # Connect the combo_box's currentIndexChanged signal to the update_input_widgets function
        combo_box.currentIndexChanged.connect(update_input_widgets)

        # Set the initial visibility based on the default selection
        update_input_widgets()

        # Add a label below the combo box
        label = QLabel('Powered By © Hasan Sami', dialog)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Create a QPushButton for confirming the filter
        confirm_button = QPushButton('OK', dialog)
        confirm_button.clicked.connect(dialog.accept)

        # Create a layout for the dialog
        layout = QVBoxLayout()
        layout.addWidget(combo_box)
        layout.addWidget(value_input)
        layout.addWidget(end_date_input)
        layout.addWidget(start_date_input)
        layout.addWidget(date_input)        
        layout.addWidget(confirm_button)
        layout.addWidget(label)
        
        # Set the layout for the dialog
        dialog.setLayout(layout)

        # Show the dialog and get the selected filter criteria and value
        if dialog.exec_() == QDialog.Accepted:
            filter_criteria = combo_box.currentText()
            if filter_criteria == "Date":
                value_to_filter = date_input.date().toString("yyyy-MM-dd")
                if "AND" in value_to_filter:
                    QMessageBox.warning(None, 'Warning', 'Please enter a single date for the "Date" filter.')
                    return  # Exit the function
            elif filter_criteria == "Period Of Time":
                start_date = start_date_input.date().toString("yyyy-MM-dd")
                end_date = end_date_input.date().toString("yyyy-MM-dd")
                if not start_date or not end_date:
                    QMessageBox.warning(None, 'Warning', 'Please select both start and end dates for the "Period of Time" filter.')
                    return  # Exit the function
                value_to_filter = [start_date, end_date]
            else:
                value_to_filter = value_input.text()
                if not value_to_filter:
                    QMessageBox.warning(None, 'Warning', 'Please enter a value for the filter field.')
                    return  # Exit the function

            project = QgsProject.instance()
            layers = project.mapLayers().values()

            for layer in layers:
                if isinstance(layer, QgsVectorLayer):
                    field_to_check = None
                    if filter_criteria == "Cabinet ID":
                        field_to_check = ["Cab_ID_OR_OLT_ID", "FDT_ID", "CAB_OR_OLT_ID", "CAB_ID", "Zone_ID", "ZoneID", "cab_id", "FDT_ID_OR_OLT_ID"]
                    elif filter_criteria == "Route":
                        field_to_check = ["SUB_RingID", "subring_id", "Route_ID"]
                    elif filter_criteria == "Data Provider":
                        field_to_check = ["Data_providor", "Data_Providor", "Data_Provider"]
                    elif filter_criteria == "Contractor":
                        field_to_check = ["Implementing_Contractor", "Implementing_contractor", "Contractor", "contractor_id"]
                    elif filter_criteria == "Coordinator":
                        field_to_check = ["Coordinator"]
                    elif filter_criteria == "Exchange":
                        field_to_check = ["ExchangeID", "Exchange ID"]
                    elif filter_criteria == "Rework":
                        if value_to_filter in ['Yes', 'No']:
                            field_to_check = "Rework"
                        else:
                            QMessageBox.warning(None, 'Warning', 'Please enter "Yes" or "No" for the "Rework" field.')
                            return  # Exit the function
                    elif filter_criteria in ["Date", "Period Of Time"]:
                        field_to_check = ["Installation_Date", "Excavation_Date"]

                    if field_to_check:
                        if isinstance(field_to_check, list):
                            # Check if any of the fields in the list exist in the layer's fields
                            fields = layer.fields()
                            field_names = [field.name() for field in fields]
                            filter_strings = []
                            for field in field_to_check:
                                if field in field_names:
                                    if filter_criteria == "Period Of Time":
                                        # Use BETWEEN operator for date range
                                        start_date, end_date = value_to_filter
                                        filter_strings.append(f'"{field}" BETWEEN \'{end_date}\' AND \'{start_date}\'')
                                    else:
                                        # Use direct action
                                        filter_strings.append(f'"{field}" = \'{value_to_filter}\'')
                            if filter_strings:
                                query = ' OR '.join(filter_strings)
                                layer.setSubsetString(query)
                        else:
                            if field_to_check in layer.fields().names():
                                if filter_criteria == "Period Of Time":
                                    # Use BETWEEN operator for date range
                                    start_date, end_date = value_to_filter
                                    query = f'"{field_to_check}" BETWEEN \'{end_date}\' AND \'{start_date}\''
                                else:
                                    # Use direct action
                                    query = f'"{field_to_check}" = \'{value_to_filter}\''
                                layer.setSubsetString(query)
                            else:
                                layer.setSubsetString("")  # Clear the filter if the field is not present or if no filter value is entered
                        # Refresh the layer to apply the filter
                        layer.triggerRepaint()

        # Deactivate the custom map tool after the action is completed
        if self.tool:
            self.iface.mapCanvas().unsetMapTool(self.tool)
    
    def multiFilter(self):
        # Check if there are any layers in the project
        project = QgsProject.instance()
        if not project.mapLayers():
            QMessageBox.warning(None, 'Warning', 'The project is empty. Please add layers to the project before using this plugin.')
            return  # Exit the function

        # Create a QDialog for multi-filter input
        dialog = QDialog(self.iface.mainWindow())
        dialog.setWindowTitle('Multi-Filter')

        # Define filter criteria options
        filter_criteria_options = ["Exchange", "Route", "Cabinet"]

        # Create a combo box for choosing filter criteria
        combo_box = QComboBox(dialog)
        combo_box.addItems(filter_criteria_options)
        combo_box.setEditable(False)
        combo_box.setCurrentIndex(0)

        # Create a label for choosing the number of values
        num_values_label = QLabel('Number of Values:', dialog)

        # Create a combo box for choosing the number of values
        num_values_combo = QComboBox(dialog)
        num_values_combo.addItems(['2', '3', '4', '5', '6', '7', '8', '9', '10', '11','12', '13', '14', '15', '16', '17', '18', '19', '20','21','22', '23', '24', '25', '26', '27', '28', '29', '30'])
        num_values_combo.setEditable(False)
        num_values_combo.setCurrentIndex(0)

        # Create a list of line edit widgets for entering filter values
        value_inputs = [QLineEdit(dialog) for _ in range(30)]

        # Create a QLabel for the powered by message
        powered_by_label = QLabel('Powered By © Hasan Sami', dialog)
        powered_by_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Create a QPushButton for confirming the multi-filter
        confirm_button = QPushButton('OK', dialog)

        # Create a QPushButton for importing values from Excel
        import_excel_button = QPushButton('Import Values from Excel', dialog)

        # Create a layout for the dialog
        layout = QVBoxLayout()
        layout.addWidget(combo_box)
        layout.addWidget(num_values_label)
        layout.addWidget(num_values_combo)
        for value_input in value_inputs:
            layout.addWidget(value_input)
        layout.addWidget(import_excel_button)  # Add the import Excel button
        layout.addWidget(confirm_button)
        layout.addWidget(powered_by_label)  # Add the powered by label
        
        # Set the layout for the dialog
        dialog.setLayout(layout)

        # Function to update the visibility of value input widgets based on the selected number of values
        def update_value_inputs():
            num_values = int(num_values_combo.currentText())
            for i, input_widget in enumerate(value_inputs):
                input_widget.setVisible(i < num_values)

        # Connect the num_values_combo's currentIndexChanged signal to the update_value_inputs function
        num_values_combo.currentIndexChanged.connect(update_value_inputs)

        # Set the initial visibility based on the default selection
        update_value_inputs()

        # Function to handle importing values from Excel
        def import_values_from_excel():
            file_dialog = QFileDialog.getOpenFileName(dialog, 'Select Excel File', '', 'Excel Files (*.xlsx *.xls *.csv)')[0]
            if not file_dialog:
                return

            try:
                excel_data = pd.read_excel(file_dialog, header=None)
                num_rows, num_cols = excel_data.shape

                if num_rows > 30:
                    QMessageBox.warning(None, 'Warning', 'The Excel file contains more than 30 rows of data. Please select a smaller file.')
                    return  # Exit the function

                num_values_combo.setCurrentIndex(num_rows - 2)  # Set the combo box to the number of rows minus 2 (to account for 2 as the minimum)

                for i, value_input in enumerate(value_inputs):
                    if i < num_rows:
                        value_input.setText(str(excel_data.iloc[i, 0]))

            except Exception as e:
                QMessageBox.warning(None, 'Error', f'An error occurred while importing values from Excel: {str(e)}')

        # Connect the import_excel_button's clicked signal to the import_values_from_excel function
        import_excel_button.clicked.connect(import_values_from_excel)

        # Function to handle the OK button click event
        def confirm_multi_filter():
            filter_criteria = combo_box.currentText()
            num_values = int(num_values_combo.currentText())
            values = [value_input.text() for value_input in value_inputs[:num_values]]
            if not any(values):
                QMessageBox.warning(None, 'Warning', 'Please enter at least one value for the filter.')
                return  # Exit the function

            # Construct the IN clause for the filter
            in_clause = "','".join(values)

            project = QgsProject.instance()
            layers = project.mapLayers().values()

            for layer in layers:
                if isinstance(layer, QgsVectorLayer):
                    field_to_check = None
                    if filter_criteria == "Cabinet":
                        field_to_check = ["Cab_ID_OR_OLT_ID", "FDT_ID", "CAB_OR_OLT_ID", "CAB_ID", "Zone_ID", "ZoneID",
                                          "cab_id", "FDT_ID_OR_OLT_ID"]
                    elif filter_criteria == "Route":
                        field_to_check = ["SUB_RingID", "subring_id", "Route_ID", "Route"]
                    elif filter_criteria == "Exchange":
                        field_to_check = ["ExchangeID", "Exchange ID"]

                    if field_to_check:
                        if isinstance(field_to_check, list):
                            # Check if any of the fields in the list exist in the layer's fields
                            fields = layer.fields()
                            field_names = [field.name() for field in fields]
                            filter_strings = []
                            for field in field_to_check:
                                if field in field_names:
                                    filter_strings.append(f'"{field}" IN (\'{in_clause}\')')
                            if filter_strings:
                                query = ' OR '.join(filter_strings)
                                layer.setSubsetString(query)
                        else:
                            if field_to_check in layer.fields().names():
                                query = f'"{field_to_check}" IN (\'{in_clause}\')'
                                layer.setSubsetString(query)
                            else:
                                layer.setSubsetString("")  # Clear the filter if the field is not present or if no filter value is entered
                        # Refresh the layer to apply the filter
                        layer.triggerRepaint()

            # Close the dialog
            dialog.accept()

        # Connect the confirm_button's clicked signal to the confirm_multi_filter function
        confirm_button.clicked.connect(confirm_multi_filter)

        # Show the dialog
        dialog.exec_()

    def clearFilters(self):
        # Flag to check if any filters were applied
        filters_applied = False

        # Clear filters on all layers
        project = QgsProject.instance()
        layers = project.mapLayers().values()
        for layer in layers:
            if isinstance(layer, QgsVectorLayer):
                if layer.subsetString():  # Check if a filter is applied
                    filters_applied = True
                    layer.setSubsetString("")  # Clear the filter
                    layer.triggerRepaint()  # Refresh the layer to apply the filter removal

        # Display a message based on whether filters were cleared or not
        if filters_applied:
            QMessageBox.information(None, 'Filter Cleared', 'Filters have been cleared from all layers.')
        else:
            QMessageBox.warning(None, 'No Filters', 'No filters were applied to clear.')
