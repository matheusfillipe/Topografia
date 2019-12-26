import pathlib
import sys
from pip._internal import main
from .app.controller.estacas import msgLog
import platform
is_windows = any(platform.win32_ver())

plugin_dir = pathlib.Path(__file__).parent
sys.path.append(plugin_dir)

requirements=["OpenGL"]


try:
    import OpenGL
except:
    #with open(str(plugin_dir / 'requirements.txt'), "r") as requirements:
    requirements=["PyOpenGL" "PyOpenGL_accelerate"]
    for dep in requirements.readlines():
        dep = dep.strip().split("==")[0]
        try:
            __import__(dep)
        except:
            msgLog("{} not available, installing".format(dep))
            if is_windows:
                main.main(['install', dep])
            else:
                main(['install', dep])

msgLog("Dependências checadas!")