from ilastik.shell.gui.startShellGui import startShellGui
from objectClassificationWorkflow import ObjectClassificationWorkflow


def debug_with_existing(shell, workflow):
    """
    (Function for debug and testing.)
    """
    projFilePath = "/home/mschiegg/bla.ilp"
    #projFilePath = '/magnetic/gigacube.ilp'
    #projFilePath = '/home/bergs/Downloads/synapse_detection_training1.ilp'
    #projFilePath = '/magnetic/250-2.ilp'
    # Open a project
    shell.openProjectFile(projFilePath)


if __name__=="__main__":
    startShellGui( ObjectClassificationWorkflow, debug_with_existing )
    #startShellGui(ObjectClassificationWorkflow)