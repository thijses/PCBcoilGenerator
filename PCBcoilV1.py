"""
this code is intended for generating (and visualizing) PCB coils (a.k.a. planar inductors), with 1 or more layers
this code can (currently) only produce coils with an equal width and height (one diameter parameter)

in the making of this code, i used these papers:
paper[1] @ https://stanford.edu/~boyd/papers/pdf/inductance_expressions.pdf     which is applied for demo purposes @ https://coil32.net/pcb-coil.html
paper[2] @ http://www.edatop.com/down/paper/NFC/A_new_calculation_for_designing_multilayer_planar_spiral_inductors_PDF.pdf
paper[3] @ https://www.researchgate.net/publication/271291453_Design_and_Optimization_of_Printed_Circuit_Board_Inductors_for_Wireless_Power_Transfer_System

the single-layer math comes from paper[1]
the multilayer coil calculations came from paper[2] and paper[3]

the current sheet formula is also mentioned in paper[2] and paper[3], which gives some confidence to prefer that method
the coefficients tables are exactly the same, as they all draw from another paper, under the name 'Greenhouse'

The way a PCB coil object may be stored/exported is as a collection of straight lines, as a rendered polygon, or as a formula.
In Altium there does not appear to be a way of importing a polygon, so it'll have to be a list of lines, i guess
In EasyEDA you can make polygons, but you'd have to manually fill in a lot of values, so a series of line would also be fewer steps.

TODO list:
 - research ways of importing the results into PCB design software
 - improve pygame rendering (pygame struggles to draw thick lines like i want and the circle aren't helping much)
 - add an auto-optimizer (given a few limits (diameter, clearance, layers, layerSpacing) and targets (inductance, resistance, layers?), find the optimim coil design (minimizing for number of layers, resistance, etc.))
 - find a way to model rectangular/oval coils (non-square)
"""


import numpy as np
from typing import Callable # just for type-hints to provide some nice syntax colering

visualization = True

angleRenderResDefault = np.deg2rad(10) # angular resolution when rendering continous (circular) coils
ozCopper = 1.0 # how many oz of copper the PCB has (on all layers, individual layer )

## scientific constants:
magneticConstant = 4*np.pi * 10**-7 # Mu (greek) = Newtons / Ampere    (vacuum permeability???)
## code constants
distUnitMult = 1/1000 # all distance units are in mm, so to convert back to meters, multiply with this

class _shapeTypeHint:
    formulaCoefficients: dict[str, tuple]
    stepsPerTurn: int | float # note: this is not actually how python typing works, it just forget to spit out an error. It's just for the humans
    # calcPos: Callable[[int|float,float,float,bool], tuple[float,float]] # the typing way of doing it
    # calcLength: Callable[[int|float,float,float], float]
    @staticmethod
    def calcPos(itt:int|float,diam:float,clearance:float,traceWidth:float,CCW:bool)->tuple[float, float]:  ... # the modern python way of type-hinting an undefined function
    @staticmethod
    def calcLength(itt:int|float,diam:float,clearance:float,traceWidth:float)->float:  ...
    isDiscrete: bool = True # most of the shapes have a discrete number points/corners/vertices by default. Only continous functions will need a render-resolution parameter
    def __repr__(self): # prints the name of the shape
        return("shape("+(self.__class__.__name__)+")")

class squareSpiral(_shapeTypeHint):
    formulaCoefficients = {'wheeler' : (2.34, 2.75),
                            'monomial' : (1.62, -1.21, -0.147, 2.40, 1.78, -0.030),
                            'cur_sheet' : (1.27, 2.07, 0.18, 0.13)}
    stepsPerTurn: int = 4 # multiply with number of turns to get 'itt' for functions below
    @staticmethod
    def calcPos(itt: int, diam: float, clearance: float, traceWidth: float, CCW=False) -> tuple[float, float]:
        """ input is the number of steps (corners), 4 steps would be a full circle, generally: itt=(stepsPerTurn*turns)
            output is a 2D coordinate along the spiral, starting outwards """
        spacing = calcTraceSpacing(clearance, traceWidth)
        x =      (1 if (((itt%4)>=2) ^ CCW) else -1)      * (((diam-traceWidth)/2) - ((itt//4)     * spacing))
        y = (1 if (((itt%4)==1) or ((itt%4)==2)) else -1) * (((diam-traceWidth)/2) - (((itt-1)//4) * spacing))
        return(x,y)
    @staticmethod
    def calcLength(itt: int, diam: float, clearance: float, traceWidth: float) -> float:
        """ returns the length of the spiral at a given itt (without iterating, direct calculation) """
        ## NOTE: if the spiral goes beyond the center point and grows larger again (it shouldn't), then the length will be negative). I'm intentionally not fixing that, becuase it makes for good debug info
        spacing = calcTraceSpacing(clearance, traceWidth)
        horLines = (itt//2)
        sumOfWidths = (horLines * (diam-traceWidth)) - ((((horLines-1)*horLines) / 2) * spacing) # length of all hor. lines = (horLines * diam) - triangular number of (horLines-1)
        vertLines = ((itt+1)//2)
        sumOfHeights = (vertLines * (diam-traceWidth)) - ((max(((vertLines-2)*(vertLines-1)) / 2, 0) - 1) * spacing) # length of all vert. lines
        return(sumOfWidths + sumOfHeights)
        ## paper[3] mentioned the formula: 4*turns*diam - 4*turns*tracewidth - (2*turns+1)^2 * (spacing)   but, please review their definitions of outer diameter and spacing before using this!

class circularSpiral(_shapeTypeHint):
    formulaCoefficients = {'wheeler' : (2.23, 3.45),
                            # the monomial formula does cover circular spirals
                            'cur_sheet' : (1.00, 2.46, 0.00, 0.20)}
    stepsPerTurn: float = 2*np.pi # multiply with number of turns to get 'angle' for functions below
    isDiscrete = False # let the renderer know that this shape needs a resolution parameter
    @staticmethod
    def calcPos(angle: float, diam: float, clearance: float, traceWidth: float, CCW=False) -> tuple[float, float]:
        """ input is an angle in radians, 2pi would be a full circle, generally: angle=(stepsPerTurn*turns)
            output is a 2D coordinate along the spiral, starting outwards """
        spacing = calcTraceSpacing(clearance, traceWidth)
        phaseShift = 0.0 # note: i have already phase-shifted (and inverted) the conventional cirlce by 90deg by using sin() for x and cos() for y (normally you would do it the other way around)
        x = (1 if CCW else -1) * np.sin(angle) * (((diam-traceWidth)/2) - ((angle/(2*np.pi)) * spacing))
        y =         -1         * np.cos(angle) * (((diam-traceWidth)/2) - ((angle/(2*np.pi)) * spacing))
        return(x,y)
    @staticmethod
    def calcLength(angle: float, diam: float, clearance: float, traceWidth: float) -> float:
        """ returns the length of the spiral at a given angle (without iterating, direct calculation) """
        turns = (angle/circularSpiral.stepsPerTurn) # (float)
        return(np.pi * turns * (diam + calcSimpleInnerDiam(turns, diam, clearance, traceWidth, circularSpiral())) / 2) # pi * turns * (diam + innerDiam) / 2 = basically just the circumference of the average diameter (outer+inner)/2

## now that the circularSpiral class exists, we can just derive sampled classes from that:
class NthDimSpiral(_shapeTypeHint): # a general class for Nth dimensional polygon spirals. Specify the number of points/corners/sides (6 for hexagon, 8 for octagon, etc.) and provide formulaCoefficients in the subclass
    @classmethod
    def circumDiam(subclass, inscribedDiam: float) -> float:  return(inscribedDiam / np.cos(np.deg2rad(180/subclass.stepsPerTurn))) # just a macro for calculating the diameter of a circumscribed circle (spiral diam is inscribed)
    @classmethod # class methods let you use subclass static variables
    def calcPos(subclass, itt: int, diam: float, clearance: float, traceWidth: float, CCW=False) -> tuple[float, float]:
        """ input is the number of steps (corners), 'stepsPerTurn' steps would be a full circle, generally: itt=(stepsPerTurn*turns)
            output is a 2D coordinate along the spiral, starting outwards """
        ## the easiest way is just to consider it as a circularSpiral, sampled at 6 points per rotation, with the diameter and spacing of a a circumscribed circle (sothat the inscribed circle has the desired diam)
        # return(circularSpiral.calcPos(itt*np.deg2rad(360/subclass.stepsPerTurn), subclass.circumDiam(diam), subclass.circumDiam(clearance), subclass.circumDiam(traceWidth), CCW))
        ## but i wish to have custom phase-shift based on the number of corners (to orient it straight)
        spacing = calcTraceSpacing(subclass.circumDiam(clearance), subclass.circumDiam(traceWidth))
        angle = itt*np.deg2rad(360/subclass.stepsPerTurn)
        circumscribedDiam = subclass.circumDiam(diam-traceWidth)
        phaseShift = np.deg2rad(180/subclass.stepsPerTurn)
        x = (1 if CCW else -1) * np.sin(angle+phaseShift) * ((circumscribedDiam/2) - ((angle/(2*np.pi)) * spacing))
        y =         -1         * np.cos(angle+phaseShift) * ((circumscribedDiam/2) - ((angle/(2*np.pi)) * spacing))
        return(x,y)
    @classmethod
    def calcLength(subclass, itt: int, diam: float, clearance: float, traceWidth: float) -> float:
        """ returns the length of the spiral at a given itt (without iterating, direct calculation) """
        return(itt * np.sin(np.deg2rad(180/subclass.stepsPerTurn)) * (subclass.circumDiam(diam) + calcSimpleInnerDiam(itt/subclass.stepsPerTurn, subclass.circumDiam(diam), subclass.circumDiam(clearance), subclass.circumDiam(traceWidth), NthDimSpiral())) / 2)
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



def calcSimpleInnerDiam(turns: int, diam: float, clearance: float, traceWidth: float, shape: _shapeTypeHint) -> float:
    """ calculate the (approximate) inner diameter of the coil 
        (in a way that makes sense to me, personally) (same as calcTrueInnerDiam ONLY for squareSpiral) """
    spacing = calcTraceSpacing(clearance, traceWidth)
    return(((diam/2) - ((turns - (1 if (isinstance(shape, squareSpiral)) else 0)) * spacing) - traceWidth)*2)
    ## rInner = rOuter - turns*spacing - traceWidth. this is the smallest circle that shares a center with the (naive) outer diam (but not the 'true' outer diam)
    ## EXCEPT the squareSpiral, which has basically 1 turn less worth of innerdiam

def _calcTrueDiamOffset(clearance: float, traceWidth: float, shape: _shapeTypeHint) -> float:
    """ both inner- and outer TrueDiam (as defined in the papers) circle does not share a center with the outer (except for the squareSpiral)"""
    if(isinstance(shape, squareSpiral)):  return(0.0) # for squareSpiral, there is no offset
    else:  return(calcTraceSpacing(clearance, traceWidth) / 4) # for circular spirals and polygons, still not that complicated
    ## note: for NthDimSpirals, the calculation should be the same as for circularSpirals (because of the inscribed-circle-based definition)

def calcTrueInnerDiam(turns: int, diam: float, clearance: float, traceWidth: float, shape: _shapeTypeHint) -> float:
    """ calculate the (exact) inner diameter of the coil (except for the squareSpiral)
        it does not share a center with other diameter(s), as it is offset by _calcTrueDiamOffset() away from the start of the spiral 
        (EXCEPT for the squareSpiral, which just uses the (naive) outer diam and simpleInnerDiam, and no offsets) """
    ## according to all of the papers, inner diameter is defined as the distance between the innermost point and the nearest trace found when tracing a line through the (spiral) center
    ##  this means that the inner cirlce does NOT share a center point with the outer diameter
    return(calcSimpleInnerDiam(turns, diam, clearance, traceWidth, shape) + (_calcTrueDiamOffset(clearance, traceWidth, shape)*2))

def calcTrueDiam(diam: float, clearance: float, traceWidth: float, shape: _shapeTypeHint) -> float:
    """ the diameters (as defined in the papers) is the largest distance from starting point, in line with the center
        it does not share a center with other diameter(s), as it is offset by _calcTrueDiamOffset() towards the start of the spiral
        (EXCEPT for the squareSpiral, which just uses the (naive) outer diam and simpleInnerDiam, and no offsets) """
    return(diam - (_calcTrueDiamOffset(clearance, traceWidth, shape)*2))


def calcReturnTraceLength(turns: int, clearance: float, traceWidth: float) -> float: # does not really need a function, but perhaps it will avoid silly mistakes in the future (when i've forgotten how this code works)
    """ calculate the (approximate) length of the return trace (assumed to be a straight downwards line) """
    return(turns * calcTraceSpacing(clearance, traceWidth))

# def calcTraceClearance(spacing: float, traceWidth: float) -> float: # does not really need a function, but perhaps it will avoid silly mistakes in the future (when i've forgotten how this code works)
#     """ just a macro for (spacing - traceWidth) """
#     return(spacing - traceWidth)
def calcTraceSpacing(clearance: float, traceWidth: float) -> float: # does not really need a function, but perhaps it will avoid silly mistakes in the future (when i've forgotten how this code works)
    """ just a macro for (clearance + traceWidth) """
    return(clearance + traceWidth) # 

def calcCoilTraceResistance(turns: int, diam: float, clearance: float, traceWidth: float, resistConst: float, shape: _shapeTypeHint) -> float:
    """ calculate the resistance of the coil in Ohms (single layer, return trace ignored)"""
    coilLength = shape.calcLength(shape.stepsPerTurn*turns, diam, clearance, traceWidth) * distUnitMult # calculate the length of the coil itself (with 1 nice direct calculation (not iteration)) in meters
    coilResistance = resistConst * (coilLength / (traceWidth*distUnitMult)) # resistance = Rho * length / diam * width = resistConst * length/diam = resistance in ohms (all dist units in meters!)
    return(coilResistance)

def calcTotalResistance(turns: int, diam: float, clearance: float, traceWidth: float, layers: int, resistConst: float, shape: _shapeTypeHint) -> float:
    """ calculate the resistance of the entire coil in Ohms """
    singleResist = calcCoilTraceResistance(turns, diam, clearance, traceWidth, resistConst, shape)
    coilResistance = singleResist * layers
    # ## also factor in the vias (TODO)
    # coilResistance += viaResistance * layers
    # ## also factor in the return trace (TODO)
    # if((layers%2)!=0): # if there is an odd number of layers (even layers would eliminate the return trace entirely)
    #   returnTraceLength = calcReturnTraceLength(turns, clearance, traceWidth)
    #   returnTraceResistConst = (resistConst if (returnTraceResistConst is None) else returnTraceResistConst) # in case no argument was provided, default to the same resistance constant for both layers
    #   if(returnTraceMatchResist):
    #       returnTraceWidth = traceWidth * (returnTraceResistConst / resistConst) # match resistance with the coil layer by changing trace width (generally, PCB's middle layers are thinner, so more width is needed)
    #   returnTraceResistance = returnTraceResistConst * (returnTraceLength / (returnTraceWidth*distUnitMult))
    #   coilResistance += returnTraceResistance
    return(coilResistance)

def calcInductance(turns: int, diam: float, clearance: float, traceWidth: float, shape: _shapeTypeHint, formula: str):
    """ returns inducance (in Henry) of a PCB coil (single layer)
        math comes from: https://stanford.edu/~boyd/papers/pdf/inductance_expressions.pdf """
    if(formula not in shape.formulaCoefficients):  print("could not calcInductance(), for shape=", shape, " and formula=", formula);  return(-1.0)
    trueInnerDiamM = calcTrueInnerDiam(turns, diam, clearance, traceWidth, shape) * distUnitMult # inner diameter as defined in the papers
    trueDiamM = calcTrueDiam(diam, clearance, traceWidth, shape) * distUnitMult # outer diameter as defined in the papers
    fillFactor = (trueDiamM - trueInnerDiamM) / (trueDiamM + trueInnerDiamM) # fill factor
    averageDiamM = ((trueDiamM + trueInnerDiamM) / 2) # average diameter of coil
    coeff = shape.formulaCoefficients[formula] # just a shorter name for more legible math below
    if(formula == 'wheeler'):
        return(coeff[0] * magneticConstant * (turns**2) * averageDiamM / (1 + (coeff[1] * fillFactor)))
    elif(formula == 'monomial'):
        outputMult = (10**-6) # this formula outputs in mH by default, and i store coeff[0] (a.k.a Beta) as 10^3 times larger than the paper lists it (becuase if i'm scaling up anyway, might as well)
        return(outputMult * coeff[0] * (trueDiamM**coeff[1]) * ((traceWidth*distUnitMult)**coeff[2]) * (averageDiamM**coeff[3]) * (turns**coeff[4]) * (clearance**coeff[5]))
    elif(formula == 'cur_sheet'):
        return((coeff[0] * magneticConstant * (turns**2) * averageDiamM * (np.log(coeff[1]/fillFactor) + (coeff[2]*fillFactor) + (coeff[3]*(fillFactor**2)))) / 2)
    else: print("impossible point reached in calcInductance(), check the formulaCoefficients formula names in this function!");  return(-1.0) # should never happen due to earlier check

def calcInductanceMultilayer(turns: int, diam: float, clearance: float, traceWidth: float, layers: int, layerSpacing: float, shape: _shapeTypeHint, formula: str):
    """ returns inducance (in Henry) of PCB coil (multi-layer)
        math comes from: http://www.edatop.com/down/paper/NFC/A_new_calculation_for_designing_multilayer_planar_spiral_inductors_PDF.pdf """
    singleInduct = calcInductance(turns, diam, clearance, traceWidth, shape, formula) # calculate the inductance of a single layer the same way
    if(singleInduct < 0):  print("can't calcInductanceMultilayer(), calcInductance() returned <0:", singleInduct);  return(-1.0) # should never happen
    
    ## now, the mutual inductance
    ## if the fields are aligned ("Cumulatively coupled"), the mutual inductance is added, if the fields oppose eachother ("Differentially coupled"), they mutual inductance is subtracted
    ## luckily, i all the coils are Cumulatively coupled, so that at least makes it a little easier
    ## at this point however, the math (in both papers that use it), gets real vague. 
    ##  In paper[2], the general formula for N-layer PCBs is not described, only an example (which has unfortunately ambiguous parameters)
    ##  in paper[3], a general form is expressed (although slightly ambiguous), but the definition of the coupling factor K is not given (for coupling between PCB layers)
    ## So, i've decided to combine the 2 papers: the K-factor formula from paper[2], used for the inductance formula from paper[3]
    ## HOWEVER, the coupling factor formula is intended for use with turns=5~20 and layerSpacing=0.75~2mm
    ##  i plotted that, just to see what the shape of this complicated 4th order polynomial really is: https://www.desmos.com/calculator/3k5o6fvvwe     turns out it's damn near a straight line!
    
    ## the formula for coupling factor between PCB coils (from paper[2]): # NOTE: this formula is intended for use with turns=5~20 and layerSpacing=0.75~2mm
    couplingFactor: Callable[[float,float], float] = lambda turns, layerSpacingMM : ((turns**2)/((0.184*(layerSpacingMM**3)-0.525*(layerSpacingMM**2)+1.038*layerSpacingMM+1.001)*(1.67*(turns**2)-5.84*turns+65)*0.64)) # a macro for calculating the coupling factor Kc
    
    ## the formula for inductance (from paper[3]) (assuming i'm interpreting it correctly):
    mutualInductanceFact = 0.0 # note: this is alsmost mutual inductance, it just needs to be multiplied with singleInduct (which is done at the end)
    for i in range(layers-1):
        mutualInductanceFact += (layers-1-i) * couplingFactor(turns, (i+1) * layerSpacing)
    totalInduct = singleInduct * (layers + (2*mutualInductanceFact))
    return(totalInduct)

class coilClass:
    """ a class to hold the parameter set and rendered output of a coil """
    ## some static class variables
    RhoCopper = 1.72 * 10**-8 # Ohms * meter
    topLayerHeight = 34.8 * ozCopper  * 10**-6 # 34.8um per oz (to meters)
    topLayerResistConst = RhoCopper / topLayerHeight # turn into a single parameter to pass to the resistance calculation function. Not for human purposes, just for a shorter function call!
    ## these are some constants from the paper (see top of code for link)
    
    def __init__(self, turns:int, diam:float, clearance:float, traceWidth:float, layers:int=1, layerSpacing:float=0.0, shape:_shapeTypeHint=shapes['square'], formula:str='cur_sheet', CCW:bool=False):
        ## the parameters of the coil are stored as local non-static class variables:
        self.turns = turns
        self.diam = diam
        # self.spacing = spacing # seems more logical to me, but all the papers prefer to qualify a coil by its clearance (which they call spacing)
        self.clearance = clearance
        self.traceWidth = traceWidth
        self.layers = layers
        self.layerSpacing = layerSpacing # (only used if layers > 1) layerSpacing is calculated as: PCBthickness/(N-1) - copperThickness*(N-1) where N is the number of copper layers (e.g. 2, 4, 6)
        if((layers>1) and (layerSpacing <= 0.0)):  raise(Exception("please set layerSpacing in coilClass constructor when layers>1"))
        self.shape = (shape if issubclass(shape.__class__, _shapeTypeHint) else self.__init__.__defaults__[-2]) # determine if the desired shape string is in the formulaCoefficients dict
        if(self.shape.__class__ != shape.__class__):  print("coilClass init() changing shape from:", shape, "to", self.shape, "because it's not a _shapeTypeHint subclass")
        self.formula = (formula if (formula in self.shape.formulaCoefficients) else self.__init__.__defaults__[-1]) # determine if the desired formula string is in the formulaCoefficients dict
        if(self.formula != formula):  print("coilClass init() changing formula from:", formula, "to", self.formula, "because it's not in the "+str(self.shape)+".formulaCoefficients")
        self.CCW = CCW

    ## the non-static class functions just refer to the static (global) functions above
    def calcCoilTraceLength(self):  return(self.shape.calcLength(self.turns*self.shape.stepsPerTurn, self.diam, self.clearance, self.traceWidth) * self.layers)

    def calcSimpleInnerDiam(self):  return(calcSimpleInnerDiam(self.turns, self.diam, self.clearance, self.traceWidth, self.shape))
    def calcTrueInnerDiam(self):  return(calcTrueInnerDiam(self.turns, self.diam, self.clearance, self.traceWidth, self.shape))
    def calcTrueDiam(self):  return(calcTrueDiam(self.diam, self.clearance, self.traceWidth, self.shape))
    def _calcTrueDiamOffset(self):  return(_calcTrueDiamOffset(self.clearance, self.traceWidth, self.shape))

    def calcTraceSpacing(self):  return(calcTraceSpacing(self.clearance, self.traceWidth))
    def calcReturnTraceLength(self):  return(calcReturnTraceLength(self.turns, self.clearance, self.traceWidth) if ((self.layers%2)!=0) else 0.0) # coils with an even number of layers don't need a return trace
    
    def calcTotalResistance(self):  return(calcTotalResistance(self.turns, self.diam, self.clearance, self.traceWidth, self.layers, coilClass.topLayerResistConst, self.shape))
    def calcInductance(self):  return(calcInductance(self.turns, self.diam, self.clearance, self.traceWidth, self.shape, self.formula) if (self.layers == 1) else \
                                      calcInductanceMultilayer(self.turns, self.diam, self.clearance, self.traceWidth, self.layers, self.layerSpacing, self.shape, self.formula))
    
    ## some ways of rendering the coil:
    def renderAsCoordinateList(self, angleResOverride: float = None):
        if(self.shape.isDiscrete):
            return([self.shape.calcPos(i, self.diam, self.clearance, self.traceWidth, self.CCW) for i in range(self.shape.stepsPerTurn*self.turns + 1)]) # a simple forloop to render all the corner positions
        else: # for continous shapes (e.g. circularSpiral)
            angleRes = (angleResOverride if (angleResOverride is not None) else angleRenderResDefault)
            return([self.shape.calcPos(i*angleRes, self.diam, self.clearance, self.traceWidth, self.CCW) for i in range(int(round((self.shape.stepsPerTurn*self.turns)/angleRes, 0)) + 1)]) # renders the continous shape at a predetermined resolution
    # def renderAsPolygon(self):
    #     # TODO


if __name__ == "__main__": # normal usage
    try:

        coil = coilClass(turns=9, diam=40, clearance=0.15, traceWidth=0.9, layers=2, layerSpacing=0.4, shape=shapes['circle'], formula='cur_sheet')
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
            drawer.debugText = drawer.makeDebugText(coil)

            ## visualization loop:
            while(windowHandler.keepRunning):
                drawer.renderBG() # draw background

                drawer.drawLineList(renderedLineList)

                drawer.renderFG() # draw foreground (text and stuff)
                # drawer.redraw() # render all elements
                windowHandler.frameRefresh()
                UI.handleAllWindowEvents(drawer) # handle all window events like key/mouse presses, quitting, resizing, etc.
                if(drawer.localVarUpdated):
                    drawer.localVarUpdated = False
                    coil = drawer.localVar
                    renderedLineList = coil.renderAsCoordinateList()
                    drawer.debugText = drawer.makeDebugText(coil)

                    # debug for the calcLength() functions:
                    from pygameRenderer import distAngleBetwPos
                    sumOfLengths = 0
                    for i in range(1, len(renderedLineList)):
                        sumOfLengths += distAngleBetwPos(renderedLineList[i-1], renderedLineList[i])[0] # sum length manually
                    print("sumOfLengths:", sumOfLengths)
    finally:
        if(visualization):
            try:
                windowHandler.pygameEnd() # correctly shut down pygame window
                print("stopped pygame window")
            except:
                print("couldn't run pygameEnd()")