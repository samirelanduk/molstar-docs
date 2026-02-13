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

You create a plugin by just creating a `PluginContext` instance, with the spec object:

```javascript
import { PluginContext } from "molstar/lib/mol-plugin/context";

const basicSpec = {behaviors: []};
const plugin = PluginContext(basicSpec);
```

At this point, the plugin is just a Javascript object with lots of attributes, and with the spec added to the `plugin.spec` attribute. But

## Initialising a Plugin

State:

- this.subs - all the subscriptions the plugin maintains
- this.ev - the subject creation factory
- this.events
  - this.log - a `Subject` that can have things pushed to it and be subscribed to
  - this.task
  - this.canvas3d
- this.log
  - entries - a list of `LogEntry` objects
  - various methods which send values to this.events.log
- this.behaviors - various `BehaviorState` objects that other things can subscribe to
- this.dataFormats - a `DataFormatsRegistry` object that stores data formats.





On init call:

1. Logging setup
   1. 'Whenever this.events.log has a log entry pushed to it, add it to this.log.entries too'

2. initCustomFormats
3. initBehaviorEvents
4. initBuiltInBehavior
5. Set this.managers.interactivity
6. Set this.managers.lociLabels
7. Set this.builders.structure
8. initAnimations
9. initDataActions
10. initBehaviors
11. Issue log messages
12. Set _isInitialized to true
13. this.initializedPromiseCallbacks[0]









Plugin attributes:

`subs` - a list of rxjs `Subscriber` objects

`events`