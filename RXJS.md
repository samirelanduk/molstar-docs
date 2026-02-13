# RXJS

Molstar uses RxJS extensively to manage state in a reactive way. Understanding it, and the observable pattern it implements, is important in understanding the inner workings of molstar.

## Push and Pull

A function lets you encode some repeatable logic which, once executed, 'returns' a value to whatever called it. It returns one value - it may be an array of values but it is still one 'return'. And, crucially, the caller decided when execution happens.

We may want to modify these two limitations. For example, we may want a function which can return multiple values - we call the function, and it runs it until the first return and stays frozen in that state, then we run it again and it resumes from that frozen state until it returns a second value, and so on. These are iterators.

Or, we may want a function that 'pushes' rather than 'pulls'. Rather than us calling a function and waiting for it to finish before returning a value, we run the function asynchronously and let it produce a value when it's ready, with callback logic for when this happens. This is essentially what a promise is.

Iterators and callbacks the, solve two of the limitations of functions. Iterators let a function return multiple values, and promises let functions return values by pushing rather waiting to be pulled. But note that they each only solve one of the two problems. Iterators still need to be 'pulled' - you are responsible for invoking the next execution. And promises only return one value.

Vanilla Javascript is missing the fourth corner of this matrix - a kind of function which which returns multiple values, and which pushes rather than pulls. rxjs provides this type of object - it is called an observable.

## Observable

An observable is a wrapper object around a function. Its observable's contract with the world is:

> I am an object which knows how to perform a long running process that occasionally produces values. If you would like me to do this for you, then call my `subscribe` method with instructions for what to do with those values, and I will start one of those long running processes for you. I will also give you a means of stopping that long running process at a time of your choosing.

```javascript
const doSomethingThatReturnsMultipleValuesOverTime = () => {
  // 
}

const myObservable = new Observable(doSomethingThatReturnsMultipleValuesOverTime)
```

How do you actually invoke this function? How do you 'set it running'? You call the observable's `subscribe` method. You can call `subscribe` multiple times and each time it will start the function running.

The function is called synchronously - so `subscribe` only returns a value when it has completed. However the function may make any number of asynchronous calls, and these will continue running even once the synchronous body of the function has completed.

Note, we say `subscribe` returns 'a' value. `subscribe` is not returning the outputs of our function, those are 'returned' in another way that we will come to shortly. `subscribe` simple returns an object that lets you control the link to the function.

## Observers

We said that when you call `subscribe`, you have to provide instructions about what to do with the values as they are produced. You do this by passing an object called an observer.

An oberver isn't an instance of a class, you just create it yourself. It must have a `next` method, and optionally a `complete` and `error` method which dictate what you want to happen if there's an error or if the observable's long running process decides it is complete.

How these get called is entirely up to the observable's long-running process function. This function takes an observer as input, and in addition to doing whatever it does to generate values, it is also responsible for calling `next` etc on this object.

Note that `subscribe` as a convenience can also just take a raw function as input - in this case the `subscribe` method will make an observer object with that as the `next` method.

## Subscription

We also said that when you call `subscribe`, you get back some representation of the subscription which lets you manage it. This is a `Subscription` object.

The most useful thing a subscription does, is the `unsubscribe` method, which terminates whatever action the observable's function is doing. Note that the function has already exited at this point - the synchronous body of the function completes before the `subscribe` method ends. But there may be various asynchronous things still running, and `unsubscribe` causes those to end too.

Note that it is up to you as the author of the observable to determine how this is done. Every observable function should return (with a `return` statement, not the `next` calls) a function which does any of this cleanup operation, and this is what `unsubscribe` calls.

You can also combine subscriptions with the `add` method such that unsubscribing one unsubscribes them all.

## Subject

A subject is similar to an observable, with a few crucial differences.

Firstly, it does not take any kind of function as its input. Whereas regular observables generate values by running this one long running function, subjects do not.

Secondly, they are also observers - of themselves. That is, they have `next`, `error` and `complete` methods, which cause those values to be 'sent' to whatever is subscribed to them.

Thirdly, all subscribers get the same outputs. As there is no function, it is not the case that each subscriber triggers its own process - it is simply the case that any time the `next` method is called, all subscribers get that one value.

What all this means in practice is that subjects are useful for 'mult-casting' - sending a value once to multiple receivers.

## BehaviorSubject

A BehaviorSubject differs from a Subject in one respect - whereas with subjects when you subscribe, you receive nothing until the next `next` call, with BehaviorSubjects, as soon as you subscribe you get whatever the most recent value was, and then all subsequent ones as normal. As a result, you have to give it an initial value when you create it.

This gives BehaviorSubjects a kind of state that regular subjects don't have - at any given time they hold a value. You can create a highly reactive object by having all the attributes be BehaviorSubjects rather than regular variables, which are updated with `next` calls rather than by just assigning values, and where whenever that state changes all listeners react accordingly straight away.

## Creation Operators

An 'operator' is a function which produces an observable. The most conceptually simple is the creation operator, which can take any input and produce an observable.

The simplest is `of()`, which takes some sequence of values and creates an obserable that returns them - `of(1, 2, 3)` for example.

A more useful creation operator would be `fromEvent`. This takes a DOM element, an event name, and returns an observable which acts as an event listener, producing values each time the DOM event takes place.

There are other examples.

## Pipeable Operators

A pipeable operator takes one observable as input, and produces a second observable that acts on the values of the first operator.

For example, `map` will produce such an operator - it takes some function, and then outputs an operator that will take the output of one observable, and produce a new observable whose function produces some transformation of the original. Note that `map` is not the operator, it is an operator factory - the operator is whatever it produces.

You could use `map` like this:

```javascript
const observable1 = of(1, 2, 3)
const mapOperator = map(x => x * 10)
const observable2 = mapOperator(observable1)
```

But a more convenient way of achieving the same is the observable's `pipe` method:

```javascript
const observable1 = of(1, 2, 3)
const observable2 = observable1.pipe(map(x => x * 10))
```

## Debouncing

Debouncing is a useful example of chaining these observables together with operators. Debouncing converts a rapid stream of values into occasional emissions by only emitting a value once a specified period of inactivity has passed since the last value arrived.

For example, suppose you have a text box which, when the user types in it, should query some API with whatever the current value is, and you want it to do so on each new character...

```javascript
const sendQuery = text => {
  // Logic for sending HTTP request to API with text to search goes here
}

const inputElement = document.querySelector("input")
const onTypeObservable = fromEvent(inputElement, "input")
onTypeObservable.subscribe(event => {
  const text = event.target.value;
  sendQuery(text);
})
```

Firstly, the observable created by `fromEvent` outputs event objects, and we just want the text, so we can create a new observable to just output the text:

```javascript
const sendQuery = text => {
  // Logic for sending HTTP request to API with text to search goes here
}

const inputElement = document.querySelector("input")
const onTypeObservable = fromEvent(inputElement, "input").pipe(map(e => e.target.value))
onTypeObservable.subscribe(sendQuery)
```

But this is sending a HTTP request on every single character press. For rapid typers, this can overload the backend, and in many cases by the time a request has come back it isn't even needed as three more have been sent in the meantime.

What we want is an observable which emits text values at a slower pace. The logic would be:

1. Receive a piece of text from the upstream observable.
2. Wait *n* seconds (1, 5, 0.5, whatever).
3. If after that period, no *new* pieces of text come in, emit the text.
4. If during that period, a new piece of text comes in, cancel the countdown and start a new one for the text that just came in.

This will emit text values at a much more manageable pace. The code for such an operator is trivial, but one is provided by rxjs:

```javascript
const sendQuery = text => {
  // Logic for sending HTTP request to API with text to search goes here
}

const inputElement = document.querySelector("input")
const onTypeObservable = fromEvent(inputElement, "input").pipe(map(e => e.target.value))
const debouncedObservable = onTypeObservable.pipe(debounceTime(1000))
debouncedObservable.subscribe(sendQuery)
```

## rxjs in Molstar

Molstar uses rxjs for many of the attributes of its objects. Instead of just using regaulr attributes, it uses `BehaviorSubject` objects in many places to hold the state - allowing other parts of the application to subscribe to changes and react accordingly.

molstar also introduces an additional concept - the `RxEventHelper`. An `RxEventHelper` object has methods for creating `Subject` and `BehaviorSubject` objects, and maintaining a list of all the ones it has created - so that they can all be disposed of together.

For example, many objects on molstar have this top-level `ev` object used to create attributes:

```javascript
ev = RxEventHelper.create();

attribute1 = this.ev.create();
attribute2 = this.ev.behavior("initial-value");
```

These attributes all act just like any other `Subject` or  `BehaviorSubject` - they store values, the values can be updated with `next` calls, and other things can subscribe to them to get the current value. The only difference is that you can call `ev.dispose()` and all of the subjects' and behavior subjects' `complete` methods are called at once.
