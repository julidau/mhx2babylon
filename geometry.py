from math import cos, sin, sqrt

'''
Defines a Vector
'''
class Vector:
	def __init__(this, arr):
		this.x = arr[0];
		this.y = arr[1];
		this.z = arr[2];
	
	def __getitem__(this, key):
		if key == 0:
			return this.x;
		if key == 1:
			return this.y;
		if key == 2:
			return this.z;
			
		raise KeyError("index out of range");
		
	def sub(this, other):
		this.x -= other.x;
		this.y -= other.y;
		this.z -= other.z;
		return this
	
	def add(this, other):
		this.x += other.x;
		this.y += other.y;
		this.z += other.z;
		return this;
		
	# divide components by scalar
	def div(this, s):
		this.x /= s;
		this.y /= s;
		this.z /= s;
		return this;
		
	# return length of vector
	def length(this):
		return sqrt(this.x**2 + this.y**2 + this.z**2);

	# normalize vector
	def normalize(this):
		l = this.length();
		return this.div(l);
	
	# return vector as array [x,y,z]		
	def array(this):
		return [this.x, this.y, this.z];
		
	def cross(this, other):
		temp = Vector([0,0,0]);
		
		temp.x = this.y * other.z - this.z * other.y;
		temp.y = this.z * other.x - this.x * other.z;
		temp.z = this.x * other.y - this.y * other.x;
		
		return temp; 		
	
'''
Defines a quaternion as axis, angle
'''	
class Quat:
	def __init__(this, axis, angle):
		this.x = axis.x * sin(angle/2);
		this.y = axis.y * sin(angle/2);
		this.z = axis.z * sin(angle/2);
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

