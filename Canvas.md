# Canvas

## The Canvas Element

A canvas is a HTML element, `<canvas>`, embedded in the HTML like any other element. What's special about the canvas, is that you can draw on it with Javascript.

Most elements have their appearance determined solely by CSS. Their interior might be a single colour, or perhaps a gradient of some kind. It might have a border with some sort of pattern. But ultimately, unless it's an image, it's really all just decoration and positioning for text. With a canvas however, you can draw shapes, arcs, lines - anything you like. They are essentially programatically created images that can change based on user interactions.

For this reason, canvases often underpin many of the complex, dynamic, interactive interfaces we see on the web. Zoomable maps, games, document rendering - and of course, manipulatable 3D scenes such as molstar - all make use of the canvas to do this.

## Canvas Coordinates

Before we get into how you draw things to a canvas, we need to understand its coordinate system.

Canvas elements have `width` and `height` attributes - if you don't supply these they default to 300 and 150 respectively (pixels). These attributes determine two things:

- Unless you overide with CSS, they determine the dimensions of the canvas on screen - how wide and how tall it is, in pixels.
- They determine the coordinate system within the canvas. If you use a width of 500 and a height of 400, then all x-values within the canvas will be between 0 and 500, and all y-values will be between 0 and 400. Values beyond this will be 'outside' the canvas and not visible.

Where it gets somewhat complex is when you also use CSS to determine the size of the canvas. For example:

```html
<html>
  <head>
    <style>
      canvas {width: 800px; height: 500px;}
    </style>
  </head>
  <body>
    <canvas width="400" height="300"></canvas>
  </body>
</html>
```

Here, the canvas will be 800px wide, and 500px high - the CSS overrides the canvas attributes when it comes to the actual dimensions on the page. However, the internal coordinate system of the canvas is still 400 by 300, and when you draw shapes, these values should be used. This is important because the browser will draw the pixels as though they are the size determined by the canvas dimensions, so when they appear on screen here they will be stretched and blocky. Note also that here the aspect ratio has changed, so any circles etc. will become ovals.

Basically, you always want the canvas attributes to match whatever the CSS says the screen size should be. This is straightforward if you hardcode fixed pixel values as in the example above, but if you have the width be something relative, such as `100%`, you need to add logic for updating the canvas attributes and then redrawing whatever you have drawn to the canvas whenever the screen size changes.

## 2D Canvas Context

To interact with a canvas element and draw to it, you need to create a 'context' object. There are different kinds of contexts, each with their own methods and capabilities.

The most straightforward context is `2d`, which draws simple two-dimensional shapes, lines and arcs. This is not the context type that molstar uses, but understanding it is crucial to understanding how the canvas works. You create a context object with Javascript:

```javascript
const canvasElement = document.getElementById("my-canvas-id");
const ctx = canvasElement.getContext("2d");
```

This is not meant as a comprehensive guide to everything that a canvas can do, but to give a basic idea of how you interact with a canvas to draw things. Here is a basic example:

```javascript
// Fill a rectangle
ctx.fillStyle = "steelblue";
ctx.fillRect(50, 50, 200, 100);

// Stroke (outline) a rectangle
ctx.strokeStyle = "darkred";
ctx.lineWidth = 3;
ctx.strokeRect(300, 50, 150, 100);

// Clear everything we have so far
ctx.clearRect(0, 0, canvasElement.width, canvasElement.height);

// Draw a path (triangle)
ctx.beginPath();
ctx.moveTo(100, 200);
ctx.lineTo(200, 350);
ctx.lineTo(0, 350);
ctx.closePath();
ctx.fillStyle = "seagreen";
ctx.fill();

// Draw an arc (circle)
ctx.beginPath();
ctx.arc(400, 275, 75, 0, Math.PI * 2);
ctx.fillStyle = "goldenrod";
ctx.fill();
```

A few things to note:

- There are specific methods for different shapes and line types - for rectangles, circles etc. - and you can draw arbitrary polygons with `lineTo` and `moveTo`.
- The context maintains state, such as the current 'fill style' or 'line width', and uses this on each of the draw methods - you don't pass these colours etc. to the method, it just uses whatever the current state of the context is.
- Once drawn, there is no reference to the shape you have just drawn. It isn't an object in memory, you just gave an instruction to draw some pixels and now they are drawn. To 'delete' a shape, you just overwrite the pixels with a different color, as we did with `clearRect`, but deleting isn't really how you should think of it.

This last point is fundamental to understanding how the canvas works. Once you draw a blue rectangle, those pixels are blue - the canvas doesn't know there's a "rectangle" there. If you wanted the rectangle to appear to move, there's no `move` method - you clear the pixels and redraw the rectangle in a new location. 

As you can imagine, you can draw most any two-dimensional scene you can imagine with this API - but can you create three-dimensional scenes with this API?

## Representing Simple 3D Objects in 2D

We see 3D objects represented in two dimensions all the time - any time you watch television or an online video we see three dimensional scenes flattened into two dimensions in a way that looks correct enough to our brains that it interprets it as 2D, not 3D. To understand how we do this, let's begin with the simplest 3D object to handle - a cube.

Let's define our cube in code:

```javascript
const cube = {
  faces: [
    [[2, 3, 7], [5, 3, 7], [5, 6, 7], [2, 6, 7]],
  	[[2, 3, 4], [5, 3, 4], [5, 6, 4], [2, 6, 4]],
  	[[2, 3, 4], [2, 6, 4], [2, 6, 7], [2, 3, 7]],
  	[[5, 3, 4], [5, 6, 4], [5, 6, 7], [5, 3, 7]],
  	[[2, 6, 4], [5, 6, 4], [5, 6, 7], [2, 6, 7]],
  	[[2, 3, 4], [5, 3, 4], [5, 3, 7], [2, 3, 7]],
  ],
  color: "red"
};
```

We define the cube by giving the xyz coordinates for each of the four corners of each of its six faces, and the colour of the faces (in this case every face has the same colour). How we represent it doesn't matter - we could just have easily defined it by giving the coordinates of its center, its radius, and its orientation. The point is, we have all the information we need to know what space it occupies in three dimensions.

How do we draw this when all we can do is draw 2D shapes? We draw each of its six faces as 2D four-sided polygons. For each face in the cube, we convert the 3d coordinates of its four corners, into the 2d canvas coordinates they will have on screen. The mathematics of how this is done aren't important here, but if you even begin to think of how it *might* be done, you will immediately spot a problem you don't have in 2D - the 2D coordinates depend on where you are looking from. If you are looking directly 'over' the cube it will have a different representation than if you are looking directly at a corner. *For 3D objects, the 2D representation is a function of the object's geometry, **and** the coordinates of the vantage point*.

Let's represent this with some pseudocode:

```javascript
const convert3dFaceTo2dPolygon(face, vantagePoint) {
  // Mathematics goes here
  // Input is four x,y,z values
  // Output is four x,y values
  return [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
}

const drawPolygonToCanvas(ctx, cornerCoordinates2D) {
  ctx.beginPath();
  ctx.moveTo(cornerCoordinates2D[0][0], cornerCoordinates2D[0][1]);
  for (let i = 1; i < cornerCoordinates2D.length; i++) {
    ctx.lineTo(cornerCoordinates2D[i][0], cornerCoordinates2D[i][1]);
  }
  ctx.closePath();
  ctx.stroke();
}

const drawCubeToCanvas(cube, vantagePoint, ctx) {
  for (const face of cube.faces) {
    const cornerCoordinates2D = convert3dFaceTo2dPolygon(face, vantagePoint)
    drawPolygonToCanvas(ctx, cornerCoordinates2D) 
  }
}
```

This would produce something like this:

*Image of cube wireframe goes here*

It is actually six four sided 2D polygons whose edges line up, but your brain probably sees it as the wireframe of a cube. It's a wireframe because we didn't fill in any of the polygons. Our cube is defined so that each face is red, but if our `drawPolygonToCanvas` were updated to just take `cube.color` as an input, and make the interior of each polygon red, we would get this:

*Image of red cube, with every face #ff0000, looking more like a six-sided 2D polygon than a sphere*

Suddenly it doesn't look very much like a cube - more like a sort of skewed hexagon. The problem is, just because an cube's face is a particular colour, that doesn't mean that in real life we would see each face as the same colour, because in real life we also have to factor in *light*. 3D objects' faces have different levels of shadown which darken them, depending on where the light is coming from and how it strikes that face. We need to update our basic example:

```javascript
const convert3dFaceTo2dPolygon(face, vantagePoint) {
  // Mathematics goes here
  // Input is four x,y,z values
  // Output is four x,y values
  return [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
}

const drawPolygonToCanvas(ctx, cornerCoordinates2D, faceColor) {
  ctx.beginPath();
  ctx.moveTo(cornerCoordinates2D[0][0], cornerCoordinates2D[0][1]);
  for (let i = 1; i < cornerCoordinates2D.length; i++) {
    ctx.lineTo(cornerCoordinates2D[i][0], cornerCoordinates2D[i][1]);
  }
  ctx.closePath();
  ctx.stroke();
  ctx.fillStyle = faceColor;
  ctx.fill();
}

const getFaceColor(face, baseColor, lightDirection) {
  // More mathematics goes here - angle calculations etc.
  // Returns a colour string
}

const drawCubeToCanvas(cube, vantagePoint, lightDirection, ctx) {
  for (const face of cube.faces) {
    const cornerCoordinates2D = convert3dFaceTo2dPolygon(face, vantagePoint)
    const faceColor = getFaceColor(face, cube.color, lightDirection)
    drawPolygonToCanvas(ctx, cornerCoordinates2D, faceColor) 
  }
}
```

*Image of more realistic looking cube, albeit with each face one block colour*

This looks like a cube again. There are a few details omitted here - for example now it matters which order we draw the faces in. We only see three of the faces at any given time, so it's important we either only draw those faces, or draw them last so they paint over the ones we can't see. This requires some more calculations. We also need to know or calculate which 'side' of the face is on the exterior of the cube, which again requires more math.

To make the cube look *really* realistic, we would have to calculate the colour not per face (which currently makes each face the same colour) but per *pixel* within each face, which would let the faces have a gradient shadow:

*Example image of the above*

Even for a cube then, rendering requires: transforming 3D coordinates to 2D, accounting for the vantage point, calculating lighting, and determining which faces are visible. And unfortunately, you rarely only need to render cubes.

## Representing Complex 3D Objects in 2D

The workflow above can be used for any simple 3D geometric object. A pyramid for example, would be rendered in the same way, only with triangles for faces instead of squares.

What about a sphere? How many 'faces' does a sphere have? Depending on your viewpoint, the answer is either 'an infinite number' or 'the question doesn't make sense'. Either way, the task becomes more complex.

We have to *approximate* a sphere. For example, we could use an object with eight, triangular faces like so:

*Image of diamond looking thing*

Not very sphere-like. But what if we use more faces?

*Image of soccer ball looking thing*

Definitely more sphere-like, but not strictly speaking a sphere. We can never 'get to' a sphere by increasing the number of faces, but we can get an approximation that the human eye can't distinguish from a sphere if we use enough.

*Image of a sphere*

The worflow is still the same. We represent the sphere with a list of faces, each defined by its vertices. For each face we work out what that face will look like in 2D from a particular vantage point, and what colour it will be for a given light source. We then draw each of the polygons, and trust that our calculation of light and shade is enough to let the human brain handle intepreting it as a sphere.

(Note: in practice, there is another way of representing spheres in 2D using a method called impostors. We will return to this in a later section, but it does not contradict anything we are covering here.)

In fact, *any* three dimensional object can be represented this way, not just geometric shapes. A person, a building, a molecule - you start with its 'real' 3D description, and then convert it into a **mesh** of polygons (potentially thousands or even millions) which approximate the curves and edges of that object. Each polygon is then converted to 2D coordinates using math, and each polygon face is then coloured to provide shade and a sense of depth. Do this for multiple objects, and you have an entire three dimensional scene.

No matter how complex, it's all just polygons as far as the computer is concerned.

## The Limitations of 2D Context

Let's get back to the canvas. We've seen how you represent 3D scenes in 2D in theory, but can a canvas's `2d` context do it in practice?

There is no reason why it couldn't. We can implement the workflow described above for any object to get a list of 2d polygons, with colours for each, and then draw them with `drawTo` and `fill` commands.

However, it is not easy, and I am not talking about the human difficulty of writing the code - I'm talking about how easy it is for the computer to execute. There are two main problems:

1. The calculations which convert 3d vertices to 2d coordinates have to be done for *every* polygon, and for *every* corner of every polygon. We didn't really go into details but these are somewhat complex linear algebra calculations that need to be done one by one, on the CPU, potentially millions of times.
2. Calculating the colour of each polygon face is time consuming if you have to do it once, but remember what we really want is for the colour to change *within* a face to fully capture shade and lighting. This means calculating the colour of *every pixel* one by one, for every polygon. And this is before we get into the fact that the 2d context methods only let you fill entire shapes with a single colour - so we would have to do separate draw commands for every pixel.

You can represent any 3D scene using canvas's `2d` context, no matter how complex. You really, truly can. But it will take a long, long time. And that's just when you draw it once.

## Interactive 3D Scenes

So far, we have been tackling the question of how you draw a 3D scene once, and all of the calculations that go into this. As we have seen, this is difficult to do with the canvas tools we've been using so far.

But if you've ever used a 3D animation online, or played a video game, one thing may have struck you - how do you *interact* with the canvas. Once you've drawn your cube, or your sphere, or your video game character, what happens if you click the canvas and drag? Or mousewheel to zoom?

Well, by default, nothing. Remember we're just painting pixels, the canvas has no concept of a 'cube' object or anything else. If we want to make the canvas interactive, we have to (1) write event handlers which capture mouse actions, (2) use these mouse events to calculate how the vantage point should move, and then (3) *wipe the canvas clear and redraw everything from the new vantage point*. If we want smooth animations, we need to do this up to 60 times a second.

The canvas as we have been using it just can't do this. It cannot perform all the geometric, positional and shading calculations for every single polygons in 1/60 of a second. This is just not what Javascript is built to handle, and it is frankly not even what CPUs are built to handle.

We can do it, but we need a different canvas context that `2d`.

## WebGL

WebGL is an alternative context to canvases than `2d`. It uses different methods, and has different functionalities.

However, and this is crucial to stress: **webGL is still fundamentally a 2D context**. There is no `drawSphere` method in webGL, you still just draw 2D polygons. In fact in some ways it is less capable than the `2d` context because while `2d` can draw all kinds of shapes, webgl can only do three things - drawing points at specific locations, linking two locations with a line, or drawing a triangle between three points.

However, it has some features which entirely solve the problems we encountered earlier:

1. It lets you move the complex calculations of working out the 2D coordinates of 3D coordinates to the GPU, not the CPU. The GPU lets you do these calculations in parallel, and architecturally is designed for doing precisely the kinds of linear algebra calculations that are involved in this.
2. It also lets you do the pixel colour calculations on the GPU, in parallel - and crucially it supports interopolation from the colours at the triangle corners.

Everything else is the same, in terms of the workflow. You still have to convert your 3D object to a mesh of polygons, you still have to convert all the 3D coordinates to 2D after factoring in the vantage point, you still have to manually calculate colours based on lighting - webGL doesn't do any of this for you. What it does it provide a way for you to do these calculation and draw the polygons in a vastly more efficient way.

*How* you do this is beyond the scope here. You use a mixture of Javascript and a compiled language called GSLS, and there are many excellent tutorials for how to write webGL code. The purpise here is to understand they why, not the how.

## Abstractions Over WebGL

Finally, I say webGL doesn't do any of these manual calculations for you, and we still need to implement the workflow outlined above, but I only mean that the browser webGL API itself doesn't provide a way to do it for you. That doesn't mean that in practice, developers working on 3D scenes are writing code to do the mathematics of polygon rotation in all their projects.

There are many libaries which act as a layer of abstraction over webGL, and which do provide helper methods that are the equivalent of `drawSphere`:

- three.js is the most popular and widely used library. It handles all the low-level webgl code for you, and lets you work with actual 3d objects directlt.
- babylon.js is a similar library developed by Microsoft, commonly used in creating video games.
- A-Frame is a layer of abstraction above three.js, with a declaritive syntax.

Molstar uses webGL, but it doesn't use any of these libraries. It implements its own layer of abstraction over webGL (albeit one heavily inspired by, and in some places copied with attribution from, three.js). This custom implementation allows molstar to optimize specifically for molecular visualization.

