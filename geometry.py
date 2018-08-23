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
	
	def multiply(this, s):
		this.x *= s;
		this.y *= s;
		this.z *= s;
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
A 4x4 matrix
'''
class Matrix:
	def __init__(this):
		this.data = [0]*16;
		# create identity
		for i in range(0,4):
			this[i,i] = 1;
			
	def __getitem__(this, key):
		if type(key) == type(0):
			return this.data[key*4:(key+1)*4];
			
		return this.data[key[0]+key[1]*4];
		
	def __setitem__(this, key, value):
		if type(key) == type(0):
			for i in range(0,4):
				this.data[i + key*4] = value[i];
		else:			
			this.data[key[0]+key[1]*4] = value;
			
		return value;
		
	def multiply(this,other):
		result = Matrix();
		
		for i in range(0,4):
			for j in range(0,4):
				sum = 0;
				for ii in range(0,4):
					sum = sum + this[ii, j] * other[i, ii];
					
				result[i,j] = sum;
				
		return result;
	
	def translation(vector):
		result = Matrix();
		result[3,0] = vector.x;
		result[3,1] = vector.y;
		result[3,2] = vector.z;
		return result;
	
	
	def array(this):
		result = [];
		
		# convert to BABYLONJS column first notation
		for i in range(0,4):
			for j in range(0,4):
				result.append(this[i,j]);
			
		return result;

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
	
	def transMat(this, origin):
		result = Matrix();
		sqw = this.w*this.w;
		sqx = this.x*this.x;
		sqy = this.y*this.y;
		sqz = this.z*this.z;
		
		result[0,0] =  sqx - sqy - sqz + sqw;  # since sqw + sqx + sqy + sqz =1
		result[1,1] = -sqx + sqy - sqz + sqw;
		result[2,2] = -sqx - sqy + sqz + sqw;

		tmp1 = this.x*this.y;
		tmp2 = this.z*this.w;
		
		result[0,1] = 2.0 * (tmp1 + tmp2);
		result[1,0] = 2.0 * (tmp1 - tmp2);

		tmp1 = this.x*this.z;
		tmp2 = this.y*this.w;
		result[0,2] = 2.0 * (tmp1 - tmp2);
		result[2,0] = 2.0 * (tmp1 + tmp2);

		tmp1 = this.y*this.z;
		tmp2 = this.x*this.w;
		result[1,2] = 2.0 * (tmp1 + tmp2);
		result[2,1] = 2.0 * (tmp1 - tmp2);

		a1 = origin.x;
		a2 = origin.y;
		a3 = origin.z;

		result[0,3] = a1 - a1 * result[0,0] - a2 * result[0,1] - a3 * result[0,2];
		result[1,3] = a2 - a1 * result[1,0] - a2 * result[1,1] - a3 * result[1,2];
		result[2,3] = a3 - a1 * result[2,0] - a2 * result[2,1] - a3 * result[2,2];
		result[3,0] = result[3,1] = result[3,2] = 0.0;
		result[3,3] = 1.0;
		
		return result;
		
	# matrix describing a rotation around the origin
	def matrix(this):
		this.normalize();
		
		matrix = Matrix();
		
		matrix[0] = [
			1- 2*this.y**2 - 2*this.z**2,
			2*this.x*this.y - 2*this.z*this.w,
			2*this.x*this.z + 2*this.y*this.w,
			0
		];
		
		matrix[1] = [
			2*this.x*this.y + 2*this.z*this.w,
			1-2*this.x**2 - 2*this.z**2,
			2*this.y*this.z - 2*this.x*this.w,
			0
		];
		
		matrix[2] = [
			2*this.x*this.z - 2*this.y*this.w,
			2*this.y*this.z + 2*this.x*this.w,
			1-2*this.x**2 - 2*this.y**2,
			0
		];
		
		matrix[3] = [
			0,
			0,
			0,
			1.0,
		];
		
		return matrix;

