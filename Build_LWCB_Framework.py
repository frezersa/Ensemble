"""builds the lwcb operational framework. we will build locally & distribute via ftp.

user must have 'Build_Framework' directory locally; contains all folders required. hosted on ftp for use.
user performs svn checkout within the 'Build_Framework' of LWCB_WinnipegRiver, only grabbing trunk.

this script pulls files needed from checkout

bin files must be in 'bin' folder located on same level as 'trunk'

output is a final directory with all files/executables in correct location. 

directory can be zipped for distribution. zip name is same as frameworks.

for lwcb, call '
python C:\WATFLOOD_Repo\WATFLOOD_Development\trunk\Python\Build_LWCB_Framework.py --Directory C:\WR_WTFLD_Framework --Trunk C:\WATFLOOD_Repo\WATFLOOD_Development\trunk --CaPA C:\Users\JMB\workspace\CaPA\CaPA_WATFLOOD
'
"""


import glob
import os
import argparse
import shutil
import subprocess
from datetime import date

class args(object):
    pass

# get command line arguments
data = args()
parser = argparse.ArgumentParser()
parser.add_argument('--Directory', help="Full path of local root of directory 'Build_Framework'")
parser.add_argument('--Trunk', help="Full path of root SVN Checkout directory within 'Build_Framework'")
parser.add_argument('--CaPA', help="Full path of directory holding CaPA .r2c files")
parser.add_argument('--Software',action="store_true",help="Include installation software prerequisites in final build")
parser.add_argument('--Zip',action="store_true",help="Zip up final framework structure. Must have 7-zip installed and on path.")
parser.parse_args(namespace=data)


localDirectory = data.Directory #r"D:\Projects\LWCB_Automation\Build_Framework"
svnCheckout = data.Trunk #= r"D:\Projects\LWCB_Automation\Build_Framework\LWCB_WinnipegRiver"
CapAdirectory = data.CaPA
Prerequisites = data.Software #False
Zip = data.Zip #True

# framework name
frameworkName = "WR_WTFLD_Framework"


# framework directory
svnFrameworkDirectory = os.path.join(svnCheckout,"Frameworks","LWCB")
print svnFrameworkDirectory
# template directory
svnTemplateDirectory = os.path.join(svnCheckout,"Template")
# Python scripts directory
svnPythonDirectory = os.path.join(svnCheckout,"Python")
# R scripts directory
svnRDirectory = os.path.join(svnCheckout,"R")
# bin directory
trunkparent = os.path.dirname(svnCheckout)
svnBinDirectory = os.path.join(svnCheckout, "bin")
# print svnBinDirectory

# specific R files not contained in rlib to copy
r_files = ["LWCBtoTBO.R","LWCB_RESIN_COMPARISON_Framework.R","LWCB_SPL_COMPARISON_Framework.R","LWCBtoPT2.R","forecastmaps.R","LakeLevels.R","r2cAdjust.R","Ensemble_process.R"]

# # build_framework directory names
binaries = "bin"
softwarePrerequisties = "Installation_Prerequisites"


# http://stackoverflow.com/questions/1868714/how-do-i-copy-an-entire-directory-of-files-into-an-existing-directory-using-pyth
# overcomes the limitations of shutil.copytree; in that the directories can not exist prior to dst copy.
def copytree(src, dst, symlinks=False, ignore=None):
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, symlinks, ignore)
        else:
            shutil.copy2(s, d)

# finds a specific file name and returns full path
# http://stackoverflow.com/questions/1724693/find-a-file-in-python
def find(name, path):
    for root, dirs, files in os.walk(path):
        if name in files:
            return os.path.join(root, name)


# set working directory to input local directory
os.chdir(localDirectory)


# has older version of framework been built. remove if it has. check for 'framework' in file name.
files = os.listdir(".")
for e in files:
    if e == frameworkName:
        shutil.rmtree(e)


# -- folder structure
# trunk/frameworks/ec_operational_framework
copytree(svnFrameworkDirectory,localDirectory)

# -- copy template files trunk/Templates into framework/model_repository/lib
copytree(svnTemplateDirectory,os.path.join(localDirectory,frameworkName,"model_repository","lib"))

# -- copy batch file to execute main scripts
shutil.copy(os.path.join(svnTemplateDirectory,"RunWATFLOOD.bat"),os.path.join(localDirectory,frameworkName))


# -- Python & R scripts framework/model_repository/scripts.
# Python scripts. only copy *.py files
scriptsDirectory = os.path.join(localDirectory,frameworkName,"model_repository","scripts")
files = glob.glob(os.path.join(svnPythonDirectory,"*.py"))
for e in files:
    shutil.copy(os.path.join(svnPythonDirectory,e),scriptsDirectory)

# R scripts
# copy specific R files
for e in r_files:
    foundPath = find(e,svnRDirectory)
    # copy files to scripts directory
    shutil.copy(foundPath,scriptsDirectory)

# copy the rlib folder
# make sub folder rlib. copytree does not recreate top dir
os.mkdir(os.path.join(scriptsDirectory,"rlib"))
copytree(os.path.join(svnRDirectory,"rlib"),os.path.join(scriptsDirectory,"rlib"))

#Most current CaPA file
CurrentYear = date.today().year
CaPAfile = str(CurrentYear) + '0101_met.r2c'
shutil.copy(os.path.join(CapAdirectory,CaPAfile),os.path.join(localDirectory,frameworkName,"model_repository","wxdata","CaPA"))



# -- copy Build_Framework /bin files to framework/model_directory/bin
binDirectory = os.path.join(frameworkName,"Model_Repository",binaries)
copytree(svnBinDirectory,binDirectory)


# copy Build_Framework software Installation_Prerequisties. if client already has these, ignore. allows for smaller package size for testing.
if Prerequisites:
    path = os.path.join(frameworkName,softwarePrerequisties)
    copytree(softwarePrerequisties,path)


# zip up final framework structure
if Zip:
    zipOut = os.path.join(localDirectory,frameworkName + ".zip")
    zipDirectory = os.path.join(localDirectory,frameworkName + "/")
    cmd = ["7z.exe","a",zipOut,zipDirectory]
    print cmd
    subprocess.call(cmd,shell=True)

