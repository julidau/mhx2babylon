
canvas = document.querySelector("#main");
engine = new BABYLON.Engine(canvas, true);

scene = function(){
	scene = new BABYLON.Scene(engine);
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
