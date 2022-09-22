import os

from isaaq.Common.QubitMapping import *
from isaaq.Common.QubitMappingProblem import *
from isaaq.IO.QubitMappingProblem import *
from isaaq.IO.QubitMappingResult import *
from isaaq.Solver.Amplify.AmplifySettings import *

from .RuntimeDataTypes import *
from typing import Tuple

def _ExportRuntimeSettings(settings: AmplifyRuntimeSettings, filepath: str):
	S = []
	S.append(settings.token + "\n")
	S.append(str(settings.timeout) + "\n")
	S.append(str(settings.constraint_strength) + "\n")

	with open(filepath, "w") as f:
		f.writelines(S)

def _ImportRuntimeSettings(filepath: str) -> AmplifyRuntimeSettings:
	with open(filepath, "r") as f:
		S = f.readlines()
	
	token = S[0].strip()
	timeout = int(S[1].strip())
	constraint_strength = float(S[2].strip())

	return AmplifyRuntimeSettings(
		token,
		timeout,
		constraint_strength
	)

def _ExportRuntimeInfo(info: AmplifyRuntimeInfo, filepath: str):
	S = []
	S.append(str(info.constraint_strength) + "\n")

	with open(filepath, "w") as f:
		f.writelines(S)

def _ImportRuntimeInfo(filepath: str) -> AmplifyRuntimeInfo:
	with open(filepath, "r") as f:
		S = f.readlines()
	
	constraint_strength = float(S[0].strip())
	
	return AmplifyRuntimeInfo(
		constraint_strength
	)


def ExportProblem(
	problem: QubitMappingProblem,
	settings: AmplifyRuntimeSettings,
	id: str
):
	folderPath = os.path.join(os.path.dirname(__file__), "../temp_problems")
	problemFilePath = os.path.join(folderPath, id + "_problem.txt")
	settingsFilePath = os.path.join(folderPath, id + "_settings.txt")

	os.makedirs(folderPath, exist_ok = True)

	ExportMappingProblem(problem, problemFilePath)
	_ExportRuntimeSettings(settings, settingsFilePath)

def ImportProblem(id: str) -> Tuple[QubitMappingProblem, AmplifyRuntimeSettings]:
	folderPath = os.path.join(os.path.dirname(__file__), "../temp_problems")
	problemFilePath = os.path.join(folderPath, id + "_problem.txt")
	settingsFilePath = os.path.join(folderPath, id + "_settings.txt")

	os.makedirs(folderPath, exist_ok = True)

	problem = ImportMappingProblem(problemFilePath)
	settings = _ImportRuntimeSettings(settingsFilePath)
	return (problem, settings)

def ExportResult(result: QubitMapping, info: AmplifyRuntimeInfo, id: str):
	folderPath = os.path.join(os.path.dirname(__file__), "../temp_results")
	resultFilePath = os.path.join(folderPath, id + "_result.txt")
	infoFilePath = os.path.join(folderPath, id + "_info.txt")

	os.makedirs(folderPath, exist_ok = True)

	ExportMappingResult(result, resultFilePath)
	_ExportRuntimeInfo(info, infoFilePath)

def ImportResult(dst_mapping: QubitMapping, id: str) -> AmplifyRuntimeInfo:
	folderPath = os.path.join(os.path.dirname(__file__), "../temp_results")
	resultFilePath = os.path.join(folderPath, id + "_result.txt")
	infoFilePath = os.path.join(folderPath, id + "_info.txt")

	os.makedirs(folderPath, exist_ok = True)

	ImportMappingResult(dst_mapping, resultFilePath)
	return _ImportRuntimeInfo(infoFilePath)