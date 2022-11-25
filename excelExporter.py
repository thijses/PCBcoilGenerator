import pandas as pd # used to make nice-looking excel files (alternatively, just use .CSV)
## TODO: if pandas fails to import, fall back to .csv
## NOTE: installing pandas ('pip install pandas') may also require installing openpyxl ('pip install openpyxl') to get full the .to_excel() function to work


import DXFexporter as DXFexp

fileExtension = ".xlsx" # for pandas DataFrame output

def exportCoils(coilList: list['coilClass'], filename: str) -> bool: # i wanted to avoid importing any one version of PCBcoilV_, so this type hint is mostly useless
    """ save some (list of) coil parameters and predictions to an excel file """
    dataFrameToSave = pd.DataFrame({'Shape' : [coil.shape.__class__.__name__ for coil in coilList], # not ideal, but searching through the 'shapes' list's keys is some terrible code, let's just not.
                                    'Layers' : [coil.layers for coil in coilList],
                                    'Turns' : [coil.turns for coil in coilList],
                                    'Trace width [mm]' : [coil.traceWidth for coil in coilList],
                                    'Clearance [mm]' : [coil.clearance for coil in coilList],
                                    'Diam [mm]' : [coil.diam for coil in coilList],
                                    'Calculated trace length [mm]' : [coil.calcCoilTraceLength() for coil in coilList],
                                    'PCBthickness [mm]' : [coil.PCBthickness for coil in coilList],
                                    'Layer spacing [mm]' : [coil.calcLayerSpacing() for coil in coilList],
                                    'Copper thickness [um]' : [(coil.copperThickness*1000) for coil in coilList],
                                    'Calculated trace length [mm]' : [coil.calcCoilTraceLength() for coil in coilList],
                                    'Predicted Resistance [mOhm]' : [(coil.calcTotalResistance()*1000) for coil in coilList],
                                    'Predicted Inductance [uH]' : [(coil.calcInductance()*1000000) for coil in coilList],
                                    'Predicted Inductance single-layer [uH]' : [(coil.calcInductanceSingleLayer()*1000000) for coil in coilList],
                                    'formula used' : [coil.formula for coil in coilList],
                                    'general filename' : [DXFexp.generateCoilFilename(coil) for coil in coilList]})
    try:
        if(not filename.endswith(fileExtension)):
            filename += fileExtension
        dataFrameToSave.to_excel(filename)
        return(True)
    except Exception as excep:
        print("FAILED exportCoils(), exception:", excep)
        return(False)

if __name__ == "__main__": # normal usage
    import PCBcoilV2 as PC

    filename = "someCoils" + fileExtension

    coilList: list[PC.coilClass] = [] # a list to store the resulting coils in

    PAcopperThickness        = 0.030
    JLCcopperThickness2layer = 0.030
    JLCcopperThickness4layer = 0.030
    PCBthicknessPA     = 0.1 # just a guess, but it doesn't matter as it's only 1 layer
    PCBthickness2layer = 0.6
    PCBthickness4layer = 0.8
    formula = 'cur_sheet'
    ## single-layer on PA:
    coilList.append(PC.coilClass(turns=9, diam=40, clearance=0.15, traceWidth=0.9, layers=1, PCBthickness=PCBthicknessPA    , copperThickness=PAcopperThickness, shape=PC.shapes['square'], formula=formula))
    coilList.append(PC.coilClass(turns=9, diam=40, clearance=0.15, traceWidth=0.9, layers=1, PCBthickness=PCBthicknessPA    , copperThickness=PAcopperThickness, shape=PC.shapes['circle'], formula=formula))
    coilList.append(PC.coilClass(turns=9, diam=40, clearance=0.30, traceWidth=1.0, layers=1, PCBthickness=PCBthicknessPA    , copperThickness=PAcopperThickness, shape=PC.shapes['hexagon'], formula=formula))
    ## 2-layer PCB (JLC)
    # 1 layer
    coilList.append(PC.coilClass(turns=9, diam=40, clearance=0.15, traceWidth=0.9, layers=1, PCBthickness=PCBthickness2layer, copperThickness=JLCcopperThickness2layer, shape=PC.shapes['square'], formula=formula))
    coilList.append(PC.coilClass(turns=9, diam=40, clearance=0.15, traceWidth=0.9, layers=1, PCBthickness=PCBthickness2layer, copperThickness=JLCcopperThickness2layer, shape=PC.shapes['circle'], formula=formula))
    # (default)
    coilList.append(PC.coilClass(turns=9, diam=40, clearance=0.15, traceWidth=0.9, layers=2, PCBthickness=PCBthickness2layer, copperThickness=JLCcopperThickness2layer, shape=PC.shapes['square'], formula=formula))
    coilList.append(PC.coilClass(turns=9, diam=40, clearance=0.15, traceWidth=0.9, layers=2, PCBthickness=PCBthickness2layer, copperThickness=JLCcopperThickness2layer, shape=PC.shapes['circle'], formula=formula))
    # fewer turns
    coilList.append(PC.coilClass(turns=6, diam=40, clearance=0.15, traceWidth=0.9, layers=2, PCBthickness=PCBthickness2layer, copperThickness=JLCcopperThickness2layer, shape=PC.shapes['square'], formula=formula))
    coilList.append(PC.coilClass(turns=6, diam=40, clearance=0.15, traceWidth=0.9, layers=2, PCBthickness=PCBthickness2layer, copperThickness=JLCcopperThickness2layer, shape=PC.shapes['circle'], formula=formula))
    # thicker trace
    coilList.append(PC.coilClass(turns=9, diam=40, clearance=0.15, traceWidth=1.2, layers=2, PCBthickness=PCBthickness2layer, copperThickness=JLCcopperThickness2layer, shape=PC.shapes['square'], formula=formula))
    coilList.append(PC.coilClass(turns=9, diam=40, clearance=0.15, traceWidth=1.2, layers=2, PCBthickness=PCBthickness2layer, copperThickness=JLCcopperThickness2layer, shape=PC.shapes['circle'], formula=formula))
    # more clearance
    coilList.append(PC.coilClass(turns=9, diam=40, clearance=0.30, traceWidth=0.9, layers=2, PCBthickness=PCBthickness2layer, copperThickness=JLCcopperThickness2layer, shape=PC.shapes['square'], formula=formula))
    coilList.append(PC.coilClass(turns=9, diam=40, clearance=0.30, traceWidth=0.9, layers=2, PCBthickness=PCBthickness2layer, copperThickness=JLCcopperThickness2layer, shape=PC.shapes['circle'], formula=formula))
    # smaller diam
    coilList.append(PC.coilClass(turns=9, diam=30, clearance=0.15, traceWidth=0.9, layers=2, PCBthickness=PCBthickness2layer, copperThickness=JLCcopperThickness2layer, shape=PC.shapes['square'], formula=formula))
    coilList.append(PC.coilClass(turns=9, diam=30, clearance=0.15, traceWidth=0.9, layers=2, PCBthickness=PCBthickness2layer, copperThickness=JLCcopperThickness2layer, shape=PC.shapes['circle'], formula=formula))
    ## 4-layer PCB (JLC)
    coilList.append(PC.coilClass(turns=9, diam=40, clearance=0.15, traceWidth=0.9, layers=3, PCBthickness=0.6               , copperThickness=JLCcopperThickness4layer, shape=PC.shapes['circle'], formula=formula)) # 3 layer
    coilList.append(PC.coilClass(turns=9, diam=40, clearance=0.15, traceWidth=0.9, layers=4, PCBthickness=PCBthickness4layer, copperThickness=JLCcopperThickness4layer, shape=PC.shapes['circle'], formula=formula)) # (defualt)
    coilList.append(PC.coilClass(turns=9, diam=40, clearance=0.15, traceWidth=0.9, layers=4, PCBthickness=PCBthickness4layer, copperThickness=JLCcopperThickness4layer, shape=PC.shapes['square'], formula=formula)) # square
    coilList.append(PC.coilClass(turns=6, diam=40, clearance=0.15, traceWidth=0.9, layers=4, PCBthickness=PCBthickness4layer, copperThickness=JLCcopperThickness4layer, shape=PC.shapes['circle'], formula=formula)) # fewer turns
    
    # shapeList = (PC.shapes['square'], PC.shapes['circle']) # to fetch all shapes, use: [PC.shapes[key] for key in PC.shapes]
    # layerList = (1,2,3,4)
    # turnsList = (6,9)
    # traceWidthList = (0.9, 1.2)
    # clearanceList = (0.15, 0.3)
    # diamList = (30, 40)
    # PCBthicknessList = (0.6, 0.8)
    # copperThicknessList = (0.03, 0.0348)
    # formulaList = ('cur_sheet', )

    # for shape in shapeList:
    #     for layers in layerList:
    #         for turns in turnsList:
    #             for traceWidth in traceWidthList:
    #                 for clearance in clearanceList:
    #                     for diam in diamList:
    #                         for PCBthickness in PCBthicknessList:
    #                             for copperThickness in copperThicknessList:
    #                                 for formula in formulaList:
    #                                     coilList.append(PC.coilClass(turns=turns, diam=diam, clearance=clearance, traceWidth=traceWidth, layers=layers, \
    #                                                                     PCBthickness=PCBthickness, copperThickness=copperThickness, shape=shape, formula=formula))
            
    exportCoils(coilList) # now export to an excel file