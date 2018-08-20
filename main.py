import argparse
import json
from math import sin,cos,sqrt
from os import path

output = {
"producer": {"name": "mhx2babylon", "version":"1.0.0"}, 
"materials":[],
}

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
	
def addVector(one, two):
	if len(one) != len(two) or len(one) != 3:
		raise ValueError("no vector given");
	
	one[0] += two[0];
	one[1] += two[1];
	one[2] += two[2];
	
	return one;

def subVector(one, two):
	if len(one) != len(two) or len(one) != 3:
		raise ValueError("no vector given");
	
	one[0] -= two[0];
	one[1] -= two[1];
	one[2] -= two[2];
	
	return one;
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
			
class Quat:
	def __init__(this, axis, angle):
		this.x = axis[0] * sin(angle/2);
		this.y = axis[1] * sin(angle/2);
		this.z = axis[2] * sin(angle/2);
		this.w = cos(angle/2);
	
	def normalize(this):
		l = sqrt(this.x**2 + this.y**2 + this.z**2 + this.w**2);
		this.x /= l;
		this.y /= l;
		this.z /= l;
		this.w /= l;
		
	def matrix(this):
		this.normalize();
		
		matrix = [];
		
		matrix.append([
			1- 2*this.y**2 - 2*this.z**2,
			2*this.x*this.y - 2*this.z*this.w,
			2*this.x*this.z + 2*this.y*this.w,
			0
		]);
		
		matrix.append([
			2*this.x*this.y + 2*this.z*this.w,
			1-2*this.x**2 - 2*this.z**2,
			2*this.y*this.z - 2*this.x*this.w,
			0
		]);
		
		matrix.append([
			2*this.x*this.z - 2*this.y*this.w,
			2*this.y*this.z + 2*this.x*this.w,
			1-2*this.x**2 - 2*this.y**2,
			0
		]);
		
		matrix.append([
			0,
			0,
			0,
			1.0,
		]);
		
		return matrix;

class Vector:
	def __init__(this, arr):
		this.x = arr[0];
		this.y = arr[1];
		this.z = arr[2];
		
	def sub(this, other):
		this.x -= other.x;
		this.y -= other.y;
		this.z -= other.z;
		
	def length(this):
		return sqrt(this.x**2 + this.y**2 + this.z**2);

	def array(this):
		return [this.x, this.y, this.z];
		
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
		axis = subVector(bone["tail"], bone["head"]);
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
	
def convertMesh(input, hasSkeleton):
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
	}
	
	# mhx2 only has one skeleton
	if hasSkeleton:
		mesh["skeletonId"] = 0;
		
		# TODO: write matricesWeight and matricesIndices
	
	# babylon collects all vertices in mesh 
	# and then defined all relevant data (index, vertex start etc)
	# in the submeshes
	mesh["submeshes"] = [];
	mesh["positions"] = [];
	mesh["indices"] = [];
	
	for pos in input["mesh"]["vertices"]:
		mesh["positions"].extend(pos);

		
	for face in input["mesh"]["faces"]:
		# must triangulate quads
		if len(face) == 4:
			mesh["indices"].extend([face[0], face[1], face[3]]);
			mesh["indices"].extend([face[1], face[2], face[3]]);
		else:
			raise ValueError("found triangle, expected quad");
	
	mesh["submeshes"].append({
		"materialIndex": 0,
		"verticesStart": 0,
		"verticesStop": len(input["mesh"]["vertices"]),
		"indexStart": 0,
		"indexStop": len(mesh["indices"]),
	});
	
	return mesh;
	
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
	output["meshes"] = [];
	for mesh in input["geometries"]:
		# TODO: give hasSkeleton Arg
		output["meshes"].append(convertMesh(mesh, hasSkeleton));

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

	# write output
	with  open(args.output, "w") as file:
		json.dump(output, file);

if __name__ == "__main__":
	main();
