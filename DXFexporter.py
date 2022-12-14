"""
this file servers to convert a generated coil into DXF format for use with:
- Altium
- EasyEDA

this code owes its existance to DXFEngine   https://pypi.org/project/dxfwrite/

NOTE: i have aspired to make this code usable from any version of PCBcoilV_, but i have not actually bothered to check whether it will.


in EasyEDA:
importing DXFs is easy, but limited:
 open a PCB or footprint,
 click 'file->import->DXF' in the topleft menu bar,
 select 'mm' as unit and enter the traceWidth you used when generating the coil
 HOWEVER, easyEDA only accepts importing 1 layer at a time, even if the DXF has multiple layers (it will simply merge all the layers).
 so, this code will export a second DXF file for the bottom/inner layers, and you'll have to manually import both files and set the layer (and tracewidth) correctly
 Also, it EasyEDA does not allow importing of text though DXF, only lines (and perhaps polygons, but i have yet to test that)
 so my efforts to include silkscreen are in vein


TODO:
- make EasyEDA silkscreen DXF generator (info about current coil)
- make explanatory silkscreen DXF generator (info about how a coil is defined (use LinearDimension() and the other ones for the best results))
- Altium

"""

from dxfwrite import DXFEngine as dxf

DXFoutputFormats: dict[str,str] = {'EasyEDA' : 'EasyEDA',
                                    'Altium' : 'Altium'}

## NOTE: the following function has been moved to PCBcoilV_ (V2 onwards)
def generateCoilFilename(coil: 'coilClass') -> str:
    """ DEPRICATED, use the function by the same name in PCBcoilV_ from V2 onwards """
    filename = coil.shape.__class__.__name__[0:2]   # shape (first 2 letters)
    filename += '_di'+str(int(round(coil.diam, 0)))  # diam (millimeters)
    filename += '_tu'+str(coil.turns)                # turns
    filename += '_wi'+str(int(round(coil.traceWidth * 1000, 0))) # traceWidth (micrometers)
    filename += '_cl'+str(int(round(coil.clearance * 1000, 0)))  # clearance (micrometers)
    ## the following values are (more) dependent on the production process, and should be verified or ignored:
    filename += '_cT'+str(int(round(coil.copperThickness * 1000, 0)))  # copper thickness (micrometers)
    if(coil.layers > 1):
        filename += '_La'+str(coil.layers)               # Layers
        filename += '_Pt'+str(int(round(coil.PCBthickness * 1000, 0)))  # PCBthickness (micrometers)
    ## the following values are only valid if the previous (production-dependent ones) hold true. If not, these should be ignored:
    filename += '_Re'+str(int(round(coil.calcTotalResistance() * 1000, 0))) # Resistance (milliOhms) (assuming nothing changes!)
    filename += '_In'+str(int(round(coil.calcInductance() * 1000000000, 0)))  # Inductance (nanoHenry) (assuming nothing changes!)
    return(filename)

def EasyEDAlayerName(layer:int=0, totalLayers:int=2) -> str:
    """ not actually used by EasyEDA DXF importer, but it's nice to keep consistant naming, right?"""
    if(layer == 0): # if it's the top layer
        return('TopLayer')
    elif(layer == (totalLayers-1)): # if it's the bottom layer
        return('BottomLayer')
    else: # if its an inner layer
        return('Inner'+str(layer)) # e.g. 'Inner1', 'Inner2' for a 4-layer PCB

def saveDXF(coil: 'coilClass', DXFoutputFormat: str) -> list[str]:
    """ generates and saves a .dxf file to be imported in the software of your choosing (DXFoutputFormat)
        returns: a list of the names of the files it made """
    filenames: list[str] = []
    if(DXFoutputFormat not in DXFoutputFormats):  print("makeDXF() output format:", DXFoutputFormat, " not in list:", DXFoutputFormats);  return(filenames)
    if(DXFoutputFormat == 'EasyEDA'): # EasyEDA
        renderedCoils: list[list[tuple[float,float]]] = [coil.renderAsCoordinateList(False), coil.renderAsCoordinateList(True)]
        try: # the code should not hang on something so trivial as a filename
            filenames: list[str] = [(DXFoutputFormat+'_'+coil.generateCoilFilename()+'_')  for i in range(min(coil.layers, 2))] # from PCBcoilV2 onwards, this is the proper way to do it
        except:
            print("warning!: using depricated filename function (because coil.generateCoilFilename failed). Names may be inconsistant!")
            filenames: list[str] = [(DXFoutputFormat+'_'+generateCoilFilename(coil)+'_')  for i in range(min(coil.layers, 2))] # fall back to depricated file system for PCBcoilV1
        for i in range(coil.layers):   filenames[i%2] += '_'+EasyEDAlayerName(i, coil.layers) # e.g. "(coilNamePrefix)__TopLayer_Inner2" and "(coilNamePrefix)__Inner1_BottomLayer" for a 4 layer PCB
        for i in range(len(filenames)):   filenames[i] += '.dxf' # add extensions
        # dxfFiles = [dxf.drawing(filename) for filename in filenames] # initialize files (done in forloop instead)
        for i in range(min(coil.layers, 2)): # 
            dxfFile = dxf.drawing(filenames[i%2]) # dxfFiles[i%2] # even layers in 1 file, odd layers in the other
            layerName = EasyEDAlayerName(i, coil.layers) # just formality really, EasyEDA is not gonna use it
            dxfFile.add_layer(layerName)
            ## you can either add the lines individually (contiguous)
            # for j in range(1, len(renderedCoils[i%2])):
            #     dxfFile.add(dxf.line(renderedCoils[i%2][j-1], renderedCoils[i%2][j], layer=layerName, thickness=coil.traceWidth)) # NOTE: EasyEDA ignores all parameters except position
            ## or you can just add it as a long (continuous) line
            dxfFile.add(dxf.polyline(renderedCoils[i%2], layer=layerName, thickness=coil.traceWidth, startwidth=coil.traceWidth, endwidth=coil.traceWidth)) # NOTE: EasyEDA ignores all parameters except position
            dxfFile.save()
        # ## now generate a little silkscreen to identify the coil:     NOTE: can't, cause EasyEDA ignores text...
        # filenames.append( generateCoilFilename(coil)+'_silkscreen'+'.dxf' )
        # dxfFile = dxf.drawing(filenames[-1])
        # dxfFile.add_layer('TopSilkLayer') # truly a meaningless formality at this point
        # dxfFile.add(dxf.text('Line 1', (0.0, 0.0)))
        # dxfFile.save()
    elif(DXFoutputFormat == 'Altium'): # Altium
        print("output format 'Altium' is TBD!")
    else: print("impossible point reached in calcInductance(), check the formulaCoefficients formula names in this function!");  return(filenames)
    return(filenames)

def coilTestSilkscreen():
    ... # TODO: generate a little drawing, explaining the geometry of the coil shape(s). consider using LinearDimension and other such classes for extra fancy

if __name__ == "__main__": # an example of how this file may be used
    # from dxfwrite import const
    # print("consts:")
    # [print(entry, type(getattr(const, entry))) for entry in dir(const)]
    # print('\n')

    ## generate a little cross
    # drawing = dxf.drawing('test.dxf')
    # N = 4; table = (1,1,-1,-1)
    # for i in range(N):
    #     drawing.add_layer(EasyEDAlayerName(i, N))
    #     drawing.add(dxf.line((0, 0), (table[i%4], table[(i+1)%4]), layer=EasyEDAlayerName(i, N)))
    # drawing.save()

    from PCBcoilV2 import coilClass, shapes, ozCopperToMM
    coil = coilClass(turns=9, diam=24, clearance=0.1, traceWidth=1.0, layers=2, shape=shapes['circle'])
    # for outputFormat in DXFoutputFormats:
    #     filenames = saveDXF(coil, outputFormat)
    #     print("saved", outputFormat, "files:", filenames)
    saveDXF(coil, DXFoutputFormats['EasyEDA'])