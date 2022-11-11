"""
this code is intended for generating (and visualizing) PCB coils (a.k.a. planar inductors)
I strive to generate a relatively simple output:
a single layer coil, spiraling inwards, ending at a via leading it back to the start
this code can (currently) only produce coils with an equal width and height (one diameter parameter)

the math comes from here: https://coil32.net/pcb-coil.html    which in term gets its math from here: https://stanford.edu/~boyd/papers/pdf/inductance_expressions.pdf

the current sheet formula is also mentioned in this other paper:  http://www.edatop.com/down/paper/NFC/A_new_calculation_for_designing_multilayer_planar_spiral_inductors_PDF.pdf
the coefficients table is exactly the same, which gives some confidence to prefer that method



The way a PCB coil object may be stored/exported is as a collection of straight lines, as a rendered polygon, or as a formula.
In Altium there does not appear to be a way of importing a polygon, so it'll have to be a list of lines, i guess
In EasyEDA you can make polygons, but you'd have to manually fill in a lot of values, so a series of line would also be fewer steps.

TODO list:
 - check if spacing parameter (as described in paper) matches my implementation (check if used in math correctly), as it is somewhat ambiguous at times
 - check if the inner and outer diameter should be calculated considering the trace width (like the paper/s infographics show) (note: also somewhat ambiguous at times!)
 - research more ways of importing the results into PCB design software
 - add multilayer math (math's not that hard, just kind of tricky to implement)
 - find a way to model rectangular/oval coils (non-square)
"""


import numpy as np
from typing import Callable # just for type-hints to provide some nice syntax colering

visualization = True

angleRenderResDefault = np.deg2rad(10) # angular resolution when rendering continous (circular) coils

## scientific constants:
magneticConstant = 4*np.pi * 10**-7 # Mu (greek) = Newtons / Ampere    (vacuum permeability???)
## code constants
distUnitMult = 1/1000 # all distance units are in mm, so to convert back to meters, multiply with this
# formulaCoefficients = {'wheeler' :  {'square' : (2.34, 2.75),
#                                     'hexagon': (2.33, 3.82),
#                                     'octagon': (2.25, 3.55),
#                                     'circle' : (2.23, 3.45)},
#                        'monomial': {'square' : (0.00162, -1.21, -0.147, 2.40, 1.78, -0.030),
#                                     'hexagon': (0.00128, -1.24, -0.174, 2.47, 1.77, -0.049),
#                                     'octagon': (0.00133, -1.21, -0.163, 2.43, 1.75, -0.049)},
#                        'cur_sheet':{'square' : (1.27, 2.07, 0.18, 0.13),
#                                     'hexagon': (1.09, 2.23, 0.00, 0.17),
#                                     'octagon': (1.07, 2.29, 0.00, 0.19),
#                                     'circle' : (1.00, 2.46, 0.00, 0.20)}}

class _shapeTypeHint:
    formulaCoefficients: dict[str, tuple]
    stepsPerTurn: int | float # note: this is not actually how python typing works, it just forget to spit out an error. It's just for the humans
    # calcPos: Callable[[int|float,float,float,bool], tuple[float,float]] # the typing way of doing it
    # calcLength: Callable[[int|float,float,float], float]
    def calcPos(itt:int|float,diam:float,spacing:float,CCW:bool)->tuple[float, float]:  ... # the modern python way of type-hinting an undefined function
    def calcPos(itt:int|float,diam:float,spacing:float)->float:  ...
    isDiscrete: bool = True # most of the shapes have a discrete number points/corners/vertices by default. Only continous functions will need a render-resolution parameter
    def __repr__(self): # prints the name of the shape
        return("shape("+(self.__class__.__name__)+")")

class squareSpiral(_shapeTypeHint):
    formulaCoefficients = {'wheeler' : (2.34, 2.75),
                            'monomial' : (1.62, -1.21, -0.147, 2.40, 1.78, -0.030),
                            'cur_sheet' : (1.27, 2.07, 0.18, 0.13)}
    stepsPerTurn: int = 4 # multiply with number of turns to get 'itt' for functions below
    @staticmethod
    def calcPos(itt: int, diam: float, spacing: float, CCW=False) -> tuple[float, float]:
        """ input is the number of steps (corners), 4 steps would be a full circle, generally: itt=(stepsPerTurn*turns)
            output is a 2D coordinate along the spiral, starting outwards """
        x = (1 if (((itt%4)>=2) ^ CCW) else -1) * ((diam/2) - ((itt//4) * spacing))
        y = (1 if (((itt%4)==1) or ((itt%4)==2)) else -1) * ((diam/2) - (((itt-1)//4) * spacing))
        return(x,y)
    @staticmethod
    def calcLength(itt: int, diam: float, spacing: float) -> float:
        """ returns the length of the spiral at a given itt (without iterating, direct calculation) """
        ## NOTE: if the spiral goes beyond the center point and grows larger again (it shouldn't), then the length will be negative). I'm intentionally not fixing that, becuase it makes for good debug info
        horLines = (itt//2)
        sumOfWidths = (horLines * diam) - ((((horLines-1)*horLines) / 2) * spacing) # length of all hor. lines = (horLines * diam) - triangular number of (horLines-1)
        vertLines = ((itt+1)//2)
        sumOfHeights = (vertLines * diam) - ((max(((vertLines-2)*(vertLines-1)) / 2, 0) - 1) * spacing) # length of all vert. lines
        return(sumOfWidths + sumOfHeights)

class circularSpiral(_shapeTypeHint):
    formulaCoefficients = {'wheeler' : (2.23, 3.45),
                            # the monomial formula does cover circular spirals
                            'cur_sheet' : (1.00, 2.46, 0.00, 0.20)}
    stepsPerTurn: float = 2*np.pi # multiply with number of turns to get 'angle' for functions below
    isDiscrete = False # let the renderer know that this shape needs a resolution parameter
    @staticmethod
    def calcPos(angle: float, diam: float, spacing: float, CCW=False) -> tuple[float, float]:
        """ input is an angle in radians, 2pi would be a full circle, generally: angle=(stepsPerTurn*turns)
            output is a 2D coordinate along the spiral, starting outwards """
        x = (1 if CCW else -1) * np.sin(angle) * ((diam/2) - ((angle/(2*np.pi)) * spacing))
        y = -1 * np.cos(angle) * ((diam/2) - ((angle/(2*np.pi)) * spacing))
        return(x,y)
    @staticmethod
    def calcLength(angle: float, diam: float, spacing: float) -> float:
        """ returns the length of the spiral at a given angle (without iterating, direct calculation) """
        turns = (angle/circularSpiral.stepsPerTurn) # (float)
        return(np.pi * turns * (diam + calcInnerDiam(turns, diam, spacing)) / 2) # pi * turns * (diam + innerDiam) / 2 = basically just the circumference of the average diameter (outer+inner)/2

## now that the circularSpiral class exists, we can just derive sampled classes from that:
class NthDimSpiral(_shapeTypeHint): # a general class for Nth dimensional polygon spirals. Specify the number of points/corners/sides (6 for hexagon, 8 for octagon, etc.) and provide formulaCoefficients in the subclass
    @classmethod # class methods let you use subclass static variables
    def calcPos(subclass, itt: int, diam: float, spacing: float, CCW=False) -> tuple[float, float]:
        """ input is the number of steps (corners), 'stepsPerTurn' steps would be a full circle, generally: itt=(stepsPerTurn*turns)
            output is a 2D coordinate along the spiral, starting outwards """
        circumscribedDiam: Callable[[float], float] = lambda inscribedDiam : (inscribedDiam / np.cos(np.deg2rad(180/subclass.stepsPerTurn))) # just a macro for calculating the diameter of a circumscribed circle (spiral diam is inscribed)
        ## the easiest way is just to consider it as a circularSpiral, sampled at 6 points per rotation, with the diameter and spacing of a a circumscribed circle (sothat the inscribed circle has the desired diam)
        return(circularSpiral.calcPos(itt*np.deg2rad(360/subclass.stepsPerTurn), circumscribedDiam(diam), circumscribedDiam(spacing), CCW))
    @classmethod
    def calcLength(subclass, itt: int, diam: float, spacing: float) -> float:
        """ returns the length of the spiral at a given itt (without iterating, direct calculation) """
        circumscribedDiam: Callable[[float], float] = lambda inscribedDiam : (inscribedDiam / np.cos(np.deg2rad(180/subclass.stepsPerTurn))) # just a macro for calculating the diameter of a circumscribed circle (spiral diam is inscribed)
        return(itt * np.sin(np.deg2rad(180/subclass.stepsPerTurn)) * (circumscribedDiam(diam) + calcInnerDiam(itt/subclass.stepsPerTurn, circumscribedDiam(diam), circumscribedDiam(spacing))) / 2)
        ## similar to the circularSpiral, the perimiter (circumference) of an NthDimSpiral can be seem as the perimiter of the average polygon. Then just simplify the equations after inserting itt (calculating turn variable is a little extra)

class hexagonSpiral(NthDimSpiral):
    formulaCoefficients = {'wheeler' : (2.33, 3.82),
                            'monomial' : (1.28, -1.24, -0.174, 2.47, 1.77, -0.049),
                            'cur_sheet' : (1.09, 2.23, 0.00, 0.17)}
    stepsPerTurn: int = 6

class octagonSpiral(NthDimSpiral):
    formulaCoefficients = {'wheeler' : (2.25, 3.55),
                            'monomial' : (1.33, -1.21, -0.163, 2.43, 1.75, -0.049),
                            'cur_sheet' : (1.07, 2.29, 0.00, 0.19)}
    stepsPerTurn: int = 8

# class squareSpiral(NthDimSpiral): # NOTE: this is not a square (same way the hexagon and octagon are also technically illigal), and it has significantly different values (length!) to the hardcoded sqaure above.
#     formulaCoefficients = {'wheeler' : (2.34, 2.75),
#                             'monomial' : (1.62, -1.21, -0.147, 2.40, 1.78, -0.030),
#                             'cur_sheet' : (1.27, 2.07, 0.18, 0.13)}
#     stepsPerTurn: int = 4

# class triangleSpiral(NthDimSpiral): # this one i'd love to see in action, but i don't have formula coefficients for it
#     formulaCoefficients = {} # TBD
#     stepsPerTurn: int = 3

shapes = {'square' : squareSpiral(),
          'hexagon' : hexagonSpiral(),
          'octagon' : octagonSpiral(),
          'circle' : circularSpiral()}


def calcInnerDiam(turns: int, diam: float, spacing: float) -> float:
    """ calculate the (approximate) size of the empty space inside the coil """
    # return(abs(squareSpiral(turns*4, diam, spacing)[0] - squareSpiral(turns*4-1, diam, spacing)[0])) # get the length of the last line (as it is the shortest)
    return(diam - (turns * spacing * 2)) # fairly straightforward math

def calcReturnTraceLength(turns: int, spacing: float) -> float: # does not really need a function, but perhaps it will avoid silly mistakes in the future (when i've forgotten how this code works)
    """ calculate the (approximate) length of the return trace (assumed to be a straight downwards line) """
    return(turns * spacing)

def calcTraceClearance(spacing: float, traceWidth: float) -> float: # does not really need a function, but perhaps it will avoid silly mistakes in the future (when i've forgotten how this code works)
    return(spacing - traceWidth) # there should be enough space between the traces to aviod shorts (but do also consider capacitance as a significant factor)

def calcResistance(turns: int, diam: float, spacing: float, traceWidth: float, resistConst: float, shape: _shapeTypeHint) -> float:
    """ calculate the resistance of the coil in Ohms """
    coilLength = shape.calcLength(shape.stepsPerTurn*turns, diam, spacing) * distUnitMult # calculate the length of the coil itself (with 1 nice direct calculation (not iteration)) in meters
    coilResistance = resistConst * (coilLength / (traceWidth*distUnitMult)) # resistance = Rho * length / diam * width = resistConst * length/diam = resistance in ohms (all dist units in meters!)
    # ## also factor in the return trace (TODO)
    # returnTraceLength = calcReturnTraceLength(turns, spacing)
    # returnTraceResistConst = (resistConst if (returnTraceResistConst is None) else returnTraceResistConst) # in case no argument was provided, default to the same resistance constant for both layers
    # if(returnTraceMatchResist):
    #     returnTraceWidth = traceWidth * (returnTraceResistConst / resistConst) # match resistance with the coil layer by changing trace width (generally, PCB's middle layers are thinner, so more width is needed)
    # returnTraceResistance = returnTraceResistConst * (returnTraceLength / (returnTraceWidth*distUnitMult))
    # coilResistance += returnTraceResistance
    return(coilResistance)

def calcInductance(turns: int, diam: float, spacing: float, traceWidth: float, shape: _shapeTypeHint, formula: str):
    """ returns inducance in Henry """
    if(formula not in shape.formulaCoefficients):  print("could not calcInductance(), for shape=", shape, " and formula=", formula);  return(-1.0)
    innerDiam = calcInnerDiam(turns, diam, spacing) # this function is the same for 
    fillFactor = (diam - innerDiam) / (diam + innerDiam) # fill factor
    averageDiam = ((diam + innerDiam) / 2) * distUnitMult # average diameter of coil
    coeff = shape.formulaCoefficients[formula] # just a shorter name for more legible math below
    if(formula == 'wheeler'):
        return(coeff[0] * magneticConstant * (turns**2) * averageDiam / (1 + (coeff[1] * fillFactor)))
    elif(formula == 'monomial'):
        traceClearance = calcTraceClearance(spacing, traceWidth) * distUnitMult
        outputMult = (10**-6) # this formula outputs in mH by default, and i store coeff[0] (a.k.a Beta) as 10^3 times larger than the paper lists it (becuase if i'm scaling up anyway, might as well)
        return(outputMult * coeff[0] * ((diam*distUnitMult)**coeff[1]) * ((traceWidth*distUnitMult)**coeff[2]) * (averageDiam**coeff[3]) * (turns**coeff[4]) * (traceClearance**coeff[5]))
    elif(formula == 'cur_sheet'):
        return((coeff[0] * magneticConstant * (turns**2) * averageDiam * (np.log(coeff[1]/fillFactor) + (coeff[2]*fillFactor) + (coeff[3]*(fillFactor**2)))) / 2)
    else: print("impossible point reached in calcInductance(), check the formulaCoefficients formula names in this function!");  return(-1.0) # should never happen due to earlier check

class coilClass:
    """ a class to hold the parameter set and rendered output of a coil """
    ## some static class variables
    RhoCopper = 1.72 * 10**-8 # Ohms * meter
    topLayerHeight = 34.8 * 2  * 10**-6 # 34.8um per oz (to meters)
    topLayerResistConst = RhoCopper / topLayerHeight # turn into a single parameter to pass to the resistance calculation function. Not for human purposes, just for a shorter function call!
    ## these are some constants from the paper (see top of code for link)
    
    def __init__(self, turns: int, diam: float, spacing: float, traceWidth: float, shape: _shapeTypeHint = shapes['square'], formula: str = 'wheeler'):
        ## the parameters of the coil are stored as local non-static class variables:
        self.turns = turns
        self.diam = diam
        self.spacing = spacing
        self.traceWidth = traceWidth
        self.shape = (shape if issubclass(shape.__class__, _shapeTypeHint) else squareSpiral()) # determine if the desired shape string is in the formulaCoefficients dict
        if(self.shape.__class__ != shape.__class__):  print("coilClass init() changing shape from:", shape, "to", self.shape, "because it's not a _shapeTypeHint subclass")
        self.formula = (formula if (formula in self.shape.formulaCoefficients) else 'wheeler') # determine if the desired formula string is in the formulaCoefficients dict
        if(self.formula != formula):  print("coilClass init() changing formula from:", formula, "to", self.formula, "because it's not in the "+str(self.shape)+".formulaCoefficients")

    ## the non-static class functions just refer to the static (global) functions above
    def calcCoilTraceLength(self):  return(self.shape.calcLength(self.turns*self.shape.stepsPerTurn, self.diam, self.spacing)) # discrete shapes need 1 extra step
    def calcInnerDiam(self):  return(calcInnerDiam(self.turns, self.diam, self.spacing))
    def calcTraceClearance(self):  return(calcTraceClearance(self.spacing, self.traceWidth))
    def calcReturnTraceLength(self):  return(calcReturnTraceLength(self.turns, self.spacing))
    def calcResistance(self):  return(calcResistance(self.turns, self.diam, self.spacing, self.traceWidth, coilClass.topLayerResistConst, self.shape))
    def calcInductance(self):  return(calcInductance(self.turns, self.diam, self.spacing, self.traceWidth, self.shape, self.formula))
    
    ## some ways of rendering the coil:
    def renderAsCoordinateList(self, angleResOverride: float = None):
        if(self.shape.isDiscrete):
            return([self.shape.calcPos(i, self.diam, self.spacing) for i in range(self.shape.stepsPerTurn*self.turns + 1)]) # a simple forloop to render all the corner positions
        else: # for continous shapes (e.g. circularSpiral)
            angleRes = (angleResOverride if (angleResOverride is not None) else angleRenderResDefault)
            return([self.shape.calcPos(i*angleRes, self.diam, self.spacing) for i in range(int(round((self.shape.stepsPerTurn*self.turns)/angleRes, 0)) + 1)]) # renders the continous shape at a predetermined resolution
    # def renderAsPolygon(self):
    #     # TODO


if __name__ == "__main__": # normal usage
    try:

        coil = coilClass(turns=10, diam=35, spacing=0.5, traceWidth=0.3 )#, shape=shapes['circle'], formula='monomial')
        renderedLineList = coil.renderAsCoordinateList()
        
        if(visualization):
            import pygameRenderer as PR # rendering code
            import pygameUI as UI # UI handling code

            ## some UI window initialization
            resolution = [1280, 720]
            windowHandler = PR.pygameWindowHandler(resolution)
            drawer = PR.pygameDrawer(windowHandler, resolution)
            
            drawer.localVar = coil # not my best code...
            drawer.localVarUpdated = False # a flag for the UI to trigger a re-calculation
            makeDebugText: Callable[[coilClass], list[str]] = lambda coil :["diam [mm]: "+str(round(coil.diam, 1)),
                                                                            "shape: "+coil.shape.__class__.__name__,
                                                                            "formula: "+coil.formula,
                                                                            "innerDiam [mm]: "+str(round(coil.calcInnerDiam(), 1)),
                                                                            "turns: "+str(coil.turns),
                                                                            "traceWidth [mm]: "+str(round(coil.traceWidth, 2)),
                                                                            "spacing [mm]: "+str(round(coil.spacing, 2)),
                                                                            "clearance [mm]: "+str(round(coil.calcTraceClearance(), 2)),
                                                                            "lenght (uncoiled) [mm]: "+str(round(coil.calcCoilTraceLength(), 2)),
                                                                            "return trace length [mm]: "+str(round(coil.calcReturnTraceLength(), 2)),
                                                                            "resistance [mOhm]: "+str(round(coil.calcResistance() * 1000, 2)),
                                                                            "inductance [uH]: "+str(round(coil.calcInductance() * 1000000, 2)) ]
            drawer.debugText = makeDebugText(coil)

            ## visualization loop:
            while(windowHandler.keepRunning):
                drawer.renderBG() # draw background

                drawer.drawLineList(renderedLineList, coil.traceWidth)

                drawer.renderFG() # draw foreground (text and stuff)
                # drawer.redraw() # render all elements
                windowHandler.frameRefresh()
                UI.handleAllWindowEvents(drawer) # handle all window events like key/mouse presses, quitting, resizing, etc.
                if(drawer.localVarUpdated):
                    drawer.localVarUpdated = False
                    coil = drawer.localVar
                    renderedLineList = coil.renderAsCoordinateList()
                    drawer.debugText = makeDebugText(coil)

                    ## debug for the calcLength() functions:
                    # from pygameRenderer import distAngleBetwPos
                    # sumOfLengths = 0
                    # for i in range(1, len(renderedLineList)):
                    #     sumOfLengths += distAngleBetwPos(renderedLineList[i-1], renderedLineList[i])[0] # sum length manually
                    # print("sumOfLengths:", sumOfLengths)
    finally:
        if(visualization):
            try:
                windowHandler.pygameEnd() # correctly shut down pygame window
                print("stopped pygame window")
            except:
                print("couldn't run pygameEnd()")