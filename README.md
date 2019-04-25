# Nine43 [![Build Status](https://travis-ci.com/math2001/nine43.svg?branch=master)](https://travis-ci.com/math2001/nine43)

> The successor of Nine42

This project is supposed to teach me concurrency. It's the start of game
server with a client, all in Python.

## The server

The server is organized in sections that are completely independent. The only
way they talk with one an other is through channels. This makes the server
much easier to test because all those sections are pure functions (in the
sense that they have no side effect, and aren't be affected by any).

Firstly, we have the network section, the interface between the network and the 
application. It accepts raw `trio.SocketStream`s, wraps them in `net.JSONStream`
and sends them, through a channel called `connch` to the initiator. 

The initiator has one task: find out the username of the connection (and make
sure that there aren't any duplicates in the application). Once it has done
that, it can wrap the connection in a `Player` (which is just a connection and
a username). It then sends it off to a channel called `playerch`.

And the `lobby` is listening to that channel. The lobby's role is very
simplistic: to stack up players in groups of N, and sends the `Group` on an
other channel: `groupch`. 

Notice of up to now, all those section are exclusive on the application: there
is only one `server` running, one`initiator` and one `lobby`.

But now that we have a group of players, we can ask them what they want to do,
and then, depending on, it will start a chain of events: a sub. A sub is just
a select section, a game section, and an end section.

The server needs to be able to run multiple subs at the same time, but none of 
those subs need to know about each other. So we have a sub manager which spawns
subs as it receives groups.

In this case, there are 3 subs running:

![visualization of process explained above][server-flowchart]

> Made using [stackedit.io][] and [mermaid][]

There are a few key parts I've omitted on this graph because it makes look
unnecessarily complex.

1. Every section is connected to the `initiator` through a channel called
`quitch`. As soon as a connection is closed, we assumed that the layer below
tried it's best to recover the connection, and throw it away. But the username
needs to be released. This is the role of the `quitch`: every section can send
a player on it, and the `initiator` will release the username. `initiator` is
the sole consumer of this channel, every other section receives a clone of the
sending end of the channel.
2. As player leave a sub (leave the fin section), they get sent back to the
lobby through a clone of the `playerch`. This is managed by the sub manager
(the server doesn't anything about what's going on inside a `sub`).

> Every section is in fact just a proxy, which reads from a channel, and writes
> on another.

This means the sections are easy to test independently, and we'll know that
they'll behave likewise in the app, because those channels are the only way they
have to communicate.

> Only the sender should close the connection.

Another important part of the server is cascading: as soon a section detects
that its input channel has been closed, it cleans itself up, and closes its
output channel, creating a cascading effect, closing everything.

You might notice that since subs don't read from a channel (only the sub manager
does, it then spawns one sub per group), it won't know when to stop.

And this is an interesting behavior that could be desired: don't accept anymore
connections (close everything up to the sub manager), but finish the game you're
running.

If we really want to close everything forcefully, it'd be quite easy to pass a
`trio.Event` to every sub that will be triggered when it needs to be forcefully
closed.

> Note that this organization only works because when something is written on a
> channel, it is given up by the sender. For example, this wouldn't be allowed:

```python
async def section1(ch: SendCh[Obj]):
	obj = make_new_obj(arg='value')
	await ch.send(obj)
	obj.alter() # no!! You don't own obj anymore!
```

It prevents us from thinking of every section as independent, and we have to 
consider the whole application as a whole.

## Client

TODO


[stackedit.io]: https://stackedit.io
[mermaid]: https://mermaidjs.github.io
[server-flowchart]: imgs/server-flowchart.png