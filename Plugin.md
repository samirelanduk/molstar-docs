# Plugin

## What is a plugin?

A plugin is a Javascript object which acts as the central state object for a single molstar canvas. In general, you interact with the molstar by creating and initialising a plugin, and then using its attributes and methods to change what appears on screen. Each canvas has one plugin object attached to it, acting as the interface between the developer and what appears on the canvas.

It is so called because it 'plugs in' to an existing interface or application, rather than being a self-contained UI by itself.

## Plugin Specification

Plugins are highly customisable. Rather than doing this customisation with lots of instantiation parameters, you instead provide a single object - the plugin 'spec' - whose attributes are determined by the `PluginSpec` interface.

This spec object has seven attributes. We will not go into depth on any of them here, so only a cursory understanding of what each of them hooks into is needed at this stage:

- `behaviors` - the only required attribute. It takes a list of `Behavior` objects, which govern how the canvas responds to user interactions.
- `actions` - a list of 'actions', which are callables that update the plugin's state.
- `animations` - 
- `customFormats` - 
- `canvas3d` - initialisation parameters for setting up the canvas in the first place.
- `layout` - 
- `config` - 

The simplest plugin spec is therefore `{behaviors: []}`. molstar also provides a suggested default spec, with useful behaviors etc., which you can get with the `DefaultPluginSpec` class:

```javascript
import { DefaultPluginSpec } from "molstar/lib/mol-plugin/spec";

const basicSpec = {behaviors: []};

const defaultSpec = DefaultPluginSpec();

const customisedSpec = {
  ...DefaultPluginSpec(),
  actions: [
    // Set your own actions
  ]
};
```



## Creating a Plugin

## Initialising a Plugin