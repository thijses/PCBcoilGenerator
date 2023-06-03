# import numpy as np

couplingConstant_D : tuple[float] = (1.025485443, -0.201166582) # like (D0,D1) where k = D1*s + D0 (1st order polynomial)

outerLayerCopperThickness = 0.035
innerLayerCopperThickness = 0.0152
# dielectricConstants: dict[str,float] = {'None':0.0, 'core' : 4.6, '7628' : 4.6, '2116' : 4.25, '3313' : 4.05} # do not seem to affect things significantly

layerStack : tuple[float] \
            = (outerLayerCopperThickness,
                0.0994,
                innerLayerCopperThickness,
                0.35,
                innerLayerCopperThickness,
                0.1088,
                innerLayerCopperThickness,
                0.35,
                innerLayerCopperThickness,
                0.0994,
                outerLayerCopperThickness,
                )

Lsingle = 3.058 # inductance of a single layer (uH)
N = (len(layerStack)//2)+1   # number of layers

sumOfSpacings = 0.0
for i in range(0, len(layerStack)-2, 2): # Note: this could go to len(layerStack), but the last entry would skip the j for-loop below entirely.
    for j in range(i+1, len(layerStack)-1, 2):
        spacing = sum(layerStack[i:(j+2)]) # total thickness (incuding copper) from layer i to layer (j+1)
        spacing -= (layerStack[i] + layerStack[(j+1)]) / 2 # subtract half the thickness of both copper layers, (so the calculations are done from the centers of the copper layers)
        sumOfSpacings += spacing
        # sumOfCouplingFactors += (couplingConstant_D[1] * spacing) + couplingConstant_D[0] # DEPRICATED. The sumOfSpacings is used instead (along with a triangular number for D[0], see code below)

triangularNumber = (N*(N-1))/2 # triangular number
sumOfCouplingFactors = (couplingConstant_D[1] * sumOfSpacings) + (triangularNumber * couplingConstant_D[0]) # preliminary formula (final formula may include more parameters)
Lmulti = Lsingle * (N + 2*sumOfCouplingFactors) # preliminary formula (final formula may include more parameters)
print(Lmulti)
