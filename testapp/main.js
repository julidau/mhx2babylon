
canvas = document.querySelector("#main");
engine = new BABYLON.Engine(canvas, true);


scene = function(){
	scene = new BABYLON.Scene(engine);
	assetManager = new BABYLON.AssetsManager(scene);
	
	referenceMesh = assetManager.addMeshTask("model", "", "model/", "reference.babylon");
	referenceMesh.onError = function(task, error, e) {
		console.error("could not load reference model:", error);
	}
	referenceMesh.onSuccess = function(task) {
		console.log("loaded reference model");
		task.loadedMeshes[1].position = new BABYLON.Vector3(5,0,0);
	}
	
	convertedMesh = assetManager.addMeshTask("model2", "", "model/", "test.babylon");
	convertedMesh.onError = function(t, error, e) {
		console.error("could not load converted model:", error);
	}
	
	convertedMesh.onSuccess = function(task) {
		console.log("loaded converted model");
		task.loadedMeshes[1].position = new BABYLON.Vector3(-5,0,0);
	}
	
	assetManager.load();
	
	camera = new BABYLON.ArcRotateCamera("Camera", Math.PI/2, Math.PI/2, 2, BABYLON.Vector3.Zero(), scene);
	camera.attachControl(canvas, true);
	
	light = new BABYLON.HemisphericLight("light", new BABYLON.Vector3(0,1,0), scene);
	sphere = BABYLON.MeshBuilder.CreateSphere("sphere", {diameter: 1}, scene);
	
	
	return scene;
}();


engine.runRenderLoop(function() {
	scene.render();
});

window.addEventListener("resize", engine.resize);

console.log("starting app....");
