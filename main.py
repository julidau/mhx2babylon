import argparse
import json
import copy
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
Used to encode the BabylonJS class to JSON 
'''
class Encoder(json.JSONEncoder):
	def default(self, input):
		if isinstance(input, Mesh):
			print("write mesh", input.name);
			output = copy.deepcopy(input.__dict__);
			del output["parent"]
			return output
			
		if isinstance(input, Skeleton):
			return input.__dict__;
			
		return input;


'''
Represents a BabylonJS Mesh
'''
class Mesh:
	'''
	initialize empty mesh
	'''
	def __init__(this, scene):
		this.parent = scene; # save scene handle
		
		this.name = "";
		this.id = "";
		this.materialId = "";
		
		this.position = [0,0,0];
		this.scaling = [1,1,1];
		
		
		this.isVisible = True;
		this.isEnabled = True;
		this.checkCollision = False;
		this.receiveShadows = False;
		this.pickable = True;
		
		this.billboardMode = 0; # normal
		this.physicsImposter = 0;
		this.tags = "";
		this.animations = [];
		this.instances = [];
		this.actions = [];
		
		this.submeshes = [];
		this.positions = []; # vertex buffer
		this.normals   = []; # normals buffer
		this.uv        = []; # uv buffer
		this.indices   = []; # index buffer
	
	def convertWeights(this, input):
		this.skeletonId = 0; # only one skeleton supported by mhx2
		this.matricesWeights = [];
		this.matricesIndices = [];
		
		influencers = {};
		numInfluencers = 0; # keeps track of the maximum of bones that influence
							# one vertex
		
		# list all bones and note the weight
		# for each vertex
		for bonename in input:
			weights = input[bonename];
			boneId = this.parent.skeletons[0].getBoneByName(bonename);
			
			for w in weights:
				vertexId = w[0];
				
				if not vertexId in influencers:
					influencers[vertexId] = [];
				
				influencers[vertexId].append([boneId, w[1]]);				
				if numInfluencers < len(influencers[vertexId]):
					# count the maximum number of influencers
					numInfluencers = len(influencers[vertexId]);
		
		# write influencers
		# cap to 8 (babylonjs maximum)
		if numInfluencers > 8:
			print("mesh has more than 8 relevant bones influencing it. Babylon has a limit 8 bones per vertex. Will ignore the remaining weights");
			numInfluencers = 8; 
		
		# write only if there are ANY bones
		if numInfluencers == 0:
			return;
		
		if numInfluencers > 4:
			this.matricesIndicesExtra = [];
			this.matricesWeightsExtra = [];
			
		this.numBoneInfluencers = numInfluencers; # seems to be an optional attribute
		print("type:", type(influencers));
		
		for vertex in sorted(influencers):
			data = influencers[vertex];
			l = len(data);
		
			# write matricesIndices and matricesWeights
			for i in range(0,4):
				this.matricesIndices.append(data[i][0] if i < l else 0);
				this.matricesWeights.append(data[i][1] if i < l else 0);
			
			if numInfluencers > 4:
				# write extra
				for i in range(0,4):
					this.matricesIndicesExtra.append(data[i+4][0] if i+4 < l else 0);
					this.matricesWeightsExtra.append(data[i+4][1] if i+4 < l else 0);
				
	def fromMhx2(input, scene):
		this = Mesh(scene);
		
		this.name = input["name"];
		this.id = input["name"];
		this.materialId = input["material"]
		
		mhxMesh = input["mesh"];
						
		# babylon collects all vertices in mesh 
		# and then defined all relevant data (index, vertex start etc)
		# in the submeshes
		
		offset = Vector(input["offset"]);
		
		for uv in mhxMesh["uv_coordinates"]:
			this.uv.extend(uv);
			
		for pos in mhxMesh["vertices"]:
			this.positions.extend(Vector(pos).add(offset).array());

		facenormals = {};
		
		for face in mhxMesh["faces"]:
			# must triangulate quads
			if len(face) == 4:
				# calculate face normal
				A = Vector(mhxMesh["vertices"][face[1]]).sub(Vector(mhxMesh["vertices"][face[0]]))
				B = Vector(mhxMesh["vertices"][face[3]]).sub(Vector(mhxMesh["vertices"][face[0]]))
				normal = A.cross(B);
				
				this.indices.extend([face[3], face[1], face[0]]);
				this.indices.extend([face[3], face[2], face[1]]);
				
				# add facenormal for every vertex in this face
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
				normal = normal.add(n);
						
			normal.normalize();
			this.normals.extend(normal.array());
			last = key;	
		
		print("calculated {} normals".format(last+1));
		
		# create submesh
		this.submeshes.append({
			"materialIndex": 0,
			"verticesStart": 0,
			"verticesStop": len(mhxMesh["vertices"]),
			"indexStart": 0,
			"indexStop": len(this.indices),
		});
		
		
		# convert weights of mesh if needed
		# mhx2 only has one skeleton
		if "weights" in mhxMesh:
			this.convertWeights(mhxMesh["weights"]);
			print("converted weights");
		
		return this;
		
'''
Represents a BabylonJS Scene
'''
class BabylonJS:
	def __init__(this):
		this.producer = {"name": "mhx2babylon", "version":"2.0.27", "exporter_version":"1.0.0"}
	
		this.multiMaterials = [];
		this.shadowGenerators = [];
		
		# necessary flags (don't hold value in this context)
		this.autoClear = False;
		this.workerCollisions = False;
		this.collisionsEnabled = False;
		this.physicsEnabled = False;
		this.autoAnimate = False;
		
		# scene settings (most likely also ignored by importer)
		this.clearColor = [1,1,1];
		this.ambientColor = [1,1,1];
		this.gravity = [0,-9,0];
		this.cameras = [];
		this.activeCamera = ""
		this.lights = [];
		
		# attributes we do not posses
		this.particleSystems = [];
		this.lensFlareSystems = [];
		this.actions = [];
		this.sounds = [];
	
		# The only things of importance
		this.materials = [];
		this.skeletons = [];
		this.meshes = [];
	
	def fromMhx2(input):
		this = BabylonJS();
		
		print ("begin conversion");
		
		# convert materials
		for material in input["materials"]:
			this.materials.append(convertMaterial(material))

		# TODO: test
		if "skeleton" in input:
			this.skeletons = [Skeleton(input["skeleton"])];
			
		# convert meshes
		this.convertMeshes(input["geometries"]);
		
		print ("conversion is finished");
		return this;
		
	def convertMeshes(this, input):
		parentId = "";
		
		# find mesh of human (and set as parent for others)
		for mesh in input:
			if mesh["human"]:
				this.meshes.append(Mesh.fromMhx2(mesh,this));
				parentId = mesh["name"]
				print("found parent: ", parentId);
				break;
				
		# convert remaining meshes
		for mesh in input:
			if parentId != "" and mesh["human"]:
				continue;
			
			m = Mesh.fromMhx2(mesh, this);
			# set parent
			m.parentId = parentId;
			this.meshes.append(m);	
			
	
		
'''
Converts a MHX2 texture structure to a babylon texture
'''
def convertTexture(name):
	# TODO: pack image file in base64 field
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
	head = Vector(input["head"]).add(offset);
	tail = Vector(input["tail"]).add(offset);	
	roll = input["roll"];
	
	print(head, tail, roll);
	
	return None;

def convertMatrix(input):
	output = Matrix();
	
	for i in range(0,4):
		for j in range(0,4):
			output[i,j] = input[i][j];
		
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
			newbone["parentBoneIndex"] = this.getBoneByName(bone["parent"]);
		else:
			# root node is parent
			newbone["parentBoneIndex"] = -1;
		
		
		# convert restpose
		origin = Vector(bone["head"]);
		axis   = Vector(bone["tail"]).sub(origin)
		angle  = bone["roll"]
		rest   = Quat(axis, angle);
		
		#origin = Vector([0,0,0]);
		# transformation = shift to point * rotate around origin * shift to origin
		T      = Matrix.translation(origin.multiply(-1)); # shift to origin
		revT   = Matrix.translation(origin);              # shift back to point
		rotMat = rest.matrix();                           # rotate around origin
		
		# combine all transformations
		mat = revT.multiply(rotMat.multiply(T)); 
		
		# write matrix to bone		
		newbone["matrix"] = mat.array();
		newbone["rest"]   = mat.array();
		newbone["length"] = Vector(axis).length();
		newbone["index"]  = len(this.bones);
		
		
		
		this.bones.append(newbone);
		
	def getBoneByName(this, name):
		for index, bone in enumerate(this.bones):
			if bone["name"] == name:
				return index
		
		raise RuntimeError("skeleton references parent bone before it existing");
	
	def getBoneMap(this):
		output = {}
		for index, bone in enumerate(this.bones):
			output[bone["name"]] = index;
			
		return output;		
		
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
		
def convert(input):
	output = BabylonJS.fromMhx2(input);
	return output.__dict__;
	
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

	output = convert(data);
	output["producer"]["file"] = path.basename(args.output);
	
	# write output
	with  open(args.output, "w") as file:
		json.dump(output, file, cls=Encoder);

if __name__ == "__main__":
	main();
