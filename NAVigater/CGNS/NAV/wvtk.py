#  -------------------------------------------------------------------------
#  pyCGNS.NAV - Python package for CFD General Notation System - NAVigater
#  See license.txt file in the root directory of this Python module source  
#  -------------------------------------------------------------------------
#  $Release$
#  -------------------------------------------------------------------------
from PySide.QtCore    import *
from PySide.QtGui     import *
from CGNS.NAV.Q7VTKWindow import Ui_Q7VTKWindow
from CGNS.NAV.wfingerprint import Q7Window
from CGNS.NAV.mparser import Mesh
from CGNS.NAV.defaults import G__COLORS
import numpy as NPY

import random
import vtk

# ----------------------------------------------------------------------------

class wVTKContext():
    def __init__(self,cm):
      (self.vx,self.vy,self.vz)=cm.GetViewUp()
      (self.cx,self.cy,self.cz)=cm.GetFocalPoint()
      (self.px,self.py,self.pz)=cm.GetPosition()
      (self.sx,self.sy,self.sz)=(0.,0.,0.)
      (self.ox,self.oy,self.oz)=(0.,0.,0.)
    def setViewUp(self,vx,vy,vz):
      (self.vx,self.vy,self.vz)=(vx,vy,vz)
    def setFocalPoint(self,cx,cy,cz):
      (self.cx,self.cy,self.cz)=(cx,cy,cz)
    def setPosition(self,px,py,pz):
      (self.px,self.py,self.pz)=(px,py,pz)
    def dump(self):
      return """
(self.vx,self.vy,self.vz)=%s
(self.cx,self.cy,self.cz)=%s
(self.px,self.py,self.pz)=%s
(self.sx,self.sy,self.sz)=%s
(self.ox,self.oy,self.oz)=%s"""%(\
        (self.vx,self.vy,self.vz),
        (self.cx,self.cy,self.cz),
        (self.px,self.py,self.pz),
        (self.sx,self.sy,self.sz),
        (self.ox,self.oy,self.oz))

# -----------------------------------------------------------------
class Q7VTK(Q7Window,Ui_Q7VTKWindow):
  def __init__(self,control,node,fgprint):
      Q7Window.__init__(self,Q7Window.VIEW_VTK,control,node,fgprint)
      self._xmin=self._ymin=self._zmin=self._xmax=self._ymax=self._zmax=0.0
      self._vtktree=self.wCGNSTree(self._fgprint.tree)
      self._T=self._fgprint.tree
      self._selected=[]
      self._currentactor=None
      self._blackonwhite=False
      self.display.Initialize()
      self.display.Start()
      self.display.show()
      self.bX.clicked.connect(self.b_xaxis)
      self.bY.clicked.connect(self.b_yaxis)
      self.bZ.clicked.connect(self.b_zaxis)
      self.bSuffleColors.clicked.connect(self.b_shufflecolors)
      self.bBlackColor.clicked.connect(self.b_blackandwhite)
      self.bAddView.clicked.connect(self.b_saveview)
      self.bNext.clicked.connect(self.b_next)
 
  def SyncCameras(self,ren,event):
    cam = ren.GetActiveCamera()
    self.camAxes.SetViewUp(cam.GetViewUp())
    self.camAxes.OrthogonalizeViewUp()
    x, y, z = cam.GetDirectionOfProjection()

    bnds = self.renAxes.ComputeVisiblePropBounds()
    x0, x1, y0, y1, z0, z1 = self.renAxes.ComputeVisiblePropBounds()
    self.renAxes.ResetCamera(x0, x1, y0, y1, z0, z1) 
    pos = self.camAxes.GetPosition()
    px, py, pz = self.camAxes.GetPosition()
    d = NPY.sqrt(px*px + py*py + pz*pz)
    dproj = NPY.sqrt(x*x + y*y + z*z)

    self.camAxes.SetFocalPoint(0,0,0)
    self.camAxes.SetPosition(-d*x/dproj, -d*y/dproj, -d*z/dproj)
    self.renAxes.ResetCameraClippingRange()

  def findObjectPath(self,selected):
    return self._parser.getPathFromObject(selected)
    
  def leave(self):
    self._wtop.destroy()
    self._control._hasvtkWindow=None
  
  def onexit(self):  
    self._control._control.delTreeView(self._viewid,
                                       self._fgprint.filedir,
                                       self._fgprint.filename)
    self.leave()

  def annotatePick(self, object, event):
    self._selected=[]
    if self.picker.GetCellId() < 0:
        self.textActor.VisibilityOff()
        self._selected=[]
    else:        
        selPt = self.picker.GetSelectionPoint()
        pickAct = self.picker.GetActors()
        a=pickAct.InitTraversal()
        a=pickAct.GetNextItem()
        t=''
        sl=[]
        while a:
          x=a.GetMapper().GetInput()
          s=self.findObjectPath(x)
          t+=s+'\n'
          self._selected+=[[s,a]]
          self.textMapper.SetInput(t)
          yd=self._vtk.GetRenderWindow().GetSize()[1]-self.textMapper.GetHeight(self._vtkren)-10.
          self.textActor.SetPosition((10.,yd))
          self.textActor.VisibilityOn()
          self._vtkren.AddActor(self.textActor)
          a=pickAct.GetNextItem()
          self.setCurrentPath(s)
                             
  def addPicker(self):
    self.textMapper = vtk.vtkTextMapper()
    tprop = self.textMapper.GetTextProperty()  
    tprop.SetFontFamilyToArial()
    tprop.SetFontSize(10)
    tprop.BoldOff()
    tprop.ShadowOn()
    tprop.SetColor(0, 0, 0)
    self.textActor = vtk.vtkActor2D()
    self.textActor.VisibilityOff()
    self.textActor.SetMapper(self.textMapper)
    self.picker = vtk.vtkCellPicker()
    self.picker.SetTolerance(0.001)
    self.picker.AddObserver("EndPickEvent", self.annotatePick)
    
  def addAxis(self):
    self.camAxes = vtk.vtkCamera()
    self.camAxes.ParallelProjectionOn()

    self.renAxes = vtk.vtkRenderer()
    self.renAxes.InteractiveOff()
    self.renAxes.SetActiveCamera(self.camAxes)
    self.renAxes.SetViewport(0, 0, 0.2, 0.2)
    self.renAxes.SetBackground(1,1,1)

    xAxis = vtk.vtkArrowSource()
    xAxisMapper = vtk.vtkPolyDataMapper()
    xAxisMapper.SetInput(xAxis.GetOutput())
    xAxisActor = vtk.vtkActor()
    xAxisActor.SetMapper(xAxisMapper)
    xAxisActor.GetProperty().SetColor(1,0,0)

    yAxis = vtk.vtkArrowSource()
    yAxisMapper = vtk.vtkPolyDataMapper()
    yAxisMapper.SetInput(yAxis.GetOutput())
    yAxisActor = vtk.vtkActor()
    yAxisActor.SetMapper(yAxisMapper)
    yAxisActor.GetProperty().SetColor(1,1,0)
    yAxisActor.RotateZ(90)

    zAxis = vtk.vtkArrowSource()
    zAxisMapper = vtk.vtkPolyDataMapper()
    zAxisMapper.SetInput(zAxis.GetOutput())
    zAxisActor = vtk.vtkActor()
    zAxisActor.SetMapper(zAxisMapper)
    zAxisActor.GetProperty().SetColor(0,1,0)
    zAxisActor.RotateY(-90)

    xLabel = vtk.vtkCaptionActor2D()
    xLabel.SetCaption("X")
    xprop=vtk.vtkTextProperty()
    xprop.SetFontSize(3)
    xLabel.SetCaptionTextProperty(xprop)
    xLabel.SetAttachmentPoint(0.75,0.2,0)
    xLabel.LeaderOff()
    xLabel.BorderOff()
    xLabel.GetProperty().SetColor(0,0,0)
    xLabel.SetPosition(0,0)

    yLabel = vtk.vtkCaptionActor2D()
    yLabel.SetCaption("Y")
    yprop=vtk.vtkTextProperty()
    yprop.SetFontSize(3)
    yLabel.SetCaptionTextProperty(yprop)
    yLabel.SetAttachmentPoint(0.2,0.75,0)
    yLabel.LeaderOff()
    yLabel.BorderOff()
    yLabel.GetProperty().SetColor(0,0,0)
    yLabel.SetPosition(0,0)

    zLabel = vtk.vtkCaptionActor2D()
    zLabel.SetCaption("Z")
    zprop=vtk.vtkTextProperty()
    zprop.SetFontSize(3)
    zLabel.SetCaptionTextProperty(zprop)
    zLabel.SetAttachmentPoint(0,0.2,0.75)
    zLabel.LeaderOff()
    zLabel.BorderOff()
    zLabel.GetProperty().SetColor(0,0,0)
    zLabel.SetPosition(0,0)

    Axes3D = vtk.vtkPropAssembly()
    Axes3D.AddPart(xAxisActor)
    Axes3D.AddPart(yAxisActor)
    Axes3D.AddPart(zAxisActor)
    Axes3D.AddPart(xLabel)
    Axes3D.AddPart(yLabel)
    Axes3D.AddPart(zLabel)

    self.renAxes.AddActor(Axes3D)
    
    return self.renAxes

  def wCGNSTree(self,T):

      o=vtk.vtkObject()
      o.SetGlobalWarningDisplay(0)
      del o
      
      self._vtk=self.display
      self._vtkren = vtk.vtkRenderer()
      self._targetren=vtk.vtkRenderer()
      
      self._waxs=self.addAxis()
      wpck = self.addPicker()

      self._vtk.GetRenderWindow().SetNumberOfLayers(2)
      self._vtkren.SetLayer(0)
      self._waxs.SetLayer(1)

      self._vtk.GetRenderWindow().AddRenderer(self._vtkren)
      self._vtk.GetRenderWindow().AddRenderer(self._waxs)
    
      self._parser=Mesh(T)
      alist=self._parser.createActors()
      self.fillCurrentPath()
 
      if (alist!=[]):
          for a in alist:
              self._vtkren.AddActor(a[0])

              if (a[1] is not None):
                  if (self._xmin>a[1][0]):self._xmin=a[1][0]
                  if (self._ymin>a[1][2]):self._ymin=a[1][2]
                  if (self._zmin>a[1][4]):self._zmin=a[1][4]
                  if (self._xmax<a[1][1]):self._xmax=a[1][1]
                  if (self._ymax>a[1][3]):self._ymax=a[1][3]
                  if (self._zmax>a[1][5]):self._zmax=a[1][5]
               
      self._vtkren.SetBackground(1,1,1)  
      self._vtkren.ResetCamera()
      self._vtkren.GetActiveCamera().Elevation(0.0)
      self._vtkren.GetActiveCamera().Azimuth(90.0)
      self._vtkren.GetActiveCamera().Zoom(1.0)
      self._vtkren.GetActiveCamera().OrthogonalizeViewUp()
                  
      (self.vx,self.vy,self.vz)=self._vtkren.GetActiveCamera().GetViewUp()
      (self.cx,self.cy,self.cz)=self._vtkren.GetActiveCamera().GetFocalPoint()
      (self.px,self.py,self.pz)=self._vtkren.GetActiveCamera().GetPosition()
      (self.sx,self.sy,self.sz)=(0.,0.,0.)
      (self.ox,self.oy,self.oz)=(0.,0.,0.)

      self._ctxt=wVTKContext(self._vtkren.GetActiveCamera())
      self._ctxt.setViewUp(self.vx,self.vy,self.vz)
      self._ctxt.setFocalPoint(self.cx,self.cy,self.cz)
      self._ctxt.setPosition(self.px,self.py,self.pz)
                
      istyle = vtk.vtkInteractorStyleTrackballCamera()
      self._vtk.SetInteractorStyle(istyle)
      
      self._vtk.AddObserver("KeyPressEvent", self.CharCallback)
      self._vtk.SetPicker(self.picker)

      self.iren=self._vtk.GetRenderWindow().GetInteractor()
      self.iren.AddObserver("KeyPressEvent", self.CharCallback)
      self.iren.SetPicker(self.picker)

      self._vtkren.AddObserver("StartEvent", self.SyncCameras)
        
      
      self._bindings={ 'r' :self.b_refresh,
                       'c'     :self.b_shufflecolors,
                       'T'     :self.b_nexttarget,
                       'x'     :self.b_xaxis,
                       'y'     :self.b_yaxis,
                       'z'     :self.b_zaxis,
                       's'     :self.b_surf,
                       'w'     :self.b_wire }

      self._p_wire=True
      self.setColors(True)

      return self._vtk.GetRenderWindow()

  def b_shufflecolors(self,pos=None):
      self.setColors(True)
      
  def b_blackandwhite(self,pos=None):
      self.setColors()
      
  def getRandomColor(self):
      cl=G__COLORS[G__COLORS.keys()[random.randrange(len(G__COLORS.keys()))]]
      return cl
      
  def setColors(self,randcolors=False):
      if (not randcolors):
          if (self._blackonwhite):
              self._vtkren.SetBackground(1,1,1)
              cl=(0,0,0)
          else:
              self._vtkren.SetBackground(0,0,0)
              cl=(1,1,1)
          self._blackonwhite=not self._blackonwhite
      actors = self._vtkren.GetActors()
      actors.InitTraversal()
      actor = actors.GetNextItem()
      while actor:
          if (randcolors): cl=self.getRandomColor()
          actor.GetProperty().SetColor(cl)
          actor = actors.GetNextItem()
      self.iren.GetRenderWindow().Render()

  def b_next(self):
      self.b_nexttarget(None)
      
  def b_nexttarget(self,pos):
      if (self._currentactor !=None):
          color=self._currentactor[2]
          actor=self._currentactor[1]
          actor.GetProperty().SetColor(color)
          self._vtk.GetRenderWindow().GetRenderers().GetFirstRenderer().RemoveActor(actor)
          self._vtkren.AddActor(actor)
          self._vtk.GetRenderWindow().Render()

      if (len(self._selected)>0):        
          self._selected=self._selected[1:]+[self._selected[0]]
          self._currentactor=self._selected[0]
          actor=self._currentactor[1]
          color=actor.GetProperty().GetColor()
          self._currentactor.append(color)
          actor.GetProperty().SetColor(1,0,0)
          self._vtkren.RemoveActor(actor)
          self._vtk.GetRenderWindow().GetRenderers().GetFirstRenderer().AddActor(actor)
          self._vtk.GetRenderWindow().Render()                
      
  def b_saveview(self):
      camera = self._vtkren.GetActiveCamera()
      vname=self.cViews.currentText()
      print 'Save view ',vname
      print camera.GetViewUp()
      print camera.GetDirectionOfProjection()
      print camera.GetPosition()
      self.cViews.addItem(vname)
      #camera.OrthogonalizeViewUp()

  def b_refresh(self,pos):
      self._vtk.GetRenderWindow().Render()
      
  def b_xaxis(self,pos=None):
      if (self.cMirror.isChecked()): self.setAxis(pos,-1)
      else: self.setAxis(pos,1)
    
  def b_yaxis(self,pos=None):
      if (self.cMirror.isChecked()): self.setAxis(pos,-2)
      else: self.setAxis(pos,2)
   
  def b_zaxis(self,pos=None):
      if (self.cMirror.isChecked()): self.setAxis(pos,-3)
      else: self.setAxis(pos,3)
    
  def setCurrentPath(self,path):
      ix=self.cCurrentPath.findText(path)
      if (ix!=-1): self.cCurrentPath.setCurrentIndex(ix)

  def fillCurrentPath(self):
      self.cCurrentPath.clear()
      for i in self._parser.getPathList():
          self.cCurrentPath.addItem(i)
          
  def setAxis(self,pos,iaxis):
      fit=self.cFit.isChecked()
      rat=50
      cx = (0.5*(self._xmax-self._xmin))
      cy = (0.5*(self._ymax-self._ymin))
      cz = (0.5*(self._zmax-self._zmin))
      if iaxis == 1:
          (vx,vy,vz)=(0.,0.,1.)
          (px,py,pz)=(rat*cx,cy,cz)
      elif iaxis == 2:
          (vx,vy,vz)=(0.5,0.,0.)
          (px,py,pz)=(cx,rat*cy,cz)
      elif iaxis == 3:
          (vx,vy,vz)=(0.,1.,0.)
          (px,py,pz)=(cx,cy,rat*cz)
      elif iaxis == -1:
          (vx,vy,vz)=(0.,0.,-1.)
          (px,py,pz)=(rat*cx,cy,cz)
      elif iaxis == -2:
          (vx,vy,vz)=(-0.5,0.,0.)
          (px,py,pz)=(cx,rat*cy,cz)
      elif iaxis == -3:
          (vx,vy,vz)=(0.,-1.,0.)
          (px,py,pz)=(cx,cy,rat*cz)

      camera = self._vtkren.GetActiveCamera()
      camera.SetViewUp(vx, vy, vz)
      camera.SetFocalPoint(cx, cy, cz)
      camera.SetPosition(px, py, pz)
      camera.OrthogonalizeViewUp()
      self._vtkren.ResetCameraClippingRange()
      self._vtkren.Render()
      self._waxs.Render()
      self._vtkren.ResetCamera()
      self.iren.Render()
      
      self._ctxt=wVTKContext(camera)
      self._ctxt.setViewUp(vx,vy,vz)
      self._ctxt.setFocalPoint(cx,cy,cz)
      self._ctxt.setPosition(px,py,pz)

  def b_surf(self,pos):
      if (not self._p_wire):
          self.b_wire(pos)
          return
      self._p_wire=False
      actors = self._vtkren.GetActors()
      actors.InitTraversal()
      actor = actors.GetNextItem()
      while actor:
          actor.GetProperty().SetRepresentationToSurface()
          actor = actors.GetNextItem()
      self._vtk.GetRenderWindow().Render()
      
  def b_wire(self,pos):  
      if (self._p_wire):
          self.b_surf(pos)
          return
      self._p_wire=True
      actors = self._vtkren.GetActors() 
      actors.InitTraversal()
      actor = actors.GetNextItem()
      while actor:
          actor.GetProperty().SetRepresentationToWireframe()
          actor = actors.GetNextItem()
      self._vtk.GetRenderWindow().Render() 
      
  def CharCallback(self,obj,event):
      keysym  = self.iren.GetKeySym()
      pos = self.iren.GetEventPosition()
      if (self._bindings.has_key(keysym)): self._bindings[keysym](pos)
      return
  
  def closeEvent(self, event):
      self._control.close()

  def close(self):
      self._vtk.GetRenderWindow().Finalize()
      QWidget.close(self)
      
# -----------------------------------------------------------------------------
        
