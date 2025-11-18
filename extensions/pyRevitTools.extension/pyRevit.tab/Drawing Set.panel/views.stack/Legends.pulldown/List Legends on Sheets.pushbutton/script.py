# -*- coding: utf-8 -*-
""" 

Show Legendes on sheets, grouped by legend

Updated by Kevin Salmon, adapted from work by Jean-Marc Couffin

"""

from pyrevit import revit, DB, script, forms
from pyrevit.compat import get_elementid_value_func

output = script.get_output()
output.set_title("LEGENDES PAR FEUILLE")
output.set_width(800)
output.set_height(900)
output.close_others()

doc = revit.doc

get_elementid_value = get_elementid_value_func()

# All legends, whether on Sheet or not
legends = [
    v for v in DB.FilteredElementCollector(doc)
    .OfCategory(DB.BuiltInCategory.OST_Views)
    .WhereElementIsNotElementType()
    .ToElements()
    if not v.IsTemplate and v.ViewType == DB.ViewType.Legend]
    # if v.ViewType == DB.ViewType.Legend

# legends_ids = [get_elementid_value(x.Id) for x in legends]
legends_ids = [x.Id for x in legends]

leg_id_dic = dict()
for lid in legends_ids:
    leg_id_dic[lid] = [str(),[]]


sheets = (
    DB.FilteredElementCollector(doc)
    .OfCategory(DB.BuiltInCategory.OST_Sheets)
    .WhereElementIsNotElementType()
    .ToElements()
)

table_data = []
table_header = [
                "Select/Zoom", 
               "Legend > Sheets",
                "Sheet name"]

for sheet in sheets:
    vpids = sheet.GetAllPlacedViews()
    
    for vpid in vpids:
        # print(type(vpid))
        # vp_id = get_elementid_value(vpid)
        
        if vpid in legends_ids:
            h_has_a_legend = True
            vp_name = "{}".format(doc.GetElement(vpid).Name)
            leg_id_dic[vpid][0] = vp_name
            leg_id_dic[vpid][1].append(sheet)
            # table_data.append((output.linkify(doc.GetElement(vp).Id, title="Lég"), vp_name, output.linkify(sheet.Id, title="Feuille"), sheet.SheetNumber, sheet.Name))


for k, v in leg_id_dic.items():
    # print(k, v[1])
    sh_has_a_legend = False
    if len(v[1]) >0:
        sh_has_a_legend = True
        table_row = [
            output.linkify(k, title="Legend"),
            "<b>{}</b> (placed on {} sheets)".format(v[0], len(v[1])),
            " "]
        table_data.append(table_row)

    if len(v) > 0:
        for sheet in v[1]:
            table_row = [
                        " ",
                        "{} {}".format(output.linkify(sheet.Id, title="Sheet"), sheet.SheetNumber),
                        sheet.Name]
            table_data.append(table_row)

# table_data.append(table_header)


if len(table_data) != 0:
    # table_data = sorted(table_data, key=lambda x: (x[1], x[3])) # The sorting is rather grouping of Sheets by Legend
    # output.print_md("## Legends on Sheets")
    # table_header = table_header

    # Text-alignment or header row titles (CSS)
    column_head_align_styles = ["center", "left", "left"]

    # Text-alignment or header row titles (CSS)
    column_data_align_styles = ["right", "left", "left"]
    
    # Option to repeat the header at the bottom (useful for long tables) (bool)
    repeat_head_as_foot = True if len(table_data)>12 else False # Automatic option by table length

    column_widths = ["150px", "auto", "auto"]
    table_width_style="100%"
    row_striping = True

    output.print_md("## Legends on Sheets")
    print("Project legends, grouped by legend, showing the sheets they are placed on.\n\n")
    
    output.print_html_table(table_data, 
                        title=None,
                        columns=table_header,
                        formats=['','',''],
                        last_line_style='',
                        column_head_align_styles=column_head_align_styles,
                        column_data_align_styles=column_data_align_styles,
                        repeat_head_as_foot=repeat_head_as_foot,
                        column_widths=column_widths,
                        table_width_style=table_width_style,
                        row_striping=row_striping)
else:
    forms.alert("No legends found on sheets.")
