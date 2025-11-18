# -*- coding: utf-8 -*-
"""Collects all Grids, retrieves their vectors, and checks alignment to X or Y axes using 
Revit's built-in IsAlmostEqualTo tolerance."""

from pyrevit import revit, DB, script
from pyrevit.preflight import PreflightTestCase
from pyrevit.coreutils import Timer # Used for timing the check
from datetime import timedelta # Used for timing the check
import math # Used in angles

doc = revit.doc

# --- Helper Function for Vector Calculation
def get_grid_direction_vector(grid):
    """
    Calculates the normalized direction vector of a Grid element.
    Uses the curve's direction for Lines, or the tangent for Arcs.
    """
    grid_curve = grid.Curve
    
    if isinstance(grid_curve, DB.Line):
        start_point = grid_curve.GetEndPoint(0)
        end_point = grid_curve.GetEndPoint(1)
        direction_vector = end_point - start_point
        return (True, direction_vector.Normalize())
    else:
        return (False, None)


def check_axis_alignment(vector):
    """
    If the grid is not an arc, checks if the normalized vector aligns with the X or Y axis 
    using DB.XYZ.IsAlmostEqualTo, which utilizes Revit's internal tolerance.
    """
    # --- Pre-define Standard Axis Vectors ---
    # We use the built-in Basis vectors and their negative forms
    BASIS_X = DB.XYZ.BasisX      # (1, 0, 0)
    BASIS_Y = DB.XYZ.BasisY      # (0, 1, 0)
    BASIS_NEG_X = BASIS_X.Negate() # (-1, 0, 0)
    BASIS_NEG_Y = BASIS_Y.Negate() # (0, -1, 0)

    if not vector: # Is an arc
        return "-"
    
    # Check for X-Axis Alignment (positive or negative direction)
    if vector.IsAlmostEqualTo(BASIS_X) or vector.IsAlmostEqualTo(BASIS_NEG_X):
        return "X"
    
    # Check for Y-Axis Alignment (positive or negative direction)
    elif vector.IsAlmostEqualTo(BASIS_Y) or vector.IsAlmostEqualTo(BASIS_NEG_Y):
        return "Y"
        
    # Neither X nor Y aligned nor an arc
    return ":warning:"


def numerical_or_string_key(value):
    """Attempts to convert a value to float for numerical sorting; 
       if it fails, returns the string for text sorting.
       Corrects the sorting issue with mixed numeric and string grid names."""
    try:
        # Try to convert to float for numerical sorting
        return float(value)
    except ValueError:
        # If conversion fails (e.g., 'AA'), treat it as a string
        return value


def check_model_grids(doc, output):
    timer = Timer()

    # Manage output
    output = script.get_output()
    output.set_title("GRID AUDIT")
    output.set_width(1250)
    output.set_height(750)
    output.close_others()
    output.show()


    collector = DB.FilteredElementCollector(doc).OfClass(DB.Grid)
    grid_collect = collector.ToElements()

    if not grid_collect:
        grid_collect = [] # Nevertheless run the output to show the result table

    table_data = []
    table_x_ortho_rows = []
    table_y_ortho_rows = []
    table_non_ortho_rows = []
    table_non_straight_rows = []

    for grid in grid_collect:
        table_row = []

        grid_type = doc.GetElement(grid.GetTypeId())
        grid_type_name = grid_type.get_Parameter(DB.BuiltInParameter.SYMBOL_NAME_PARAM).AsString()
        # grid_name = float(grid.Name) if grid.Name.replace('.','',1).isdigit() else grid.Name
        grid_name = grid.Name
        grid_id = grid.Id
        grid_is_pinned = grid.Pinned
        grid_is_straight, direction_vector = get_grid_direction_vector(grid)
        link = output.linkify(grid_id, title="Select")
        
        scope_box_id = grid.get_Parameter(DB.BuiltInParameter.DATUM_VOLUME_OF_INTEREST).AsElementId()
        scope_box = doc.GetElement(scope_box_id)
        if scope_box:
            scope_box_name = scope_box.Name
        else:
            scope_box_name = "-"
        
        
        alignment = check_axis_alignment(direction_vector)
        if grid_is_straight: # Rather than an arc
            # Angle in XY plane relative to the positive X-axis
            angle_rad = math.atan2(direction_vector.Y, direction_vector.X)
            angle_deg = round(math.degrees(angle_rad), 6) # Angle in degrees rounded to 6 decimals
        else: # Arcs
            angle_deg = "-"

        table_row = ["",
                    link,
                    grid_name,
                    grid_type_name,
                    "{} {}".format(":warning:" if alignment==":warning:" else "", angle_deg),
                    "{}".format(" :pushpin:" if grid_is_pinned else ""),
                    scope_box_name,]
        if alignment == "X":
            table_x_ortho_rows.append(table_row)
        elif alignment == "Y":
            table_y_ortho_rows.append(table_row)
        else:
            if grid_is_straight: # Rather than an arc
                table_non_ortho_rows.append(table_row)
            else: # Arcs
                table_non_straight_rows.append(table_row)
        
        
    total_x = len(table_x_ortho_rows)
    total_y = len(table_y_ortho_rows)
    total_other = len(table_non_ortho_rows)
    total_non_straight = len(table_non_straight_rows)
    total_all = collector.GetElementCount()
    EMPTY_ROW = ["", "", "", "", "", ""]

    table_data.append(["<b>X-ORTHOGONAL</b>", "", "", "", ""])
    table_data.extend(sorted(table_x_ortho_rows, key=lambda row: numerical_or_string_key(row[2])))
    table_data.append(["", "Total", "<b>{}</b> X-orthogonal (horizontal)".format(total_x), "", ""])
    table_data.append(EMPTY_ROW)
    table_data.append(["<b>Y-ORTHOGONAL</b>", "", "", "", "", ""])
    table_data.extend(sorted(table_y_ortho_rows, key=lambda row: numerical_or_string_key(row[2])))
<<<<<<< HEAD
    table_data.append(["", "Total", "<b>{}</b> X-orthogonal (vertical)".format(total_y), "", ""])
=======
    table_data.append(["", "Total", "<b>{}</b> Y-orthogonal (vertical)".format(total_y), "", ""])
>>>>>>> 153ba971643c537df684bdb8f32cfdc26a3f54a4
    table_data.append(EMPTY_ROW)
    table_data.append(["<b>NON-ORTHOGONAL</b>", "", "", "", "", ""])
    table_data.extend(sorted(table_non_ortho_rows, key=lambda row: numerical_or_string_key(row[2])))
    table_data.append(["", "Total", "<b>{}</b> non-orthogonal (diagonal)".format(total_other), "", ""])
    table_data.append(EMPTY_ROW)
    table_data.append(["<b>ARCS</b>", "", "", "", "", ""])
    table_data.extend(sorted(table_non_straight_rows, key=lambda row: numerical_or_string_key(row[2])))
<<<<<<< HEAD
    table_data.append(["", "Total", "<b>{}</b> non-orthogonal (arcs)".format(total_non_straight), "", ""])
=======
    table_data.append(["", "Total", "<b>{}</b> non-orthogonal (arc)".format(total_non_straight), "", ""])
>>>>>>> 153ba971643c537df684bdb8f32cfdc26a3f54a4
    table_data.append(EMPTY_ROW)

    table_data.append(["", "Grand total", "<b>{}</b>".format(total_all), "", "", ""])

<<<<<<< HEAD
    title = "Audit Grid instances in model '{}.rvt'".format(doc.Title)
=======

    print("Audit of project grids")
>>>>>>> 153ba971643c537df684bdb8f32cfdc26a3f54a4
    # Call output
    title="{}{}".format(doc.Title, ".rvt")
    columns = [
<<<<<<< HEAD
            "Grid direction",
=======
            "Axis alignment",
>>>>>>> 153ba971643c537df684bdb8f32cfdc26a3f54a4
            "Select/Zoom",
            "Grid name",
            "Type",
            "Angle (°)",
            "Pinned",
            "Scope Box",]
    output.print_table(table_data,
                    title=title,
                    columns=columns,
                    last_line_style='color:red; font-weight:bold')
    
    # Display check duration
    endtime = timer.get_time()
    endtime_hms = str(timedelta(seconds=endtime))
    endtime_hms_claim = " \n\nCheck duration " + endtime_hms[0:7] # Remove seconods decimals from string
    print(endtime_hms_claim)


class ModelChecker(PreflightTestCase):
    """
    All grids, organised by X or Y axes.
    List project grids, organised by their X or Y orthogonal alignment.
     
    Allows identification of non-orthogonal grids and if grids are arcs.
    The results also show if grids are pinned and/or scoped to a scope box.

    This QC tools returns the following data:
        Grids alignment, count, name, type, angle, pinned status and scope box

    """

    name = "Grid audit"
    author = "Kevin Salmon"


    def startTest(self, doc, output):
        check_model_grids(doc, output)
