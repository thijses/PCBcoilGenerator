"""
note: this file may be depricated by cv2Renderer.py (once i actually finish making that one)
this is an exporter (/renderer) to images (bitmaps),
  specifically, for printing coils using inkjet equipment (special silver-ink printers, or just regular ones (useful for negative-exposure etching))

TODO:
- manual polygon math (instead of letting CV2 draw the lines)
- automatic isolation-layer rendering (slightly complex)
- direct export to multi-layer image programs like paint.NET (.pdn file), or photoshop or whatever. NOTE: .tiff doesn't work in paint.NET
"""


import numpy as np
import cv2
from typing import Callable # just for type-hints to provide some nice syntax colering


CV2outputFormats: dict[str,str] = {'.png' : '.png',
                                   '.tif' : '.tif', # same as .tiff
                                   '.tiff' : '.tiff'} # NOTE: .tiff multiple layers don't work in paint.NET (which was the whole reason i added it...)

preferredLineType = cv2.LINE_AA # there's not much difference between the line types, especially at high resolutions

## some default colors. NOTE: should be overwritten with colorFunc
backgroundColor = [0  ,0  ,0  ,0  ] # (BGRA) fully transparent
copperColor     = [0  ,0  ,0  ,255] # (BGRA) black
#isolationColor  = [0  ,216,255,255] # (BGRA) yellow # NOTE: this doesn't work with the binary thresholding, it makes this 0,255,255,255

defaultColorFunc: Callable[[int], tuple[int,int,int,int]] = lambda layer : (backgroundColor if (layer < 0) else copperColor) # the simplest implementation

def imwrite(coil: 'coilClass', pixelsPerMM:float, format:str='.png', colorFunc:Callable[[int],tuple[int,int,int,int]]=None, binary:bool=True, binaryThresh:int=100, invertY:bool=True) -> list[np.ndarray]:
    """ pixelsPerMM is required, and determined by your printing process.
        can output as several '.png' files, or as 1 '.tiff'/'.tif' file (with mutiple layers).
        colorFunc (optional) must be a function which provides a BGRA color for a given layer index, or the background color if given -1.
        if the binary parameter is set to True, pixels will have only either 0 or 255 as their value.
            binaryThresh determines the lower-cutoff threshold for values to become 255 """
    # if(imageRes is None):  imageRes = (1,1) # automatically calculate imageRes when it's not specified
    if(colorFunc is None):  colorFunc = defaultColorFunc
    if(format not in CV2outputFormats):
        print("imwrite invalid format!");   return([])
    renderedCoils: list[list[tuple[float,float]]] = [coil.renderAsCoordinateList(False), coil.renderAsCoordinateList(True)]
    maxVal: float = max([max(abs(point[0]), abs(point[1])) for point in renderedCoils[0]]) # gives the maximum coordinate in any direction
    maxVal += (coil.traceWidth/2) # the maximum coordinate is the center of a trace point, so add half the trace width to get the bounding box radius
    ## the coils are rendered around the (0,0) coordinate, so maxVal is half the minimum resolution (and let's just make it square, to make centering extra easy)
    # imageRes = (max(int(imageRes[0]), int(round(2*maxVal*pixelsPerMM))), max(int(imageRes[1]), int(round(2*maxVal*pixelsPerMM)))) # enforces minimum image size calculated
    imageRes = (int(round(2*maxVal*pixelsPerMM)), int(round(2*maxVal*pixelsPerMM)))
    blankImage = np.empty((imageRes[0],imageRes[1],4), dtype=np.uint8) # 4 channel (BGRA) image
    allImages: list[np.ndarray] = [] # a list of image arrays
    lineWidthPixels = int(coil.traceWidth * pixelsPerMM) - 1 # cv2 interprets line width a little strangely. 4=>5, 5=>7, 6=>7, 7=>9, always odd numbers, always at least 1 too big
    realToPixelPos: Callable[[tuple[float,float]], tuple[int,int]] = lambda realPos : (int((imageRes[1]/2)+(realPos[0]*pixelsPerMM)),
                                                                                        int(((imageRes[0]/2)-(realPos[1]*pixelsPerMM)) if invertY else ((imageRes[0]/2)+(realPos[1]*pixelsPerMM))))
    ## NOTE: cv2 image arrays are stored as [y][x], but most (not all) functions want coordinates in (x,y).
    pixelLineArrays = np.array([[realToPixelPos(point) for point in renderedCoil] for renderedCoil in renderedCoils], int)
    for currentLayer in range(coil.layers):
        lineArr = pixelLineArrays[currentLayer % 2]
        allImages.append(cv2.polylines(blankImage.copy(), [lineArr.reshape((-1, 1, 2))], False, colorFunc(currentLayer), lineWidthPixels, preferredLineType)) # cv2 has a function for drawing nice lines
        ## NOTE: cv2 renders lines with smooth transitions. This is nice for human eyes, but not great for metal-etching/printing. I recommend using some kind of binary 'flattening'/rounding.
    if((coil.layers%2)!=0): # only in case of an un-even number of layers
        allImages.append(cv2.line(blankImage.copy(), realToPixelPos((renderedCoils[0][-1][0], renderedCoils[0][0][1])), realToPixelPos(renderedCoils[0][-1]), colorFunc(coil.layers), lineWidthPixels, preferredLineType))
    
    if(binary):
        ## NOTE: the binary conversion is not ideal. It currently handles every channel seperately.
        for image in allImages:
            channels = cv2.split(image)
            for i in range(len(channels)): # len(channels) should always be 4, btw!
                _, mask = cv2.threshold(channels[i], binaryThresh, 255, cv2.THRESH_BINARY)
                image[:,:,i] = mask # not really how masks work, but you get the point

    coilFilename = coil.generateCoilFilename()
    if(format == '.png'):
        for i in range(len(allImages)):
            cv2.imwrite(coilFilename+"_"+str(i)+'.png', allImages[i])
    elif((format == '.tif') or (format == '.tiff')):
        cv2.imwritemulti(coilFilename+format, np.array(allImages, dtype=np.uint8)) # with .tif you can save multiple images to 1 file
    # else: # should never happen

    return(allImages)



if __name__ == "__main__": # an example of how this file may be used
    from PCBcoilV2 import coilClass, shapes, ozCopperToMM
    # coil = coilClass(turns=11, diam=35, clearance=60/56, traceWidth=10/56, layers=1, copperThickness=0.0015, shape=shapes['square'], formula='cur_sheet') # NFC antenna phase 1 (PET)
    # coil = coilClass(turns=7, diam=35, clearance=0.6, traceWidth=10/56, layers=1,                    copperThickness=0.0025, shape=shapes['square'], formula='cur_sheet') # new design 1L thicker
    # coil = coilClass(turns=3, diam=35, clearance=0.75, traceWidth=0.25, layers=2, PCBthickness=0.05, copperThickness=0.0015, shape=shapes['square'], formula='cur_sheet') # new design 2L alt
    coil = coilClass(turns=3, diam=35.5, clearance=0.25, traceWidth=0.75, layers=1, PCBthickness=0.05, copperThickness=0.0015, shape=shapes['square'], formula='cur_sheet') # new design 2L alt ISO layer
    colorFunc = lambda layer : (backgroundColor if (layer<0) else [0,0,min(int(layer*255),255),255])
    imwrite(coil, 56, '.png', colorFunc, True)