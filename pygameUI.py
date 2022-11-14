import pygame       #python game library, used for the visualization
import time         #used for debugging
import numpy as np  #general math library

import pygameRenderer as rend

# cursor in the shape of a flag
flagCurs = ("ooo         ooooooooo   ",
            "oo ooooooooo...XXXX..ooo",
            "oo ....XXXX....XXXX....o",
            "oo ....XXXX....XXXX....o",
            "oo ....XXXX.XXX....XX..o",
            "oo XXXX....XXXX....XXXXo",
            "oo XXXX....XXXX....XXXXo",
            "oo XXXX....X...XXXX..XXo",
            "oo ....XXXX....XXXX....o",
            "oo ....XXXX....XXXX....o",
            "ooo....XXXX.ooooooooo..o",
            "oo ooooooooo         ooo",
            "oo                      ",
            "oo                      ",
            "oo                      ",
            "oo                      ",
            "oo                      ",
            "oo                      ",
            "oo                      ",
            "oo                      ",
            "oo                      ",
            "oo                      ",
            "oo                      ",
            "oo                      ")
flagCurs16  =  ("oooooooooooooooo", #1
                "oo ...XXX...XXXo",
                "oo ...XXX...XXXo",
                "oo XXX...XXX...o", #4
                "oo XXX...XXX...o",
                "oo ...XXX...XXXo",
                "oo ...XXX...XXXo",
                "oo XXX...XXX...o", #8
                "oo XXX...XXX...o",
                "oooooooooooooooo",
                "oo              ",
                "oo              ", #12
                "oo              ",
                "oo              ",
                "oo              ",
                "oo              ") #16
global flagCurs24Data, flagCurs16Data, flagCursorSet, deleteCursorSet
flagCurs24Data = ((24,24),(0,23)) + pygame.cursors.compile(flagCurs, 'X', '.', 'o')
flagCurs16Data = ((16,16),(0,15)) + pygame.cursors.compile(flagCurs16, 'X', '.', 'o')
flagCursorSet = False
deleteCursorSet = False



def handleMousePress(pygameDrawerInput: rend.pygameDrawer, buttonDown: bool, button: int, pos, eventToHandle: pygame.event.Event):
    """(UI element) handle the mouse-press-events"""
    if(buttonDown and ((button == 1) or (button == 3))): #left/rigth mouse button pressed (down)
        pygame.event.set_grab(1)
        if(pygame.key.get_pressed()[pygame.K_f]):
            pygame.mouse.set_cursor(flagCurs16Data[0], flagCurs16Data[1], flagCurs16Data[2], flagCurs16Data[3]) #smaller flag cursor
        ## put code you want to run when a mouse button is pressed (not released) here
        leftOrRight = (True if (button == 3) else False)
        realPos = pygameDrawerInput.pixelsToRealPos(pos) # convert to real units
    elif((button == 1) or (button == 3)): #if left/right mouse button released
        pygame.event.set_grab(0) # allow the mouse to exit the window once again
        if(pygame.key.get_pressed()[pygame.K_f]): #flag cursor stuff
            pygame.mouse.set_cursor(flagCurs24Data[0], flagCurs24Data[1], flagCurs24Data[2], flagCurs24Data[3]) #smaller flag cursor
        ## put code you want to run when a mouse button is released here
        leftOrRight = (True if (button == 3) else False)
        realPos = pygameDrawerInput.pixelsToRealPos(pos) # convert to real units
    elif(button==2): #middle mouse button
        ## dragging the view by holding the middle mouse button
        if(buttonDown): #mouse pressed down
            pygame.event.set_grab(1)
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND)
            pygameDrawerInput.movingViewOffset = True
            pygameDrawerInput.movingViewOffsetMouseStart = pygame.mouse.get_pos()
            pygameDrawerInput.prevViewOffset = (pygameDrawerInput.viewOffset[0], pygameDrawerInput.viewOffset[1])
        else:           #mouse released
            pygame.event.set_grab(0)
            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
            pygameDrawerInput._updateViewOffset() #update it one last time (or at all, if this hasn't been running in redraw())
            pygameDrawerInput.movingViewOffset = False

def handleKeyPress(pygameDrawerInput: rend.pygameDrawer, keyDown: bool, key: int, eventToHandle: pygame.event.Event):
    """(UI element) handle the key-press-events"""
    if(keyDown): #most things only happen on keyDown, this just saves a few lines
        if(key==pygame.K_z): # z for zooming type toggle
            pygameDrawerInput.centerZooming = not pygameDrawerInput.centerZooming # toggle
        elif(key==pygame.K_g): # g for grid on/off toggle
            pygameDrawerInput.drawGrid = not pygameDrawerInput.drawGrid # toggle
        elif(key==pygame.K_s): # s for saving (TBD!)
            saveStartTime = time.time()
            try:
                if(pygameDrawerInput.localVar is not None):
                    import DXFexporter as DXFexp
                    for outputFormat in DXFexp.DXFoutputFormats:
                        filenames = DXFexp.saveDXF(pygameDrawerInput.localVar, outputFormat)
                        print("saved", outputFormat, "files:", filenames)
                    print("file saving took", round(time.time()-saveStartTime, 2), "seconds")
                else:
                    print("failed to save file, localVar is", pygameDrawerInput.localVar)
            except Exception as excep:
                print("failed to save file, exception:", excep)
        elif(key==pygame.K_t): # t
            try:
                if(pygameDrawerInput.debugText is not None):
                    keyList = list(pygameDrawerInput.debugText.keys()) # bad code (but it is generalizable)
                    if(pygameDrawerInput.debugTextKey in keyList):
                        nextKeyIndex = keyList.index(pygameDrawerInput.debugTextKey) + 1
                        if(nextKeyIndex >= len(keyList)):  pygameDrawerInput.debugTextKey = "" # no key
                        else:  pygameDrawerInput.debugTextKey = keyList[nextKeyIndex]
                    else:
                        pygameDrawerInput.debugTextKey = keyList[0]
            except Exception as excep:
                print("fialed to increment debugTextKey from pygameUI:", excep)
        # elif(key==pygame.K_v): # v
        #     ## TBD: center view?
#        elif(key==pygame.K_d): # d   (for debug)

        if(pygameDrawerInput.localVar is not None): # coil adjustment though UI requires a little bit of synchronization effor (also, python doesnt do pointers)

            ## changing the number of turns
            if((key==pygame.K_MINUS) or (key==pygame.K_EQUALS)): # - or =
                pygameDrawerInput.localVar.turns += 1 * (1 if (key==pygame.K_EQUALS) else -1)
                if(pygameDrawerInput.localVar.turns < 1):
                    pygameDrawerInput.localVar.turns = 1
            
            ## changing the (outer) diameter
            elif((key==pygame.K_LEFTBRACKET) or (key==pygame.K_RIGHTBRACKET)): # [ or ]
                pygameDrawerInput.localVar.diam += 1 * (1 if (key==pygame.K_RIGHTBRACKET) else -1)
                if(pygameDrawerInput.localVar.diam < 1):
                    pygameDrawerInput.localVar.diam = 1
                    
            ## changing the width of the coil trace
            elif((key==pygame.K_SEMICOLON) or (key==pygame.K_QUOTE)): # ; or '
                pygameDrawerInput.localVar.traceWidth += 0.05 * (1 if (key==pygame.K_QUOTE) else -1)
                if(pygameDrawerInput.localVar.traceWidth < 0.05):
                    pygameDrawerInput.localVar.traceWidth = 0.05
            
            ## changing the clearance between the turns
            elif((key==pygame.K_PERIOD) or (key==pygame.K_SLASH)): # . or /
                pygameDrawerInput.localVar.clearance += 0.05 * (1 if (key==pygame.K_SLASH) else -1)
                if(pygameDrawerInput.localVar.clearance < 0.05):
                    pygameDrawerInput.localVar.clearance = 0.05
            
            ## changing the thickness of the copper layers
            elif((key==pygame.K_u) or (key==pygame.K_i)): # u or i
                pygameDrawerInput.localVar.ozCopper += 0.5 * (1 if (key==pygame.K_i) else -1)
                if(pygameDrawerInput.localVar.ozCopper < 0.5):
                    pygameDrawerInput.localVar.ozCopper = 0.5
            
            ## changing the number of layers (V1 only)
            elif((key==pygame.K_k) or (key==pygame.K_l)): # k or l
                pygameDrawerInput.localVar.layers += 1 * (1 if (key==pygame.K_l) else -1)
                if(pygameDrawerInput.localVar.layers < 1):
                    pygameDrawerInput.localVar.layers = 1
            
            ## changing the thickness of the PCB (V1 only)
            elif((key==pygame.K_m) or (key==pygame.K_COMMA)): # m or ,
                if(pygameDrawerInput.localVar.layers > 1):
                    pygameDrawerInput.localVar.PCBthickness += 0.2 * (1 if (key==pygame.K_COMMA) else -1)
                    if(pygameDrawerInput.localVar.PCBthickness < 0.2):
                        pygameDrawerInput.localVar.PCBthickness = 0.2
            
            ## changing the shape of the coil
            elif((key==pygame.K_9) or (key==pygame.K_0)): # 9 or 0
                ## here is some absolutely awful, truly terrible code, do deal with my human-legiblity-focussed-class-structured code
                try:
                    from __main__ import shapes # bad
                    shapes: dict
                    nextKeyIndex = [item.__class__ for item in list(shapes.values())].index(pygameDrawerInput.localVar.shape.__class__) # worse
                    nextKeyIndex += (1 if (key==pygame.K_0) else -1) # increment/decrement
                    if(nextKeyIndex >= len(shapes)):  nextKeyIndex = 0 # positive rollover
                    elif(nextKeyIndex < 0):           nextKeyIndex = len(shapes)-1 # negative rollover
                    pygameDrawerInput.localVar.shape = shapes[list(shapes.keys())[nextKeyIndex]] # awful
                    ## not all shapes have all formulas enabled (e.g. circularSpiral doesn't have 'monomial' formula):
                    if(pygameDrawerInput.localVar.formula not in pygameDrawerInput.localVar.shape.formulaCoefficients): # if the formula (str) is not available (not a key in coeff. dict)
                        pygameDrawerInput.localVar.formula = list(pygameDrawerInput.localVar.shape.formulaCoefficients.keys())[0] # set it to the first formula (key str) that is available
                except Exception as excep:
                    print("fialed to increment shape from pygameUI:", excep)
            
            ## changing the formula used to calculate the inductance of the coil
            elif((key==pygame.K_o) or (key==pygame.K_p)): # o or p
                try:
                    temp = list(pygameDrawerInput.localVar.shape.formulaCoefficients.keys()) # get a list of possible formulas (key str) for the current shape
                    nextKeyIndex = temp.index(pygameDrawerInput.localVar.formula) # worse
                    nextKeyIndex += (1 if (key==pygame.K_p) else -1) # increment/decrement
                    if(nextKeyIndex >= len(temp)):  nextKeyIndex = 0 # positive rollover
                    elif(nextKeyIndex < 0):           nextKeyIndex = len(temp)-1 # negative rollover
                    pygameDrawerInput.localVar.formula = temp[nextKeyIndex]
                except Exception as excep:
                    print("fialed to increment formula from pygameUI:", excep)
            
            ## changing the direction of the spiral (V1 only)
            elif(key==pygame.K_SPACE): # spacebar
                pygameDrawerInput.localVar.CCW = not pygameDrawerInput.localVar.CCW
            
            pygameDrawerInput.localVarUpdated = True # let the drawer know it's time to re-render the coil (even if none of the key if-statements are true, it's fine)


# def currentpygameDrawerInput(pygameDrawerInputList: list[rend.pygameDrawer], mousePos: tuple[int,int]=None, demandMouseFocus=True): #if no pos is specified, retrieve it using get_pos()
#     """(UI element) return the pygameDrawer that the mouse is hovering over, or the one you interacted with last"""
#     if(len(pygameDrawerInputList) > 1):
#         if(mousePos is None):
#             mousePos = pygame.mouse.get_pos()
#         global pygameDrawerInputLast
#         if(pygame.mouse.get_focused() or (not demandMouseFocus)):
#             for pygameDrawerInput in pygameDrawerInputList:
#                 # localBoundries = [[pygameDrawerInput.drawOffset[0], pygameDrawerInput.drawOffset[1]], [pygameDrawerInput.drawSize[0], pygameDrawerInput.drawSize[1]]]
#                 # if(((mousePos[0]>=localBoundries[0][0]) and (mousePos[0]<(localBoundries[0][0]+localBoundries[1][0]))) and ((mousePos[1]>=localBoundries[0][1]) and (mousePos[0]<(localBoundries[0][1]+localBoundries[1][1])))):
#                 if(pygameDrawerInput.isInsideWindowPixels(mousePos)):
#                     pygameDrawerInputLast = pygameDrawerInput
#                     return(pygameDrawerInput)
#         if(pygameDrawerInputLast is None): #if this is the first interaction
#             pygameDrawerInputLast = pygameDrawerInputList[0]
#         return(pygameDrawerInputLast)
#     else:
#         return(pygameDrawerInputList[0])

def handleWindowEvent(pygameDrawerInput: rend.pygameDrawer, eventToHandle: pygame.event.Event):
    """(UI element) handle general (pygame) window-event"""
    if(eventToHandle.type == pygame.QUIT):
        print("pygame.QUIT event")
        pygameDrawerInput.windowHandler.keepRunning = False # stop program (soon)
    
    elif(eventToHandle.type == pygame.VIDEORESIZE):
        newSize = eventToHandle.size
        if((pygameDrawerInput.windowHandler.oldWindowSize[0] != newSize[0]) or (pygameDrawerInput.windowHandler.oldWindowSize[1] != newSize[1])): #if new size is actually different
            print("VIDEORESIZE from", pygameDrawerInput.windowHandler.oldWindowSize, "to", newSize)
            correctedSize = [newSize[0], newSize[1]]
            pygameDrawerInput.windowHandler.window = pygame.display.set_mode(correctedSize, pygame.RESIZABLE)
            #for pygameDrawerInput in pygameDrawerInputList:
            localNewSize = [int((pygameDrawerInput.drawSize[0]*correctedSize[0])/pygameDrawerInput.windowHandler.oldWindowSize[0]), int((pygameDrawerInput.drawSize[1]*correctedSize[1])/pygameDrawerInput.windowHandler.oldWindowSize[1])]
            localNewDrawPos = [int((pygameDrawerInput.drawOffset[0]*correctedSize[0])/pygameDrawerInput.windowHandler.oldWindowSize[0]), int((pygameDrawerInput.drawOffset[1]*correctedSize[1])/pygameDrawerInput.windowHandler.oldWindowSize[1])]
            pygameDrawerInput.updateWindowSize(localNewSize, localNewDrawPos, autoMatchSizeScale=False)
        pygameDrawerInput.windowHandler.oldWindowSize = pygameDrawerInput.windowHandler.window.get_size() #update size (get_size() returns tuple of (width, height))
    
    elif(eventToHandle.type == pygame.WINDOWSIZECHANGED): # pygame 2.0.1 compatible    (right now (aug 2021, pygame 2.0.1 (SDL 2.0.14, Python 3.8.3)) both get called (on windows at least), but it should be fine)
        newSize = pygameDrawerInput.windowHandler.window.get_size()
        if((pygameDrawerInput.windowHandler.oldWindowSize[0] != newSize[0]) or (pygameDrawerInput.windowHandler.oldWindowSize[1] != newSize[1])): #if new size is actually different
            print("WINDOWSIZECHANGED from", pygameDrawerInput.windowHandler.oldWindowSize, "to", newSize)
            correctedSize = [newSize[0], newSize[1]]
            #for pygameDrawerInput in pygameDrawerInputList:
            localNewSize = [int((pygameDrawerInput.drawSize[0]*correctedSize[0])/pygameDrawerInput.windowHandler.oldWindowSize[0]), int((pygameDrawerInput.drawSize[1]*correctedSize[1])/pygameDrawerInput.windowHandler.oldWindowSize[1])]
            localNewDrawPos = [int((pygameDrawerInput.drawOffset[0]*correctedSize[0])/pygameDrawerInput.windowHandler.oldWindowSize[0]), int((pygameDrawerInput.drawOffset[1]*correctedSize[1])/pygameDrawerInput.windowHandler.oldWindowSize[1])]
            pygameDrawerInput.updateWindowSize(localNewSize, localNewDrawPos, autoMatchSizeScale=False)
        pygameDrawerInput.windowHandler.oldWindowSize = pygameDrawerInput.windowHandler.window.get_size() #update size (get_size() returns tuple of (width, height))
    
    elif(eventToHandle.type == pygame.DROPFILE): #drag and drop files to import them
        #pygameDrawerInput = currentpygameDrawerInput(pygameDrawerInputList, None, False)
        print("attempting to load drag-dropped file:", eventToHandle.file)
        try:
            #note: drag and drop functionality is a little iffy for multi-drawer applications
            ## TBD: file importing code here
            print("no file handler set yet, just doing nothing with the drag-dropped file!")
        except Exception as excep:
            print("failed to load drag-dropped file, exception:", excep)
    
    elif((eventToHandle.type == pygame.MOUSEBUTTONDOWN) or (eventToHandle.type == pygame.MOUSEBUTTONUP)):
        #print("mouse press", eventToHandle.type == pygame.MOUSEBUTTONDOWN, eventToHandle.button, eventToHandle.pos)
        #handleMousePress(currentpygameDrawerInput(pygameDrawerInputList, eventToHandle.pos, True), eventToHandle.type == pygame.MOUSEBUTTONDOWN, eventToHandle.button, eventToHandle.pos, eventToHandle)
        handleMousePress(pygameDrawerInput, eventToHandle.type == pygame.MOUSEBUTTONDOWN, eventToHandle.button, eventToHandle.pos, eventToHandle)
        
    elif((eventToHandle.type == pygame.KEYDOWN) or (eventToHandle.type == pygame.KEYUP)):
        #print("keypress:", eventToHandle.type == pygame.KEYDOWN, eventToHandle.key, pygame.key.name(eventToHandle.key))
        #handleKeyPress(currentpygameDrawerInput(pygameDrawerInputList, None, True), eventToHandle.type == pygame.KEYDOWN, eventToHandle.key, eventToHandle)
        handleKeyPress(pygameDrawerInput, eventToHandle.type == pygame.KEYDOWN, eventToHandle.key, eventToHandle)
    
    elif(eventToHandle.type == pygame.MOUSEWHEEL): #scroll wheel (zooming / rotating)
        #simToScale = currentpygameDrawerInput(pygameDrawerInputList, None, True)
        simToScale = pygameDrawerInput
        # if(pygame.key.get_pressed()[pygame.K_LCTRL]): #if holding (left) CTRL while scrolling
        #     ## do stuff
        # else:
        if(not simToScale.movingViewOffset):
            ## save some stuff before the change
            viewSizeBeforeChange = [simToScale.drawSize[0]/simToScale.sizeScale, simToScale.drawSize[1]/simToScale.sizeScale]
            mousePosBeforeChange = simToScale.pixelsToRealPos(pygame.mouse.get_pos())
            ## update sizeScale
            simToScale.sizeScale *= 1.0+(eventToHandle.y/10.0) #10.0 is an arbetrary zoomspeed
            if(simToScale.sizeScale < simToScale.minSizeScale):
                # print("can't zoom out any further")s
                simToScale.sizeScale = simToScale.minSizeScale
            elif(simToScale.sizeScale > simToScale.maxSizeScale):
                # print("can't zoom in any further")
                simToScale.sizeScale = simToScale.maxSizeScale
            dif = None # init var
            if(simToScale.centerZooming): ## center zooming:
                dif = [(viewSizeBeforeChange[0]-(simToScale.drawSize[0]/simToScale.sizeScale))/2, (viewSizeBeforeChange[1]-(simToScale.drawSize[1]/simToScale.sizeScale))/2]
            else: ## mouse position based zooming:
                mousePosAfterChange = simToScale.pixelsToRealPos(pygame.mouse.get_pos())
                dif = [mousePosBeforeChange[0] - mousePosAfterChange[0], mousePosBeforeChange[1] - mousePosAfterChange[1]]
            simToScale.viewOffset[0] -= dif[0] #equalizes from the zoom to 'happen' from the middle of the screen
            simToScale.viewOffset[1] -= dif[1]


def handleAllWindowEvents(pygameDrawerInput: rend.pygameDrawer):
    """(UI element) loop through (pygame) window-events and handle all of them"""
    # pygameDrawerInputList = []
    # if(type(pygameDrawerInput) is list):
    #     if(len(pygameDrawerInput) > 0):
    #         for entry in pygameDrawerInput:
    #             if(type(entry) is list):
    #                 for subEntry in entry:
    #                     pygameDrawerInputList.append(subEntry) #2D lists
    #             else:
    #                 pygameDrawerInputList.append(entry) #1D lists
    # else:
    #     pygameDrawerInputList = [pygameDrawerInput] #convert to 1-sizes array
    # #pygameDrawerInputList = pygameDrawerInput #assume input is list of pygamesims
    # if(len(pygameDrawerInputList) < 1):
    #     print("len(pygameDrawerInputList) < 1")
    #     pygameDrawerInput.windowHandler.keepRunning = False
    #     pygame.event.pump()
    #     return()
    for eventToHandle in pygame.event.get(): #handle all events
        if(eventToHandle.type != pygame.MOUSEMOTION): #skip mousemotion events early (fast)
            #handleWindowEvent(pygameDrawerInputList, eventToHandle)
            handleWindowEvent(pygameDrawerInput, eventToHandle)
        # else: # any mouse movement will trigger this code, so be careful to make it fast/efficient
        #     ## mouse movement trigger code here
