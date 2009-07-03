# -----------------------------------------------------------------------------
# pyS7 - CGNS/SIDS editor
# ONERA/DSNA - marc.poinot@onera.fr
# pyS7 - $Rev: 70 $ $Date: 2009-01-30 11:49:10 +0100 (Fri, 30 Jan 2009) $
# -----------------------------------------------------------------------------
# See file COPYING in the root directory of this Python module source
# tree for license information.

import Tkinter
Tkinter.wantobjects=0 #necessary for tk-8.5 and some buggy tkinter installs
from Tkinter import *
from TkTreectrl import *
import os
import sys
import numpy as Num
#import threading
import time

from S7.version import __vid__

import s7globals
G___=s7globals.s7G

import s7treeFingerPrint
import S7.supervisor.s7parser as s7parser
import s7treeSimple
import s7tableSimple
import s7patternBrowser
import s7operateView
import s7utils
import s7fileDialog
import s7optionView
import s7windoz
import s7linkView
import s7history
    
# threads not implemented yet...

# -----------------------------------------------------------------------------
class wTopControl(s7windoz.wWindoz,ScrolledMultiListbox): #,threading.Thread):
  def lock_acquire(self,msg=''):
#    print 's7 ACQ',msg
#    self.lock.acquire()
    pass
  def lock_release(self,msg=''):
#    print 's7 REL'  ,msg  
#    self.lock.release()
    pass
  def cbk_newtree(self):
    self.newTree()
  def cbk_loadtree(self):
    self.loadFile()
  def cbk_options(self):
    s7optionView.wOptionView(self)
  def cbk_help(self):
    import os
    os.system(G___.firedox)
  def cbk_pattern(self): 
    self.patternView()
  def cbk_operate(self):
    r=[]
    self.operateView(None,r)
  def __init__(self,wparent):
#    threading.Thread.__init__(self)
#    self.lock = threading.Lock()

    s7windoz.wWindoz.__init__(self,None,'pyS7: Control panel [v%s]'%__vid__)
    self.wparent = wparent

    self.patternWindow=None
    self.operateWindow=None
    self.logWindow=None
    self.linkWindow=None
    self.newcount=1

    ScrolledMultiListbox.__init__(self,self._wtop,relief=GROOVE,border=3,
                                  height=G___.wminheight,width=G___.wminwidth)
    mcols=self.menu([('tree-new',W,2,self.cbk_newtree, 'New tree'),
                     ('tree-load',W,20,self.cbk_loadtree,'Load tree from file'),
                     ('pattern',W,2,self.cbk_pattern,'Pattern window'),
                     ('options-view',W,20,self.cbk_options,'Options window'),
                     ('help-view',W,2,self.cbk_help,'Help in browser')])
    self.coldim=6
    self.listbox.config(columns=('S','T','View','File','Dir','Node'),
                        selectbackground=G___.color_Ca,
                        selectforeground=G___.color_Cb,
                        selectmode=SINGLE,font=self.listfont)
    colors = ('white',)
    self.listbox.sort_allowed=[2,3,4,5]
    self.listbox.sort_init=0
    self.listbox.column_configure(self.listbox.column(0),font=self.titlefont,
                                  borderwidth=1,itembackground=colors,width=20)
    self.listbox.column_configure(self.listbox.column(1),font=self.titlefont,
                                  borderwidth=1,itembackground=colors,width=20)
    for ct in self.listbox.sort_allowed:
      self.listbox.column_configure(self.listbox.column(ct),
                                    font=self.titlefont,borderwidth=1,
                                    itembackground=colors,
                                    arrow='down',arrowgravity='right')
    self.listbox.notify_install('<Header-invoke>')
    self.listbox.notify_bind('<Header-invoke>',s7utils.operate_sort_list)
    self.listbox.bind('<Return>',self.do_focus)
    self.listbox.bind('<Delete>',self.closeView)
    self.grid(row=1,sticky=N+E+S+W)
    t=self.winfo_toplevel() 
    t.rowconfigure(1,weight=1,minsize=0,uniform=2)
    t.columnconfigure(0,weight=1,minsize=20)
   

  # --------------------------------------------------------------------
  def s7_recursive_open(self):
    if (G___.expandRecurse): G___.expandRecurse=0
    else:                    G___.expandRecurse=G___.maxRecurse
    
  def s7_show_index(self):
    G___.showIndex=not G___.showIndex
    
  def s7_sids_recurse(self):
    G___.sidsRecurse=not G___.sidsRecurse
    
  def s7_show_title(self):
    G___.showColumnTitle=not G___.showColumnTitle
    
  def s7_one_view_per_node(self):
    G___.singleView=not G___.singleView

  def s7_check_on_the_fly(self):
    G___.flyCheck=not G___.flyCheck

  def s7_pattern_base(self):
    if (self.patternWindow): self.patternClose()
    else:                    self.patternView()
    
  # --------------------------------------------------------------------
  def unmodified(self,tf):
    tf.unmodified()
    self.updatecontrolline(tf)
  def modified(self,tf):
    tf.modified()
    self.updatecontrolline(tf)

  def updatecontrolline(self,tf):
    for wtn in range(self.listbox.size()-1,-1,-1):
      wt=self.listbox.get(wtn)
      (ts,vt,nv,cfn,cfd,nd)=wt[0]
      if (    (tf.filedir==cfd)
          and (tf.filename==cfn)):
        clf=self.listbox.column(0)
        elt=self.listbox.element('text')
        it=self.listbox.item(wtn)
        self.listbox.itemelement_configure(it,clf,elt,text=tf.state)
    
  def do_focus(self,e):
    t=e.widget.get(e.widget.nearest(e.y))
    if (t):
      (ts,vt,nv,fn,fd,nd)=t[0]
      w=self.getTreeView(int(nv),fd,fn)
      if (w != None):
        g=w.view._wtop.geometry()
        w.view._wtop.withdraw()
        w.view._wtop.deiconify()
        w.view._wtop.geometry(g)
#        self.listbox.focus_force()

  def newTree(self):
    treeroot=['CGNSTree',None,[],'CGNSTree_t']
    tag="CGNS-%.3d"%self.newcount
    self.newcount+=1
    tree=s7treeFingerPrint.wTreeFingerPrint('.',tag,treeroot)
    self.lock_acquire('newTree')
    G___.treeStorage.append(tree)
    self.lock_release('newTree')
    createDataTreeWindow(self,tree,G___.expandRecurse)
        
  def saveContext(self):
    s7history.saveHistory()

  def saveAsPattern(self,tree,treefingerprint,file=None):
    s7patternBrowser.wPatternEdit(self,tree,treefingerprint)

  def saveFile(self,tree,treefingerprint,file=None,msg=1):
    if (file and os.path.exists(file)):
       if (not s7utils.overwriteCheck()): return
       bakfile=file+'.bak'
       os.rename(file,bakfile)
    if (not file): file=s7fileDialog.s7filedialog(self.wparent,save=1)
    if (not file): return
    if (file):
      (filename,fileext)=os.path.splitext(os.path.basename(file))
      if (fileext in G___.cgnspyFiles):
        f=open(file,'w+')
        f.write(s7utils.asFileString(tree))
        f.close()
      elif (fileext in G___.cgnsbinFiles):
        import CGNS
        tlinks=[]
        lfile="%s/%s%s"%(treefingerprint.filedir,
                       treefingerprint.filename,
                       treefingerprint.fileext)
        for lk in treefingerprint.links:
          if (lfile==lk[0]):
            tlinks.append(lk)
        if (not G___.saveLinks): tlinks=[]
        CGNS.saveAsADF(file,tree,tlinks)
      else:
        s7utils.fileWarning(fileext)
        return 0
      treefingerprint.fileext=fileext
      if ((treefingerprint.nosave)
          or ((treefingerprint.filename[:4]=='NEW-')
           and (treefingerprint.filedir=='.'))):
        tfn=filename
        tfd=os.path.dirname(file)
        for wtn in range(self.listbox.size()-1,-1,-1):
          wt=self.listbox.get(wtn)
          (ts,vt,nv,cfn,cfd,nd)=wt[0]
          if (    (treefingerprint.filedir==cfd)
              and (treefingerprint.filename==cfn)):
            clf=self.listbox.column(3)
            cld=self.listbox.column(4)
            elt=self.listbox.element('text')
            it=self.listbox.item(wtn)
            self.listbox.itemelement_configure(it,clf,elt,text=tfn)
            self.listbox.itemelement_configure(it,cld,elt,text=tfd)
        treefingerprint.filename=tfn
        treefingerprint.filedir=tfd
      if (msg): s7utils.saveFileWarning(file)
      return 1
    return 0
    
  def loadFile(self,file=None):
    if (not file):
      file=s7fileDialog.s7filedialog(self.wparent)
    self.top('loadFile start')
    self.lockMouse()
    if (file):
      (filename,fileext)=os.path.splitext(os.path.basename(file))
      filedir=os.path.dirname(file)
      if (not filedir): filedir='.'
      if   (fileext in G___.cgnspyFiles):
        tree=self.importFile(filedir,filename)
      elif (fileext in G___.cgnsbinFiles):
        tree=self.readFile(filedir,filename,fileext)
      else:
        s7utils.fileWarning(fileext)
        return
      if (tree and tree.status):
        self.top('readFile end')
        createDataTreeWindow(self,tree,G___.expandRecurse)
    self.unlockMouse()
    self.top('loadFile end')

  def readFile(self,fd,fn,fileext):
    filename='%s/%s%s'%(fd,fn,fileext)
    treefingerprint=self.getIfAlreadyImported(fd,fn)
    if (treefingerprint and s7utils.updateTreeLoad()):
      self.closeTree(fd,fn)
      treefingerprint=None
    if (s7utils.getFileSize(filename) > G___.minFileSizeNoWarning):
       if (not s7utils.bigFileWarning(G___.noData)): return None
       s7utils.forceNoRecursionWarning()
       G___.expandRecurse=0
    try:
      if (not treefingerprint and (fileext in G___.cgnslibFiles)):
        import CGNS
        lk=CGNS.getLinksAsADF(filename)
        if (G___.noData): vmax=G___.maxDisplaySize
        else:             vmax=sys.maxint
        tt=CGNS.loadAsADF(filename,G___.followLinks,vmax)
        treefingerprint=s7treeFingerPrint.wTreeFingerPrint(fd,fn,tt)
        if (not treefingerprint.status):
          s7utils.badFileError(filename)
        else:
          treefingerprint.links=lk
          if (G___.noData): treefingerprint.nosave=1
          self.lock_acquire('readFile')
          G___.treeStorage.append(treefingerprint)
          self.lock_release('readFile')
        if (treefingerprint): treefingerprint.fileext=fileext
        return treefingerprint
    except ImportError:
      s7utils.importCGNSWarning(fileext)

  def importFile(self,fd,fn):
    import imp
    treefingerprint=self.getIfAlreadyImported(fd,fn)
    if (treefingerprint and s7utils.updateTreeLoad()):
      self.closeTree(fd,fn)
      treefingerprint=None
    if (not treefingerprint):
      sprev=sys.path
      sys.path.append(fd)
      try:
        m=imp.find_module(fn)
        if (s7utils.getFileSize(m[1]) > G___.minFileSizeNoWarning):
           if (not s7utils.bigFileWarning(G___.noData)): return None
        t=imp.load_module(fn,m[0],m[1],m[2]).data
        sys.path=sprev
        treefingerprint=s7treeFingerPrint.wTreeFingerPrint(fd,fn,t)
        treefingerprint.fileext='.py'
        self.lock_acquire('importFile')
        G___.treeStorage.append(treefingerprint)
        self.lock_release('importFile')
      except (ImportError, AttributeError, SyntaxError):
        sys.path=sprev
        treefingerprint=s7treeFingerPrint.wTreeFingerPrint(fd,fn,None)
        treefingerprint.fileext='.py'        
        s7utils.badFileError('%s/%s.py'%(fd,fn))
    return treefingerprint

  def getIfAlreadyImported(self,filedir,filename):
    self.lock_acquire('getIfAlreadyImported')
    for t in G___.treeStorage:
      if ((t.filedir==filedir) and (t.filename==filename)):
        self.lock_release('getIfAlreadyImported')
        return t
    self.lock_release('getIfAlreadyImported')
    return None

  def patternView(self):
    if (self.patternWindow): return
    self.patternWindow=s7patternBrowser.wPatternBrowser(self)
    self.grid()

  def patternViewClose(self):
    if (not self.patternWindow): return
    self.patternWindow._wtop.destroy()
    self.patternWindow=None

  def operateView(self,treesimple,selectedlist):
    if (not selectedlist): return
    if (self.operateWindow):
      s7utils.operateWarning()
      return
    self.operateWindow=s7operateView.wOperateView(self,treesimple,selectedlist)
    self.grid()

  def operateViewClose(self):
    self.operateWindow._wtop.destroy()
    self.operateWindow=None

  def queryViewClose(self):
    self.queryWindow._wtop.destroy()
    self.queryWindow=None

  def logViewClose(self):
     self.logWindow._wtop.withdraw()
#    self.logWindow._wtop.destroy()
#    self.logWindow=None

  def dupView(self,event):
    try:
      id=self.listbox.curselection()[0]
    except IndexError: return
    wt=self.listbox.get(id)
    (ts,vt,nv,fn,fd,nd)=wt[0]
    self.lock_acquire('dupView')
    for t in G___.treeStorage:
      if ((t.filedir==fd) and (t.filename==fn)):
       self.lock_release('dupView')
       createDataTreeWindow(self,t,G___.expandRecurse)
       return
    self.lock_release('dupView')

  def closeView(self,event):
    self.lock_acquire('closeView')
    try:
      id=self.listbox.curselection()[0]
    except IndexError: return
    wt=self.listbox.get(id)
    (ts,vt,nv,fn,fd,nd)=wt[0]
    t=self.getTree(fd,fn)
    if (t.isModified() and (not s7utils.saveCheck())):
      self.lock_release('closeView')
      return
    self.delTreeView(int(nv),fd,fn)
    self.lock_release('closeView')

  def closeAllViews(self,event):
    try:
      id=self.listbox.curselection()[0]
    except IndexError: return
    wt=self.listbox.get(id)
    (ts,vt,nv,fn,fd,nd)=wt[0]
    self.closeTree(fd,fn)

  def closeTree(self,fd,fn):
    self.lock_acquire('closeTree')
    t=self.getTree(fd,fn)
    if (t.isModified() and (not s7utils.saveCheck())):
      self.lock_release('closeTree')
      return
    for vw in t.viewlist:
      vw.view.closeWindow()
    for wtn in range(self.listbox.size()-1,-1,-1):
      wt=self.listbox.get(wtn)
      (ts,vt,nv,cfn,cfd,nd)=wt[0]
      if ((fd==cfd) and (cfn==fn)):
        self.listbox.delete(wtn)
    G___.treeStorage.remove(t)
    self.lock_release('closeTree')

  def closeAllTrees(self):
    if (s7utils.leaveCheck()): self.closeAll()

  def delTreeView(self,nv,fd,fn):
    self.lock_acquire('delTreeView')
    ix=self.getTreeViewIndex(nv,fd,fn)
    if (ix==-1):
      self.lock_release('delTreeView')
      return None
    for t in G___.treeStorage:
      if ((t.filedir==fd) and (t.filename==fn)):
        for v in t.viewlist:
          if (v.id==nv):
            vw=self.getTreeView(int(nv),fd,fn)
            if (vw): vw.view.closeWindow()
            t.viewlist.remove(v)
            self.listbox.delete(ix)
            break
        if (not t.viewlist): G___.treeStorage.remove(t)
    self.lock_release('delTreeView')
    return None

  def getTreeView(self,nv,fd,fn):
    self.lock_acquire('getTreeView')
    for t in G___.treeStorage:
      if ((t.filedir==fd) and (t.filename==fn)):
        for v in t.viewlist:
          if (v.id==nv):
            self.lock_release('getTreeView')
            return v
    self.lock_release('getTreeView')
    return None

  def getTreeViewIndex(self,nv,fd,fn):
    self.lock_acquire('getTreeViewIndex')
    for wtn in range(self.listbox.size()-1,-1,-1):
      wt=self.listbox.get(wtn)
      (ts,vt,cnv,cfn,cfd,nd)=wt[0]
      if ((nv==int(cnv)) and (fd==cfd) and (fn==cfn)):
        self.lock_release('getTreeViewIndex')
        return wtn
    self.lock_release('getTreeViewIndex')
    return -1

  def getTree(self,fd,fn):
    self.lock_acquire('getTree')
    for t in G___.treeStorage:
      if ((t.filedir==fd) and (t.filename==fn)):
        self.lock_release('getTree')
        return t
    self.lock_release('getTree')
    return None

  def getSameView(self,fd,fn,node):
    self.lock_acquire('getSameView')
    for t in G___.treeStorage:
      if ((t.filedir==fd) and (t.filename==fn)):
        for v in t.viewlist:
          if (v.node==node):
            self.lock_release('getSameView')
            return v
    self.lock_release('getSameView')
    return None

  def closeAll(self):
    self.wparent.quit()

  def onexit(self):
    self.closeAllTrees()
    self.saveContext()
    
# -----------------------------------------------------------------------------
# cgnstree is a tree fingerprint
def createDataTableWindow(wcontrol,cgnstree,path):
  node=s7parser.getNodeFromPath(path.split('/')[1:],cgnstree.tree)
  if (type(node[1]) != type(Num.array([1,2]))):
    if (type(node[1]) == type(None)): return None
    if (type(node[1]) == type("s")):
      node=[node[0],Num.array(node[1],dtype='S'),node[2],node[3]]
    if (type(node[1]) == type(1.2)):
      node=[node[0],Num.array([node[1]]),node[2],node[3]]
    if (type(node[1]) == type(1)):
      node=[node[0],Num.array([node[1]]),node[2],node[3]]
  cgnstree.viewtype='D'
  wt=s7tableSimple.wSlidingWindowView(wcontrol,cgnstree,node,path)
  t=cgnstree.viewlist[-1]  
  wcontrol.listbox.insert('end',cgnstree.state,t.type,t.id,
                          cgnstree.filename,cgnstree.filedir,t.node)
  wcontrol.grid()
  return wt

# -----------------------------------------------------------------------------
# cgnstree is a tree fingerprint  
def createDataTreeWindow(wcontrol,cgnstree,recurse,startnode=None,parent=None):
  wt=s7treeSimple.wTreeSimple(wcontrol,cgnstree,startnode,parent)
  if (recurse):
    for n in range(0,G___.maxRecurse+1): wt.expandOneMoreLevel()
  t=cgnstree.viewlist[-1]
  wcontrol.listbox.insert('end',cgnstree.state,t.type,t.id,
                          cgnstree.filename,cgnstree.filedir,t.node)
  wcontrol.grid()
  return wt

# -----------------------------------------------------------------------------
# --- last line