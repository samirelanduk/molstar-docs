# Canvas

## The Canvas Element

A canvas is a HTML element, `<canvas>`, embedded in the HTML like any other element. What's special about the canvas, is that you can draw on it with Javascript.

Most elements have their appearance determined solely by CSS. Their interior might be a single colour, or perhaps a gradient of some kind. It might have a border with some sort of pattern. But ultimately, unless it's an image, it's really all just decoration and positioning for text. With a canvas however, you can draw shapes, arcs, lines - anything you like. They are essentially programatically created images that can change based on user interactions.

For this reason, canvases often underpin many of the complex, dynamic, interactive interfaces we see on the web. Zoomable maps, games, document rendering - and of course, manipulatable 3D scenes such as molstar - all make use of the canvas to do this.

## Canvas Coordinates

Before we get into how you draw things to a canvas, we need to understand its coordinate system.

Canvas elements have `width` and `height` attributes - if you don't supply these they default to 300px and 150px respectively. These attributes determine two things:

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

## 3D Objects from 2D Shapes

## Interactive 3D Scenes

## The Limitations of Canvas2D

## WebGL

## Abstractions Over WebGL

