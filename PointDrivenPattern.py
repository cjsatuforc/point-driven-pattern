import adsk.core, adsk.fusion, traceback

app = None
ui  = None
     
# global event handlers
_handlers = []

# inputs changed
class CommandInputChangedHandler(adsk.core.InputChangedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            eventArgs = adsk.core.InputChangedEventArgs.cast(args)
            inputs = eventArgs.inputs
            cmdInput = eventArgs.input
        except:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


# destroy handler            
class CommandDestroyHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            adsk.terminate()
        except:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


# command create
class CommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            # get the command
            cmd = adsk.core.Command.cast(args.command)

            # link command destroyed event
            onDestroy = CommandDestroyHandler()
            cmd.destroy.add(onDestroy)
            _handlers.append(onDestroy)

            # link to input changed event          
            onInputChanged = CommandInputChangedHandler()
            cmd.inputChanged.add(onInputChanged)
            _handlers.append(onInputChanged)    

            # get command inputs collection
            inputs = cmd.commandInputs
            
            # create an origin selection input.
            sourceOrigin = inputs.addSelectionInput('originSelection', 'Instance Origin', 'Origin select command input')
            sourceOrigin.setSelectionLimits(1)
            sourceOrigin.addSelectionFilter('Vertices')
            
            # create a source selection input.
            sourceObject = inputs.addSelectionInput('sourceSelection', 'Source Body', 'Source select command input')
            sourceObject.setSelectionLimits(1)
            sourceObject.addSelectionFilter('Bodies')
            
            # create a target selection input.
            targetSketch = inputs.addSelectionInput('targetSelection', 'Target Points (Sketch)', 'Target select command input')
            targetSketch.setSelectionLimits(1)
            targetSketch.addSelectionFilter('Sketches')
            
            #connect to execute
            onExecute = CommandExecuteHandler()
            cmd.execute.add(onExecute)
            _handlers.append(onExecute)            
            
        except:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


# execute event
class CommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        eventArgs = adsk.core.CommandEventArgs.cast(args)
 
        #get the active product and active design
        product = app.activeProduct
        design = adsk.fusion.Design.cast(product)
        rootComp = design.activeComponent
        
        #get features collection of doc
        features = rootComp.features
        
        #get the inputs from command created handler
        inputs = eventArgs.command.commandInputs
        
        originSelection = inputs.itemById('originSelection')  
        sourceSelection = inputs.itemById('sourceSelection')        
        targetSelection = inputs.itemById('targetSelection')

        #get the selected origin
        originPoint = adsk.fusion.BRepVertex.cast(originSelection.selection(0).entity)        
        
        #extract source bodies
        sourceBodies = adsk.core.ObjectCollection.create()
        sourceBodies.add(adsk.fusion.BRepBody.cast(sourceSelection.selection(0).entity))        
        
        #make a target sketch from target selection and extract sketchpoints
        targetSketch = adsk.fusion.Sketch.cast(targetSelection.selection(0).entity)
        targetPoints = targetSketch.sketchPoints

        #this matrix will move around and paste source bodies
        moveMatrix = adsk.core.ObjectCollection.create()
        
        for index, i in enumerate (targetPoints[1:]):
            
            #establish instance origin coordinates        
            originPos = originPoint.geometry
            originCoord = originPos.getData()
            
            #get the coordinates of sketch point
            pointPos = i.worldGeometry
            pointCoord = pointPos.getData()
            
            #construct translation vector components
            tVecX = pointCoord[1]-originCoord[1]
            tVecY = pointCoord[2]-originCoord[2]
            tVecZ = pointCoord[3]-originCoord[3]

            #create a transform vector
            vector = adsk.core.Vector3D.create(tVecX,tVecY,tVecZ)
            transform = adsk.core.Matrix3D.create()
            transform.translation = vector

            # paste a body in place
            features.copyPasteBodies.add(sourceBodies)
            
            #put source body in collection to move            
            moveMatrix.add(sourceBodies)
            
            #Create a move feature        
            moveFeats = features.moveFeatures
            moveFeatureInput = moveFeats.createInput(moveMatrix.item(index), transform)
            moveFeats.add(moveFeatureInput)
            
            
def run(context):
    try:
        global app, ui
        app = adsk.core.Application.get()
        ui = app.userInterface

        # get the command definition or make one if there is none
        cmdDef = ui.commandDefinitions.itemById('pointDrivenPattern')
        if not cmdDef:
            cmdDef = ui.commandDefinitions.addButtonDefinition('pointDrivenPattern', 'Point Driven Pattern', 'Drive a pattern using all points in a Sketch.')
            
        # connect to command created event
        onCommandCreated = CommandCreatedHandler()
        cmdDef.commandCreated.add(onCommandCreated)
        _handlers.append(onCommandCreated)

        # run the command definition
        cmdDef.execute()
        
        #Prevent this module from being terminated when the script returns, because we are waiting for event handlers to fire.
        adsk.autoTerminate(False)
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
            
            
