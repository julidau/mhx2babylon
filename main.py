import argparse
import json
from geometry import *
from math import sin,cos,sqrt
from os import path

## defines the output skeleton for the babylon file
output = {
	"producer": {"name": "mhx2babylon", "version":"2.0.27", "exporter_version":"1.0.0"}, 
	"materials":[],
    "autoClear": False, # boolean,
    "clearColor": [1,1,1], # color3,
    "ambientColor": [1,1,1], # color3,
    "gravity": [0,-9,0], # vector3 (usually [0,-9,0]),
    "cameras": [], # array of Cameras (see below),
    "activeCamera_": "",# string,
    "lights": [], # array of Lights (see below),
    "multiMaterials": [], # array of MultiMaterials (see below),
    "shadowGenerators": [], # array of ShadowGenerators (see below),
    "skeletons": [],  # array of Skeletons (see below),
    "particleSystems": [], # array of ParticleSystems (see below),
    "lensFlareSystems": [], # array of LensFlareSystems (see below),
    "actions": [], #array of actions (see below),
    "sounds": [], #array of Sounds (see below),
    "workerCollisions": False, # boolean,
    "collisionsEnabled": False, # boolean,
    "physicsEnabled": False, #boolean,
    "autoAnimate": False, #boolean,
}

'''
Converts a MHX2 texture structure to a babylon texture
'''
def convertTexture(name):
	return {
		"name": name,
		"level": 1,
		"has_alpha":1,
		"uOffset":0,
		"vOffset":0,
		"uScale":1,
		"vScale":1,
		"uAng":0,
		"vAng":0,
		"wAng":0,
		"wrapU":1,
		"wrapV":1,
		"coordinatesIndex":0,
		"coordinatesMode":0,
	};

'''
Converts a MHX2 material to a babylon material 
'''
def convertMaterial(input):
	# create Texture skeleton
	material = {
		"name": input["name"],
		"id": input["name"],
		"backfaceCulling": input["backfaceCull"],
	};
	
	textureMap = {
		"diffuse_texture": "diffuseTexture",
		"normal_map_texture": "bumpTexture",
	}
	
	colorMap = {
		"diffuse_color": "diffuse",
		"specular_color": "specular",
		"ambient_color": "ambient",
		"emissive_color": "emissive",
	}
	
	# convert colors
	for aname, bname in colorMap.items():
		if aname in input:
			material[bname] = [];
			material[bname].extend(input[aname]);
	
	# convert textures
	for aname, bname in textureMap.items():
		if aname in input:
			material[bname] = convertTexture(input[aname]);
			
	return material;
	
def convertBone(input, offset):
	# don't add Root to output skeleton 
	if input["name"] == "Root":
		return None;
		
	# calculate reset pose based on offset and head/tail vector
	head = addVector(input["head"], offset);
	tail = addVector(input["tail"], offset);	
	roll = input["roll"];
	
	print(head, tail, roll);
	
	return None;

def convertMatrix(input):
	output = [];
	
	for i in range(0,4):
		for j in range(0,4):
			output.append(input[i][j]);
		
	return output;

class Skeleton: 
	def __init__(this, input):
		this.bones = [];
		this.name  = input["name"];
		this.id = 0;
		
		offset = input["offset"];
		
		for bone in input["bones"]:
			this.importBone(bone, offset);
		
	def importBone(this, bone, offset):
		# don't import root
		newbone = {
			"name": bone["name"],
		}
		
		# find parent (with index)
		if "parent" in bone:
			newbone["parentBoneIndex"] = this.BoneByName(bone["parent"]);
		else:
			# root node is parent
			newbone["parentBoneIndex"] = -1;
		
		# convert matrix
		newbone["matrix"] = convertMatrix(bone["matrix"]);
		
		# convert restpose
		axis = Vector(bone["tail"]).sub(Vector(bone["head"]))
		angle = bone["roll"]
		rest = Quat(axis, angle);
		
		newbone["rest"] = convertMatrix(rest.matrix());
		newbone["length"] = Vector(axis).length();
		newbone["index"] = len(this.bones);
		
		this.bones.append(newbone);
		
	def BoneByName(this, name):
		for index, bone in enumerate(this.bones):
			if bone["name"] == name:
				return index
		
		raise RuntimeError("skeleton references parent bone before it existing");
		
		
		
def convertSkeleton(input):
	return Skeleton(input).__dict__;
	
def convertMesh(input, hasSkeleton, parent):
	mesh = {
		"name":input["name"],
		"id": input["name"],
		"materialId": input["material"],
		"isVisible": True,
		"isEnabled": True,
		"checkCollision": False,
		"receiveShadows": False,
		"pickable": False,
		"billboardMode": 0,
		"physicsImposter": 0,
		"tags": "",
		"animations":[],
		"instances":[],
		"actions": [],
		
		# mesh stuff
		"submeshes": [], # The mesh definition
		"positions": [], # Vertex Buffer
		"normals": [], # vertex normals
		"uv": [], # vertex uvs
		"indices": [], # index buffer	
	}
	
	# mhx2 only has one skeleton
	if hasSkeleton:
		mesh["skeletonId"] = 0;
		
		# TODO: write matricesWeight and matricesIndices
	
	# babylon collects all vertices in mesh 
	# and then defined all relevant data (index, vertex start etc)
	# in the submeshes
	mhxMesh = input["mesh"];
	offset = Vector(input["offset"]);
	
	for uv in mhxMesh["uv_coordinates"]:
		mesh["uv"].extend(uv);
		
	for pos in mhxMesh["vertices"]:
		mesh["positions"].extend(Vector(pos).add(offset).array());

	if parent != "":
		mesh["parentId"] = parent;
		
	facenormals = {};
	
	for face in mhxMesh["faces"]:
		# must triangulate quads
		if len(face) == 4:
			A = Vector(mhxMesh["vertices"][face[1]]).sub(Vector(mhxMesh["vertices"][face[0]]))
			B = Vector(mhxMesh["vertices"][face[3]]).sub(Vector(mhxMesh["vertices"][face[0]]))
			normal = A.cross(B);
			
			mesh["indices"].extend([face[3], face[1], face[0]]);
			mesh["indices"].extend([face[3], face[2], face[1]]);
			
			for i in face:
				if not (i in facenormals):
					facenormals[i] = [];
					
				facenormals[i].append(normal);
		else:
			raise ValueError("found triangle, expected quad");
	
	# calculate normals for vertices
	# by blending the normals
	# of all adjacent faces together
	warn = False;
	last = -1;
	for key in sorted(facenormals):
		while key > last+1:
			# fill unknown normals with [0,0,0] for now
			mesh["normals"].extend([0,0,0]);
			last = last +1;
			if not warn:
				print("[WARN] fill missing normals, which should not be nessesary");
				warn = True # only warn once
				
		# blend normals
		normal = Vector([0,0,0]);
		for n in facenormals[key]:
			normal.add(n);
					
		normal.normalize();
		mesh["normals"].extend(normal.array());
		last = key;	
	
	print("calculated {} normals".format(last+1));
	
	mesh["submeshes"].append({
		"materialIndex": 0,
		"verticesStart": 0,
		"verticesStop": len(input["mesh"]["vertices"]),
		"indexStart": 0,
		"indexStop": len(mesh["indices"]),
	});
	
	mesh["position"] = [0,0,0];
	mesh["scaling"] = [1,1,1];
	return mesh;

def convertMeshes(input, hasSkeleton):
	output = [];
	parentId = "";
	
	# find mesh of human
	for mesh in input:
		if mesh["human"]:
			output.append(convertMesh(mesh, hasSkeleton, ""));
			parentId = mesh["name"]
			print("found parent: ", parentId);
			break;
			
	for mesh in input:
		if parentId != "" and mesh["human"]:
			continue;
			
		output.append(convertMesh(mesh, hasSkeleton, parentId));
	
	return output;
	
		
def convert(input):
	# convert materials
	output["materials"] = [];
	
	for material in input["materials"]:
		output["materials"].append(convertMaterial(material))

	hasSkeleton = False;
	# TODO: test
	if "skeleton" in input:
		output["skeletons"] = [convertSkeleton(input["skeleton"])];
		hasSkeleton = True;
		
	# convert meshes
	output["meshes"] = convertMeshes(input["geometries"], hasSkeleton);
	

def main():
	parser = argparse.ArgumentParser(description="converts mhx files from makehuman to babylon mesh files")
	parser.add_argument("input", help="the input.mhx2 file to convert")
	parser.add_argument("--output", "-o", dest="output", action="store", help="where to store the resulting .babylon file")

	args = parser.parse_args()

	# check output
	if (args.output == None):
		args.output = path.splitext(args.input)[0] + ".babylon"

	# open input file
	data = {}
	with open(args.input, "r") as file:
		data = json.load(file);

	print(len(data["materials"]));
	print(data["geometries"][0]["license"]);

	convert(data);
	output["producer"]["file"] = path.basename(args.output);
	# write output
	with  open(args.output, "w") as file:
		json.dump(output, file);

if __name__ == "__main__":
	main();
